import logging
from datetime import datetime
import requests
from readability import Document
import re
import tiktoken
from openai import AzureOpenAI
import json
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import uuid
import os

import azure.functions as func

def main(msg: func.QueueMessage) -> None:
    feed_msg = json.loads(msg.get_body().decode('utf-8'))
    
    # Get article from blogging site
    response = requests.get(feed_msg['link'])
    doc = Document(response.content)
    tosumm = doc.summary()  

    # Clean text and remove html tags
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

    def cleanhtml(raw_html):
        cleantext = re.sub(CLEANR, '', raw_html)
        return cleantext

    cleansumm = cleanhtml(tosumm)

    #count number of tokens before sending to AOAI
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    cleansummtok = (num_tokens_from_string(cleansumm, "cl100k_base"))

    ## Summaries text from AOAI
    client = AzureOpenAI(
        azure_endpoint = os.environ["aoaiendpoint"],
        api_version = "2023-07-01-preview",
        api_key = os.environ["aoaikey"],
    )

    response = client.chat.completions.create(
    model=os.environ["aoaimodel"],
    messages = [{"role":"system","content":"Using extractive summarization, condense this news article into key bullet points."},{"role":"user","content":cleansumm}]
    )

    # Save as json to blob storage
    #logging(response)
    #logging.info(response.choices[0].message.content)
    feed_msg["summary"] = response.choices[0].message.content

    # Create the BlobServiceClient object
    storageaccount = os.environ["storageaccount"]
    blob_service_client = BlobServiceClient.from_connection_string(storageaccount)

    # Create a unique name for the container with todays date and create the container
    today = datetime.today().strftime('%Y%m%d')
    container = ContainerClient.from_connection_string(storageaccount, today)

    if container.exists():
        # Container foo exists. You can now use it.
        print("Container exists")

    else:
        # Container foo does not exist. You can now create it.
         container_client = blob_service_client.create_container(today)

    # Save feed_msg to blob storage
    uid = uuid.uuid4().hex[:6]
    file_name = uid + '.json'
    blob_client = blob_service_client.get_blob_client(container=today, blob=file_name)

    # Upload the created file
    blob_client.upload_blob(json.dumps(feed_msg))
    logging.info('message saved to blob storage')