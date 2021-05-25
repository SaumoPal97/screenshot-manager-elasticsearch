## Inspiration
Everyone needs to handle massive amounts of information, which often is taken as a screenshot and kept for future use. However, managing them and extracting or searching them based on their information is a very hard task. 

## What it does
Hence I have used OCR and ML APIs to extract information from text and tags for images and stored them in ElasticSearch which is then utilized to build s searchable database for screenshots.

## How I built it
I built the web app on the Flask framework using Algorithmic's OCR APIs and Sentient's NLP and object detection APIs. After that, I used Elasticsearch as a backend for storing and querying the data and used APM to monitor the web app.

## Challenges I ran into
There wasn't any significant challenge as such apart from finding an interesting idea where search can make wonders happen. Kudos to elasticsearch for being so widely used that there isn't an idea not already solved by elasticsearch :P 

##Accomplishments I am proud of
Getting an important and painful idea to work upon and building it within 7 hours :P

## What I learned
I learned how seamlessly elasticsearch can fit into our developer toolkit, adding the quintessential search bar into any facet or product we build in the future.

## What's next
More ML APIs can help rectify some grammatical errors made by the OCR algorithms, and we can see how to add more metadata to enhance searchability of screenshots
