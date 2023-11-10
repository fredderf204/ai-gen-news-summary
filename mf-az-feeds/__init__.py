import datetime
import os
import logging
import feedparser
from datetime import datetime, timedelta
import json
import requests
from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage, BinaryBase64EncodePolicy

import azure.functions as func

def main(mytimer: func.TimerRequest) -> None:

    logging.info('Python timer trigger function')

    today = datetime.today()
    if today.weekday() == 6:
        yesterday = today - timedelta(days=2)
    else:
        yesterday = today - timedelta(days=1)
    date_format = "%a, %d %b %Y %H:%M:%S %z"

    feed_array = []

    storageaccount = os.environ["storageaccount"]
    queue_name = os.environ["queuename"]
    queue_client = QueueClient.from_connection_string(storageaccount, queue_name,
                                                      message_encode_policy = BinaryBase64EncodePolicy())

    d = feedparser.parse(os.environ["targetrss"])
    for x in d.entries:
        input_date = datetime.strptime(x.published, date_format)
        input_date = input_date.replace(tzinfo=None)
        if input_date > yesterday:
            feed_array.append({"published":str(input_date), "author":x.author, "title":x.title, "link":x.link})
 
    feed_string = json.dumps(feed_array)

    for y in feed_array:
        queue_client.send_message(json.dumps(y).encode('utf-8'))
        logging.info('message sent to queue')