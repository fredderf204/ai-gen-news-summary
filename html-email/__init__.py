import datetime
import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from datetime import datetime
import json
import os
import requests

import azure.functions as func

def main(mytimer: func.TimerRequest) -> None:
    sas = os.environ["saskey"]
    container_url = os.environ["containerurl"]
    storageaccount = os.environ["storageaccount"]
    
    blob_service_client = BlobServiceClient.from_connection_string(storageaccount)

    today = datetime.today().strftime('%Y%m%d')
    container_client = blob_service_client.get_container_client(today)

    html = "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"UTF-8\">\n<meta name=\"viewport\" content=\"width=device-width\">\n<style>\nh1 {\nmax-width: 500px;\nmargin: 0 auto;\ntext-align: center;\nfont-family: 'Courier New', Courier, monospace;\n}\nh2 {\npadding-top: 10px;\npadding-left: 100px;\nmargin: 0 auto;\ntext-align: left;\nfont-family: 'Courier New', Courier, monospace;\n}\nh3 {\npadding-top: 10px;\npadding-left: 100px;\nmargin: 0 auto;\ntext-align: left;\nfont-family: serif;\n}\npre {\npadding-top: 10px;\npadding-left: 100px;\nwhite-space: pre-wrap;\nmargin: 0 auto;\ntext-align: left;\nfont-family: 'Courier New', Courier, monospace;\n}\n</style>\n</head>\n<body>\n<h1>Azure News Summary for " + today + "</h1>\n"

    bloblist = container_client.list_blobs()

    for blob in bloblist:
        print(blob.name)
        blob_client = container_client.get_blob_client(blob.name)
        downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8')
        blob_text = downloader.readall()
        blob_text_json = json.loads(blob_text)
        html += "<h2>" + blob_text_json.get('title') + "</h2>\n<h3>" + blob_text_json.get('author') + " <a href=\"" + blob_text_json.get('link') + "\">" + blob_text_json.get('link') + "</a></h3>\n<pre>" + blob_text_json.get('summary') + "</pre>\n<hr>\n"

    html += "</body>\n</html>"

    container_client.upload_blob(name=today + ".html", data=html, overwrite=True)

    data = {"html": container_url+'/'+today+'/'+today+'.html'+sas}

    url = os.environ["logicappurl"]
    headers = {"Content-Type": "application/json"}
    data = json.dumps(data)

    response = requests.post(url, headers=headers, data=data)

    logging.info(response.status_code)