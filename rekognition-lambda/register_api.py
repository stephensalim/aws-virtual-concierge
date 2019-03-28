from __future__ import print_function

from decimal import Decimal
import base64
import boto3
from boto3.dynamodb.conditions import Attr
import json
import os
from botocore.vendored import requests #
import time
import uuid

print('Loading function')

# Environment variables
FACE_COLLECTON = os.environ["FACE_COLLECTON"]
FACE_DDB_TABLE = os.environ["FACE_DDB_TABLE"]
FACE_TOPIC_ARN = os.environ["FACE_TOPIC_ARN"]
FACE_THRESHOLD = int(os.getenv("FACE_THRESHOLD", 75))
FACE_URL_TTL = int(os.getenv("FACE_URL_TTL", 3600))
FACE_ROTATE = os.environ["FACE_ROTATE"]
INDEX_BUCKET = os.environ["INDEX_BUCKET"]
INDEX_PATH = os.environ["INDEX_PATH"]
CLASSIFY_URL = os.environ["CLASSIFY_URL"]

def detect_face(request, max_faces=1, collection_id=FACE_COLLECTON, threshold=FACE_THRESHOLD, rotate=FACE_ROTATE):
    print('detecting face')
    rekognition = boto3.client('rekognition')
    detect = rekognition.detect_faces(
        Image=request["Image"],
        Attributes=['ALL'], # So we return the details
    )
    if len(detect['FaceDetails']) != 1:
        raise ValueError("Require single face")
    # Get back to see if we have an existing face
    response = rekognition.search_faces_by_image(
        Image=request["Image"],
        CollectionId=collection_id,
        FaceMatchThreshold=threshold,
        MaxFaces=1,
    )
    if len(response['FaceMatches']) > 0:
        face = response['FaceMatches'][0]['Face']
        status = 200
    else:
        # Index the new face and return the face record
        response = rekognition.index_faces(
            Image=request["Image"],
            ExternalImageId=request["ImageId"],
            CollectionId=collection_id
        )
        if len(response['FaceRecords']) == 0:
            raise ValueError("No faces indexed")
        face = response['FaceRecords'][0]['Face']
        status = 201
    # Return explicit parameters
    ret = {
        "Status": status,
        "Face": face,
        "OrientationCorrection": detect.get('OrientationCorrection', rotate),
        "FaceDetails": detect['FaceDetails'],
    }
    return ret

def upload_object(index_bucket, index_key, buf, content_type):
    print('uploading bytes to s3')
    s3 = boto3.resource('s3')
    s3.Bucket(index_bucket).put_object(Key=index_key,Body=buf,ContentType=content_type)

def invoke_classify(url, payload):
    # Calling classify endpoint (TODO: Consider to make this async)
    headers = { 'Content-Type': 'application/json' }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    return json.loads(response.text)

def dict_to_decimal(dict):
    for k in dict:
        dict[k] = Decimal(str(dict[k]))

def update_index(item, table_name=FACE_DDB_TABLE):
    print('updating dynamodb')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    return table.put_item(Item=item)

def publish_message(payload, topic_arn=FACE_TOPIC_ARN):
    sns = boto3.client('sns')
    subject = '{}-{}'.format(payload["ThingName"], int(time.time()))
    msg = json.dumps({"default": json.dumps({ "VirtualConcierge": payload }) })
    print('publising message', msg)
    response = sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        MessageStructure='json',
        Message=msg,
    )
    return response

def get_signed_url(bucket, key, ttl=FACE_URL_TTL):
    print('getting signed url for {}/{}'.format(bucket,key))
    s3 = boto3.client('s3')
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key
        },
        ExpiresIn=ttl,
    )

def scan_avaialable_hosts(table_name=FACE_DDB_TABLE):
    print('querying dynamodb', table_name)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    return table.scan(
        ProjectionExpression='FaceId,FullName',
        FilterExpression=Attr('Available').eq(True),
    )

def respond(err, res=None, status=200):
    return {
        'statusCode': 400 if err else status,
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin": "*"
        },
    }

def handle_options():
    return {
        'statusCode': 200,
        'body': 'OK',
        'headers': {
            "Content-Type": "text/plain",
            "Access-Control-Allow-Headers": "authorization,content-type",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Origin": "*"
        },
    }

def post_register(payload):
    if not 'Image' in payload:
        return respond(ValueError('No image found'))

    start_time = time.time()
    # Get the request with optional imageId
    request = {
        "ImageId": payload.get('ImageId', str(uuid.uuid4())),
        "Image": payload['Image']
    }
    if 'Bytes' in payload["Image"]:
        # Replace the image with decoded bytes and upload
        request["Image"] = {
            "Bytes": base64.b64decode(payload["Image"]["Bytes"])
        }
        # Upload the bytes to an S3 bucket defaulting to jpeg content
        content_type = "image/jpeg"
        index_bucket = INDEX_BUCKET
        index_key = '{}/{}.jpeg'.format(INDEX_PATH, request["ImageId"])
        upload_object(index_bucket, index_key, request["Image"]["Bytes"], content_type)
    elif 'S3Object' in payload["Image"]:
        # Set the bucket/key for based on provided input
        index_bucket = payload["Image"]["S3Object"]["Bucket"]
        index_key = payload["Image"]["S3Object"]["Name"]
    else:
        return respond(ValueError("No image found"))

    # Detect the face with recognition
    response = detect_face(request, rotate=payload.get('Rotate', 'ROTATE_0'))

    # Publish message payload with nested faces collection
    message = {
        "ThingName": payload["ThingName"],
        "Visitor": {
            "FaceId": response["Face"]["FaceId"],
            "Name": payload["FullName"],
            'Url': get_signed_url(index_bucket, index_key),
            'OrientationCorrection': response["OrientationCorrection"],
        },
        "Host": payload.get("Host")
    }
    print('sns publish response', json.dumps(publish_message(message)))

    # # Call into the /classify endpoint with the upload Bucket/Key
    # # TODO: Push this to an SQS in case needs to be re-tried
    # try:
    #     classify = {
    #         "RekognitionId": response["Face"]["FaceId"],
    #         "Name": payload["FullName"],
    #         "Bucket": index_bucket,
    #         "Key": index_key,
    #         "BoundingBox": response["Face"]["BoundingBox"],
    #         "OrientationCorrection": response["OrientationCorrection"]
    #     }
    #     print('classify face', json.dumps(classify))
    #     print('classify response', json.dumps(invoke_classify(CLASSIFY_URL, classify)))
    # except:
    #     print('error classifying face')

    # Turn bounding box values to decimal before saving
    face = {
        "FaceId": response["Face"]["FaceId"],
        "FullName": payload["FullName"],
        "Bucket": index_bucket,
        "Key": index_key,
        "BoundingBox": dict_to_decimal(response["Face"]["BoundingBox"]),
        "OrientationCorrection": response["OrientationCorrection"]
    }
    print('saving face', json.dumps(face))
    print('dynamodb response', json.dumps(update_index(face)))

    # Return the face details and time processed in to client
    payload = {
        "FaceDetails": response["FaceDetails"],
        "Confidence": response["Face"]["Confidence"],
        "OrientationCorrection": response["OrientationCorrection"],
        "ProcessedIn": time.time()-start_time
    }
    return respond(None, payload, response["Status"])

def get_hosts():
    start_time = time.time()
    response = scan_avaialable_hosts()
    payload = {
        "AvailableHosts": response['Items'],
        "ProcessedIn": time.time()-start_time
    }
    return respond(None, payload)

def lambda_handler(event, context):
    operation = event['httpMethod']
    if operation == 'OPTIONS':
        return handle_options()
    try:
        path = event['path']
        if operation == 'POST':
            body = json.loads(event['body'])
            if path == '/register':
                return post_register(body)
        elif operation == 'GET':
            if path == '/hosts':
                return get_hosts()
        return respond(ValueError('Unsupported method "{}" for path "{}"'.format(operation, path)))
    except ValueError as e:
        print('error', e)
        return respond(e)
