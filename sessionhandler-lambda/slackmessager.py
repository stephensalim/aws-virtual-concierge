
from __future__ import print_function

import boto3
import json
import logging
import os
import base64

from urllib2 import Request, urlopen, URLError, HTTPError

#configuration
HOOK_URL = os.environ['SlackWebHook']
SLACK_CHANNEL = os.environ['SlackChannel']

# Setting up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    if 'Face' not in event:
        return event

    # TODO: Test these parameters
    host = "!everyone"
    color = "#2eb886"
    visitorId = event['Face']['VisitorId']
    photo = event['Face']['Url']
    name = event['Face']['Name']

    # Render the slack message
    slack_message =  {
        "channel": SLACK_CHANNEL,
        "text": "Hey <{}> You have a Guest! Please come out and greet.".format(host),
        "attachments": [{
            "color": color,
            "thumb_url": photo,
            "callback_id": visitorId,
            "fields": [{
                "title": "Name",
                "value": name,
                "short": True
            }],
            "actions": [{
                "type": "button",
                "text": "Coming out now",
                "name": "state",
                "value": "comingout",
                "style": "primary"
            }, {
                "type": "button",
                "text": "Couple of mins",
                "name": "state",
                "value": "comingoutsoon",
                "style": "danger"
            }]
        }]
    }

    #slack_message = json.dumps(message)
    logger.info(str(slack_message))

    req = Request(HOOK_URL, json.dumps(slack_message))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)

    return(event)
