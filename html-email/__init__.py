import datetime
import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from datetime import datetime
import json
import os
import requests

import azure.functions as func

def main(mytimer: func.TimerRequest) -> None:
    #sas = os.environ["saskey"]
    static_url = os.environ["staticurl"]
    storageaccount = os.environ["storageaccount"]
    
    blob_service_client = BlobServiceClient.from_connection_string(storageaccount)

    today = datetime.today().strftime('%Y%m%d')
    container_client = blob_service_client.get_container_client(today)
    container_client1 = blob_service_client.get_container_client('$web')

    html = "<!DOCTYPE html><html lang=en><title>AI Generated Azure News</title><meta charset=UTF-8><meta content=\"width=device-width,initial-scale=1\"name=viewport><link href=https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css rel=stylesheet crossorigin=anonymous integrity=sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM><link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css\"><style>h1{font-size:2.5rem}h2{font-size:2.25rem}h3{font-size:2rem}h4{font-size:1.75rem}h5{font-size:1.5rem}h6{font-size:1.25rem}p{font-size:1rem}pre{white-space:pre-wrap}@media (max-width:480px){html{font-size:12px}}@media (min-width:480px){html{font-size:13px}}@media (min-width:768px){html{font-size:14px}}@media (min-width:992px){html{font-size:15px}}@media (min-width:1200px){html{font-size:16px}}</style><div class=container-fluid style=text-align:center><h1>Azure News Summary for " + today + "</h1><p><i>* Generated with Azure Open AI, gpt-35-turbo and system message - Using extractive summarization, condense this news article into key bullet points.</i></p><p><i class=\"ti ti-brand-github\"></i><a href=\"https://github.com/fredderf204/ai-gen-news-summary\">https://github.com/fredderf204/ai-gen-news-summary</a></p><hr></div>"

    bloblist = container_client.list_blobs()

    for blob in bloblist:
        print(blob.name)
        blob_client = container_client.get_blob_client(blob.name)
        downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8')
        blob_text = downloader.readall()
        blob_text_json = json.loads(blob_text)
        html += "<div class=\"container\"><h4>" + blob_text_json.get('title') + "</h4></div><div class=\"container\"><p>" + blob_text_json.get('author') + " <a href=\"" + blob_text_json.get('link') + "\">" + blob_text_json.get('link') + "</a></p></div><div class=\"container\" style=\"word-wrap: break-word;\"><pre>" + blob_text_json.get('summary') + "</pre>\n<hr>\n</div>\n"

    html += "<script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js\" integrity=\"sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4\" crossorigin=\"anonymous\"></script></div></body>\n</html>"

    container_client.upload_blob(name=today + ".html", data=html, overwrite=True)

    container_client1.upload_blob(name="index.html", data=html, overwrite=True)
    shblob_service_client = blob_service_client.get_blob_client(container='$web', blob='index.html')
    properties = shblob_service_client.get_blob_properties()
    blob_headers = ContentSettings(content_type="text/html",
                                   content_encoding=properties.content_settings.content_encoding,
                                   content_language="en-US",
                                   content_disposition=properties.content_settings.content_disposition,
                                   cache_control=properties.content_settings.cache_control,
                                   content_md5=properties.content_settings.content_md5)
    shblob_service_client.set_http_headers(blob_headers)

    data = {"html": static_url}

    url = os.environ["logicappurl"]
    headers = {"Content-Type": "application/json"}
    data = json.dumps(data)

    response = requests.post(url, headers=headers, data=data)

    logging.info(response.status_code)