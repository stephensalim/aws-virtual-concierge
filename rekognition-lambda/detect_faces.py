from __future__ import print_function

import boto3
from urllib.parse import unquote_plus 
import time
import datetime
import json
import os

print('Loading function')

cloudwatch = boto3.client('cloudwatch')
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
sns = boto3.client('sns')

FACE_COLLECTON = os.environ["FACE_COLLECTON"]
FACE_DDB_TABLE = os.environ["FACE_DDB_TABLE"]
FACE_THRESHOLD = int(os.getenv("FACE_THRESHOLD", 75))
FACE_URL_TTL = int(os.getenv("FACE_URL_TTL", 3600))
FACE_TOPIC_ARN = os.environ["FACE_TOPIC_ARN"]
FACE_ROTATE = os.getenv("FACE_ROTATE", "ROTATE_0")

def push_to_cloudwatch(name, value, unit='Percent', timestamp=time.time()):
    try:
        metric_timestamp = datetime.datetime.fromtimestamp(timestamp)
        cloudwatch.put_metric_data(
            Namespace='string',
            MetricData=[
                {
                    'MetricName': name,
                    'Timestamp': metric_timestamp,
                    'Value': value,
                    'Unit': unit
                },
            ]
        )
        print('Log metric: {}={} {} @ {}'.format(name, value, unit, timestamp))
    except Exception as ex:
        print("Unable to push to cloudwatch e: {}".format(ex))
        return True

def get_signed_url(bucket, key, ttl=FACE_URL_TTL):
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key
        },
        ExpiresIn=ttl,
    )

def get_face(face_id, table_name=FACE_DDB_TABLE):
    start_ddb = time.time()
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'FaceId': face_id})
    if 'Item' in response:
        print('Dynamodb lookup for {} latency: {}'.format(face_id, time.time()-start_ddb))
        return response['Item']

def detect_first_face(bucket, key, collection_id=FACE_COLLECTON, threshold=FACE_THRESHOLD, rotation=FACE_ROTATE):
    # Get timestamp from the begining of the last part of the key eg 'faces/yyymmdd/ts_index.jpg'
    timestamp = int(key.split('/')[-1].split('_')[0])
    start_inference=time.time()
    response = rekognition.search_faces_by_image(
        Image={
            "S3Object": {
            "Bucket": bucket,
            "Name": key,
            }
        },
        CollectionId=collection_id,
        FaceMatchThreshold=threshold,
        MaxFaces=1,
    )
    print('Rekognition for {}/{} latency: {}'.format(bucket, key, time.time()-start_inference))
    for match in response['FaceMatches']:
        face = get_face(match['Face']['FaceId'])
        if face:
            push_to_cloudwatch('Face Confidence', round(match['Face']['Confidence'], 2), 'Percent', timestamp)
            return {
                'Frame': {
                    'Url': get_signed_url(bucket, key),
                },
                'Visitor': {
                    'FaceId': match['Face']['FaceId'],
                    'Name': face['FullName'],
                    'Url': get_signed_url(face['Bucket'], face['Key']),
                    'OrientationCorrection': face.get('OrientationCorrection') or rotation,
                }
            }

def publish_message(payload, topic_arn=FACE_TOPIC_ARN):
    subject = '{}-{}'.format(payload["ThingName"], int(time.time()))
    msg = json.dumps({"default": json.dumps({ "VirtualConcierge": payload }) })
    response = sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        MessageStructure='json',
        Message=msg,
    )
    return response['MessageId']

def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        payload = detect_first_face(bucket, key)
        if payload:
            ret = s3.head_object(Bucket=bucket,Key=key)
            payload['ThingName'] = ret['Metadata']['thingname']
            message_id = publish_message(payload)
            print('Publish sns: {} with payload: {}'.format(message_id, json.dumps(payload)))
        return payload
    except Exception as ex:
        print("Error processing object {} from bucket {}: {}".format(key, bucket, ex))
        raise ex
