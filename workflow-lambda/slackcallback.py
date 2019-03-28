import boto3
import os
import time
import hashlib
import hmac
import json

try:
    from urllib.parse import parse_qs
except ImportError:
    from urllib import parse_qs

SLACK_TOPIC_ARN = os.environ['SLACK_TOPIC_ARN']
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']

''' Verify the POST request. '''
def verify_slack_request(slack_signature=None, slack_request_timestamp=None, request_body=None):
    ''' Form the basestring as stated in the Slack API docs. We need to make a bytestring. '''
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode('utf-8')

    ''' Make the Signing Secret a bytestring too. '''
    slack_signing_secret = bytes(SLACK_SIGNING_SECRET, 'utf-8')

    ''' Create a new HMAC "signature", and return the string presentation. '''
    my_signature = 'v0=' + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()

    ''' Compare the the Slack provided signature to ours.
    If they are equal, the request should be verified successfully.
    Log the unsuccessful requests for further analysis
    (along with another relevant info about the request). '''
    if hmac.compare_digest(my_signature, slack_signature):
        return True
    else:
        logger.warning(f"Verification failed. my_signature: {my_signature}")
        return False

def lambda_handler(event, context):
    try:
        # slack_signature = event['headers']['X-Slack-Signature']
        # slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']
        #
        # if not verify_slack_request(slack_signature, slack_request_timestamp, event['body']):
        #     logger.info('Bad request.')
        #     response = {
        #         "statusCode": 400,
        #         "body": ''
        #     }
        #     return response

        # Gget the "payload" as a query string
        body = json.loads(parse_qs(event['body'])['payload'][0])
        print('got body', json.dumps(body))

        # Parse the event to get the selected option
        rekognition_id = body['callback_id']
        action_value = body['actions'][0]['value']
        slack_user_id = body['user']['id']
        print('rekog id: {}, action: {}, user: {}'.format(rekognition_id, action_value, slack_user_id))

        # Publish SNS with the rekognition and action
        msg = {
            "SlackResponse":{
                "RekognitionId": rekognition_id,
                "HostResponse": action_value
            }
        }
        client = boto3.client('sns')
        response = client.publish(
            TargetArn=SLACK_TOPIC_ARN,
            Message=json.dumps({'default': json.dumps(msg)}),
            MessageStructure='json'
        )
        print('publish', SLACK_TOPIC_ARN, json.dumps(msg))

        # Get the original message, update attactments to have text instead of actions
        original_message = body['original_message']
        action_text = [a['text'] for a in original_message['attachments'][0]['actions'] if a['value'] == action_value]
        original_message['attachments'][0]['color'] = "#36a64f"
        original_message['attachments'][0]['text'] = ":white_check_mark: <@{}> says {}".format(slack_user_id, action_text[0])
        # Delete any actions of fields
        if 'actions' in  original_message['attachments'][0]:
            del original_message['attachments'][0]['actions']
        if 'fields' in  original_message['attachments'][0]:
            del original_message['attachments'][0]['fields']

        # Return the update response
        response = json.dumps(original_message)
        print('response', response)
        return {
            "statusCode": 200,
            "body": response
        }

    except Exception as e:
        print('error', e)
        response = {
            "statusCode": 400,
            "body": 'Error adjusting state'
        }
