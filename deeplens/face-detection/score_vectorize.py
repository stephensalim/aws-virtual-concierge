import boto3
import csv
import cv2
import numpy as np
import os
from score import Scorer

rekognition = boto3.client('rekognition')

def get_bboxes(img, margin=0):
    # Detect faces
    ret, buf = cv2.imencode('.jpg', img)
    ret = rekognition.detect_faces(
        Image={
            'Bytes': buf.tobytes()
        },
        Attributes=['DEFAULT'],
    )
    # Get the rotation
    rotate = int(ret['OrientationCorrection'].strip('ROTATE_'))
    # Return the bounding boxes for each face
    height, width, _ = img.shape
    bboxes = []
    for face in ret['FaceDetails']:
        box = face['BoundingBox']
        x1 = int(box['Left'] * width)
        y1 = int(box['Top'] * height)
        x2 = int(box['Left'] * width + box['Width'] * width)
        y2 = int(box['Top'] * height + box['Height']  * height)
        bboxes.append((x1, y1, x2, y2))
    return bboxes, rotate

# Get the updated scorer
model_dir = '../models'
scorer = Scorer(model_dir)

# Initialize the people database
scorer.clear_model()

# Scan through the list of people
ingest_dir = '../../rekognition-ingest'
with open(os.path.join(ingest_dir, 'people.tsv'), 'rb') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if True: #row[2].startswith('MEL') or row[2].startswith('SYD'):
            fn = os.path.join(ingest_dir, 'images/{}.jpeg'.format(row[0]))
            img = cv2.imread(fn)
            bboxes, rotate = get_bboxes(img)
            aligned, vec = scorer.vectorize(img, bboxes[0], rotate)
            scorer.append_model(vec, row[1])
            print(row[1])

scorer.save_model()

# Upload model to s3
