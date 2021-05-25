from flask import Flask, render_template, request
from werkzeug.utils import redirect, secure_filename
import os
from PIL import Image, ExifTags
import uuid
import Algorithmia
from werkzeug.wrappers import response
import base64
import requests
import json
import re
from elastic_app_search import Client
from datetime import datetime
import urllib
from elasticapm.contrib.flask import ElasticAPM
import logging

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, "static", "images")

app = Flask(__name__, static_url_path="/static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

apm = ElasticAPM(app,logging=logging.ERROR,
server_url=config['apm']['server_url'] ,
 service_name=config['apm']['service_name'], 
 secret_token=config['apm']['secret_token'])

client = Client(
    base_endpoint=config["appsearch"]["base_endpoint"],
    api_key=config["appsearch"]["api_key"],
    use_https=True,
)

engine_name = config["appsearch"]["engine_name"]


@app.route("/")
def home():
    data = client.search(engine_name, "", {})
    return render_template("home.html", data=data)


@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
        query = request.form["search"]
    data = client.search(engine_name, query, {})
    return render_template("home.html", data=data)


@app.route("/upload")
def upload_file():
    return render_template("upload.html")


@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if request.method == "POST":
        # try:
        uploadData = {}
        f = request.files["file"]
        filename = os.path.join(
            app.config["UPLOAD_FOLDER"], urllib.parse.quote_plus(f.filename)
        )
        f.save(filename)
        uploadData["id"] = str(uuid.uuid4())
        uploadData["filename"] = urllib.parse.quote_plus(f.filename)

        algo_client = Algorithmia.client(config["algorithmia_key"])
        tempdir = algo_client.dir("data://.my/temp/")
        if not tempdir.exists():
            dir.create()
        temp_datafile = "data://.my/temp/%s" % f.filename
        algo_client.file(temp_datafile).putFile(filename)
        algo = algo_client.algo("ocr/RecognizeCharacters/0.3.0")
        algo.set_options(timeout=300)
        response = algo.pipe(temp_datafile)
        text_description = response.result.strip().replace("\n", " ")
        try:
            uploadData["description"] = text_description
            url = "https://apis.sentient.io/microservices/nlp/namedentityrecognition/v1/getpredictions"
            payload = '{"text":"%s"}' % re.sub(
                r"[^\x00-\x7F]+", " ", response.result
            ).strip().replace("\n", " ")
            headers = {
                "content-type": "application/json",
                "x-api-key": config["sentient_key"],
            }

            response = requests.request("POST", url, data=payload, headers=headers)
            text_tags = []
            try:
                text_tags.append(json.loads(response.text)["results"]["loc"])
            except TypeError:
                pass

            try:
                text_tags.append(json.loads(response.text)["results"]["per"])
            except TypeError:
                pass

            try:
                text_tags.append(json.loads(response.text)["results"]["org"])
            except TypeError:
                pass

            print(text_tags)
            uploadData["tags"] = text_tags
        except:
            try:
                url = "https://apis.sentient.io/microservices/cv/objectdetection/v0.1/getpredictions"
                payload = '{"image_base64": "%s"}' % base64.b64encode(
                    open(filename, "rb").read()
                ).decode("utf-8")
                headers = {
                    "content-type": "application/json",
                    "x-api-key": config["sentient_key"],
                }
                response = requests.request("POST", url, data=payload, headers=headers)
                object_tags = []
                for key in json.loads(response.text).keys():
                    object_tags.append(
                        json.loads(response.text)[key][0].split(":")[0].strip()
                    )
                if "tags" in uploadData.keys():
                    uploadData["tags"].append(object_tags)
                else:
                    uploadData["tags"] = object_tags
                    uploadData["tags"].append("infographic")
                if len(object_tags) < 2:
                    uploadData["type"] = "TEXT"
                else:
                    uploadData["type"] = "IMAGE"
            except:
                pass

        im = Image.open(filename)
        if "png" in filename:
            im.load()
            uploadData["metadata"] = [im.info]
        else:
            try:
                exif = {
                    ExifTags.TAGS[k]: v
                    for k, v in im._getexif().items()
                    if k in ExifTags.TAGS
                }
                uploadData["metadata"] = [
                    json.dumps(exif, ensure_ascii=False).encode("utf-8")
                ]
            except:
                pass
        now = datetime.now()
        uploadData["date_time"] = now.strftime("%m/%d/%Y, %H:%M:%S")
        print(uploadData)
        data1 = client.index_documents(engine_name, documents=[uploadData])
        print(data1)
        # except:
        #     pass
        data = client.list_documents(engine_name)
        print(data)
        return redirect("/")


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
