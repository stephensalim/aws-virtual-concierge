import boto3
import cv2
import time
from image import ImageUploader

s3_client = boto3.client('s3', region_name='ap-southeast-2')
iot_client = boto3.client('iot-data', region_name='us-east-1')
iot_topic = '$aws/things/deeplens_zz8BbGbNSVuHCsyqtWOM4Q/infer'
uploader = ImageUploader(
    s3_client, 'virtual-concierge-frames-ap-southeast-2',
    iot_client, iot_topic
)
uploader.start()

# upload a number of files
for i in range(1, 10):
    img = cv2.imread('../people/julbrigh_test.jpg')
    img = uploader.crop(img, 0, 0, 200, 200) # test crop
    item = uploader.upload(img, i, time.time(), metadata={}) # test upload
    if item:
        print(item['key'])
