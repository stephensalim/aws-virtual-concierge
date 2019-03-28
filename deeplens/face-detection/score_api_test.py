from score_api import function_handler, load_model

uploader = load_model('../models')

event = { "RekognitionId": "980e0449-1231-4eaf-acd2-368e42cfb0ac", "Name": "Joel Turner", "Bucket": "virtual-concierge-index-ap-southeast-2", "Key": "index/409955ca-7d58-4650-9e98-b2731ef4820d.jpeg", "BoundingBox": { "Width": 0.7950869798660278, "Height": 0.591346025466919, "Left": 0.11635400354862213, "Top": 0.1826920062303543 }, "OrientationCorrection": "ROTATE_0" }
print(function_handler(event, None))

uploader.start()
print(uploader)
uploader.join()
print(uploader)

# Call also via API using boto requests library
import json
from botocore.vendored import requests

headers = { 'Content-Type': 'application/json' }
url = "http://13.239.111.108/classify"
response = requests.request("POST", url, data=json.dumps(event), headers=headers)
payload = json.loads(response.text)
print(payload)
