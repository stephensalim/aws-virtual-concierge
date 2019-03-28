import boto3
import io
from PIL import Image
import json
import decimal

rekognition = boto3.client('rekognition', region_name='ap-southeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

COLLECTION = "virtual-concierge"
DDB_TABLE = "virtual-concierge-face"

# Load a test image
image = Image.open("test/image_badge.jpg")
stream = io.BytesIO()
image.save(stream,format="JPEG")
img_bytes = stream.getvalue()

response = rekognition.detect_labels(
    Image={'Bytes': img_bytes},
    MaxLabels=123,
    MinConfidence=0.9
)

labels = response['Labels']

response = rekognition.search_faces_by_image(
    CollectionId=COLLECTION,
    Image={'Bytes':img_bytes},
    FaceMatchThreshold=0.9,
    MaxFaces=1,
)

faces = []
for match in response['FaceMatches']:
    table = dynamodb.Table('virtual-concierge-face')
    face = table.get_item(Key={'RekognitionId':match['Face']['FaceId']})
    if 'Item' in face:
        item = face['Item']
        item['Confidence'] = match['Face']['Confidence']
        item['Labels'] = labels
        faces.append(item)

print(json.dumps(faces, indent=4))
