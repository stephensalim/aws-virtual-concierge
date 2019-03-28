import boto3
import cv2
import os
import numpy as np
import time
from score import Scorer
from flask import Flask, request, jsonify
try:
    import Queue as queue # Pytnon2-3 compatability
except ImportError:
    import queue
from threading import Thread, Event

class ModelUploader(Thread):
    """ ModelUploader class
    The run() method will listen to a queue of fixed size and upload model to s3
    """

    def __init__(self, s3, model_bucket, model_key, scorer, queue_timeout=1):
        # Initialize the base class, with properties for model path etc
        super(ModelUploader, self).__init__()
        self.s3 = s3
        self.model_bucket = model_bucket
        self.model_key = model_key
        self.scorer = scorer
        # Create a queue of 1 so, we only upload one at a time
        self.q = queue.Queue(maxsize=1)
        self.queue_timeout=queue_timeout
        self.running = True

    def upload(self, vec, name):
        try:
            # Append the vec and name to the model now, and queue upload request
            self.scorer.append_model(vec, name)
            self.q.put_nowait(time.time())
            print('upload queue: {}'.format(name))
        except queue.Full:
            print('upload queue full')
        except Exception as e:
            print('upload error: {}'.format(e))
        return None

    def run(self):
        while self.running:
            try:
                append_time = self.q.get(timeout=self.queue_timeout)
                print('upload started: {}'.format(append_time))
                try:
                    # Save the latest version of the model, and upload
                    start_time = time.time()
                    filename = self.scorer.save_model()
                    self.s3.Object(self.model_bucket, self.model_key).upload_file(filename)
                    print('upload {} in {}, wait {}'.format(self.model_key,
                          time.time()-start_time, start_time-append_time))
                except botocore.exceptions.ClientError as e:
                    print('error uploading: {}'.format(e))
                self.q.task_done()
            except queue.Empty:
                pass

    def join(self):
        print('gracefully shutting down queue')
        self.running = False
        self.q.join()
        super(ModelUploader, self).join()

s3 = boto3.resource('s3')
model_bucket = os.getenv('DEEPLENS_MODEL_BUCKET', 'deeplens-virtual-concierge-model')
model_path = os.getenv('DEEPLENS_MODEL_PATH', 'mobilenet1')
model_dir = os.getenv('MODEL_DIR', '/tmp')
model_files = ['mobilenet1-0000.params','mobilenet1-symbol.json','people.npz']

# Global variables
scorer = None
uploader = None

def downlad_model(model_dir):
    print('downloading mobilenet model')
    download_start = time.time()
    bucket = s3.Bucket(model_bucket)
    for file in model_files:
        key = os.path.join(model_path, file)
        dest = os.path.join(model_dir, file)
        print('downloading {} to {}'.format(key, dest))
        bucket.download_file(key, dest)
    print('Loaded {} files in {}s'.format(len(model_files), time.time()-download_start))

def load_model(model_dir):
    global scorer, uploader
    scorer = Scorer(model_dir)
    people_key = '{}/{}'.format(model_path, model_files[-1])
    uploader = ModelUploader(s3, model_bucket, people_key, scorer)
    return uploader

# Lambda like function handler
def function_handler(event, context):
    if event and 'Bucket' in event and 'Key' in event:
        score_start = time.time()
        # Load object into cv2
        bucket, key = event['Bucket'], event['Key']
        image_object = s3.Object(bucket, key)
        data = np.frombuffer(image_object.get()['Body'].read(), np.uint8)
        img = cv2.imdecode(data, -1)
        # Get the relative bounding box
        bbox = scorer.get_bbox(img, event.get('BoundingBox'))
        rotate = 0
        if 'OrientationCorrection' in event:
            rotate = int(event['OrientationCorrection'].strip('ROTATE_'))
        margin = int(event.get('Margin') or 0)
        # Vectorize the image
        aligned, vec = scorer.vectorize(img, bbox=bbox, rotate=rotate, margin=margin)
        event["Vector"] = vec.tolist()
        # If we have been given a name, queue upload back to S3
        if 'Name' in event:
            uploader.upload(vec, event['Name'])
        print('Download and score {}/{} in {}s'.format(bucket, key, time.time()-score_start))
        return event
    return { 'ok': False, 'error': 'Image Bucket and Key required' }

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello score API!"

'''
# Post to this endpoint with
curl -X POST -v -H "Content-Type: application/json" \
    -d '{ "Bucket": "virtual-concierge-index-ap-southeast-2", "Key": "test.jpeg", "BoundingBox": {"Width":0.5240384340286255,"Height":0.5240384340286255,"Left":0.5240384340286255,"Top":0.5240384340286255}, "OrientationCorrection": "ROTATE_270" }' \
    http://127.0.0.1:5000/classify
'''
@app.route('/classify', methods = ['POST'])
def classify():
    return jsonify(function_handler(request.get_json(), None))

@app.route('/update', methods = ['POST'])
def update():
    downlad_model(model_dir)
    uploader.join() # Stop the current uploader class, and re-load
    load_model(model_dir).start()
    return jsonify({ 'ok': True, 'size': scorer.vecs.shape[0] })

if __name__ == '__main__':
    downlad_model(model_dir)
    load_model(model_dir).start()
    app.run(host='0.0.0.0')
