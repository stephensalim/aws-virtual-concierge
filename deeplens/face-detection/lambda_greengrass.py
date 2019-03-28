#*****************************************************
#                                                    *
# Copyright 2018 Amazon.com, Inc. or its affiliates. *
# All Rights Reserved.                               *
#                                                    *
#*****************************************************
""" A sample lambda for face detection"""
from threading import Thread, Event
import os
import json
import numpy as np
import awscam
import cv2
import mo
import greengrasssdk
from botocore.session import Session
import time
import datetime
import random
# Custom imports
from image import ImageUploader
from score import Scorer

class LocalDisplay(Thread):
    """ Class for facilitating the local display of inference results
        (as images). The class is designed to run on its own thread. In
        particular the class dumps the inference results into a FIFO
        located in the tmp directory (which lambda has access to). The
        results can be rendered using mplayer by typing:
        mplayer -demuxer lavf -lavfdopts format=mjpeg:probesize=32 /tmp/results.mjpeg
    """
    def __init__(self, resolution):
        """ resolution - Desired resolution of the project stream """
        # Initialize the base class, so that the object can run on its own
        # thread.
        super(LocalDisplay, self).__init__()
        # List of valid resolutions
        RESOLUTION = {'1080p' : (1920, 1080), '720p' : (1280, 720), '480p' : (858, 480)}
        if resolution not in RESOLUTION:
            raise Exception("Invalid resolution")
        self.resolution = RESOLUTION[resolution]
        # Initialize the default image to be a white canvas. Clients
        # will update the image when ready.
        self.frame = cv2.imencode('.jpg', 255*np.ones([640, 480, 3]))[1]
        self.stop_request = Event()

    def run(self):
        """ Overridden method that continually dumps images to the desired
            FIFO file.
        """
        # Path to the FIFO file. The lambda only has permissions to the tmp
        # directory. Pointing to a FIFO file in another directory
        # will cause the lambda to crash.
        result_path = '/tmp/results.mjpeg'
        # Create the FIFO file if it doesn't exist.
        if not os.path.exists(result_path):
            os.mkfifo(result_path)
        # This call will block until a consumer is available
        with open(result_path, 'w') as fifo_file:
            while not self.stop_request.isSet():
                try:
                    # Write the data to the FIFO file. This call will block
                    # meaning the code will come to a halt here until a consumer
                    # is available.
                    fifo_file.write(self.frame.tobytes())
                except IOError:
                    continue

    def set_frame_data(self, frame):
        """ Method updates the image data. This currently encodes the
            numpy array to jpg but can be modified to support other encodings.
            frame - Numpy array containing the image data tof the next frame
                    in the project stream.
        """
        ret, jpeg = cv2.imencode('.jpg', cv2.resize(frame, self.resolution))
        if not ret:
            raise Exception('Failed to set frame data')
        self.frame = jpeg

    def join(self):
        self.stop_request.set()

# see if it's possible to use x-ray in greengrass lambda_handler
# see: https://docs.aws.amazon.com/xray/latest/devguide/scorekeep-lambda.html#scorekeep-lambda-worker

def greengrass_infinite_infer_run():
    """ Entry point of the lambda function"""
    try:
        # This face detection model is implemented as single shot detector (ssd).
        model_type = 'ssd'
        output_map = {1: 'face'}
        # Create an IoT client for sending to messages to the cloud.
        client = greengrasssdk.client('iot-data')
        thing_name = os.environ['AWS_IOT_THING_NAME']
        iot_topic = '$aws/things/{}/infer'.format(thing_name)
        # Create a local display instance that will dump the image bytes to a FIFO
        # file that the image can be rendered locally.
        local_display = LocalDisplay('480p')
        local_display.start()
        # Create a s3 backgound uploader
        session = Session()
        s3 = session.create_client('s3', region_name=os.getenv('REGION_NAME', 'ap-southeast-2'))
        bucket = os.getenv('FRAMES_BUCKET', 'virtual-concierge-frames-ap-southeast-2')
        uploader = ImageUploader(s3, bucket, client, iot_topic)
        uploader.start()
        # The sample projects come with optimized artifacts, hence only the artifact
        # path is required.
        model_dir = '/opt/awscam/artifacts/'
        model_path = model_dir + 'mxnet_deploy_ssd_FP16_FUSED.xml'
        # Load the model onto the GPU.
        msg = 'Loading face detection model for {}'.format(thing_name)
        client.publish(topic=iot_topic, payload=msg)
        model_start = time.time()
        model = awscam.Model(model_path, {'GPU': 1})
        msg = 'Face detection model loaded in {}s'.format(time.time()-model_start)
        client.publish(topic=iot_topic, payload=msg)
        # Attempt to load scorer library
        try:
            model_start = time.time()
            scorer = Scorer(model_dir)
            msg = 'Image classification model loaded {} in {}s'.format(scorer.vecs.shape[0], time.time()-model_start)
            client.publish(topic=iot_topic, payload=msg)
        except Exception as e:
            print('Failed to load scorer', e)
        # Set the threshold for detection
        detection_threshold = float(os.getenv('DETECT_THRESHOLD', '0.7'))
        # This is the similarity threshold
        sim_threshold = float(os.getenv('DETECT_THRESHOLD', '0.99'))
        # The height and width of the training set images
        input_height = 300
        input_width = 300
        # Do inference until the lambda is killed.
        while True:
            # get thing shadow state, to see if we should register
            cloud_output = {}
            # Get a frame from the video stream
            cloud_output["frame_start"] =  time.time();
            ret, frame = awscam.getLastFrame()
            if not ret:
                raise Exception('Failed to get frame from the stream')
            # Future integrate the shadow callback
            if False:
                cloud_output["shadow_start"] = time.time();
                shadow = client.get_thing_shadow(thingName=thing_name)
                jsonState = json.loads(shadow["payload"])
                register = jsonState['state']['desired'].get('register')
                cloud_output["shadow_register"] = register;
                cloud_output["shadow_latency"] = time.time()-cloud_output["shadow_start"];
            # Resize frame to the same size as the training set.
            cloud_output["detect_start"] = time.time()
            frame_resize = cv2.resize(frame, (input_height, input_width))
            # Run the images through the inference engine and parse the results using
            # the parser API, note it is possible to get the output of doInference
            # and do the parsing manually, but since it is a ssd model,
            # a simple API is provided.
            parsed_inference_results = model.parseResult(model_type,
                                                         model.doInference(frame_resize))
            cloud_output["detect_latency"] = time.time()-cloud_output["detect_start"];
            # Compute the scale in order to draw bounding boxes on the full resolution
            # image.
            yscale = float(frame.shape[0]/input_height)
            xscale = float(frame.shape[1]/input_width)
            # Dictionary to be filled with labels and probabilities for MQTT
            # Get the detected faces and probabilities
            for i, obj in enumerate(parsed_inference_results[model_type]):
                if obj['prob'] > detection_threshold:
                    # Add bounding boxes to full resolution frame
                    xmin = int(xscale * obj['xmin']) \
                           + int((obj['xmin'] - input_width/2) + input_width/2)
                    ymin = int(yscale * obj['ymin'])
                    xmax = int(xscale * obj['xmax']) \
                           + int((obj['xmax'] - input_width/2) + input_width/2)
                    ymax = int(yscale * obj['ymax'])
                    # Set the default title and color
                    title = '{:.2f}%'.format(obj['prob'] * 100)
                    color = (255, 0, 0) # blue
                    upload = False
                    if scorer:
                        try:
                            # Attempt to find similar face
                            cloud_output['classify_start'] = time.time()
                            bbox = [xmin,ymin,xmax,ymax]
                            aligned, vec = scorer.vectorize(frame, bbox)
                            sim, z_score, prob, name = scorer.similar(vec)
                            if prob>=sim_threshold:
                                title = name
                                if round(prob, 3) < 1.0:
                                    title += ' ({:.2f}%)'.format(prob * 100)
                                color = (0, 255, 0) # green
                                upload = True
                            cloud_output['classify'] =  {
                                'bbox': bbox,
                                'name': name,
                                'sim': float(sim),
                                'zscore': float(z_score),
                                'prob': float(prob)
                            }
                            cloud_output['classify_latency'] = time.time()-cloud_output['classify_start']
                        except Exception as e:
                            msg = "Face similarity error: " + str(e)
                            client.publish(topic=iot_topic, payload=msg)
                    if upload:
                        try:
                            metadata={
                                'ThingName': thing_name,
                                'FullName': title,
                                'Classify': json.dumps(cloud_output['classify'])
                            }
                            crop_img = uploader.crop(frame, xmin, ymin, xmax, ymax)
                            item = uploader.upload(crop_img, i, time.time(), metadata)
                            if item:
                                cloud_output['upload_key'] = item['key']
                            else:
                                cloud_output['upload_skip'] = True
                        except Exception as e:
                            msg = "Upload error: " + str(e)
                            client.publish(topic=iot_topic, payload=msg)
                    # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                    # for more information about the cv2.rectangle method.
                    # Method signature: image, point1, point2, color, and tickness.
                    cloud_output["draw_start"] = time.time()
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 10)
                    # Amount to offset the label/probability text above the bounding box.
                    text_offset = 12
                    cv2.putText(frame, title,
                                (xmin, ymin-text_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.5, color, 6)
                    # Store label and probability to send to cloud
                    cloud_output[output_map[obj['label']]] = obj['prob']
                    cloud_output["draw_latency"] = time.time()-cloud_output["draw_start"]
            # Set the next frame in the local display stream.
            local_display.set_frame_data(frame)
            cloud_output["frame_end"] = time.time()
            cloud_output["frame_latency"] = cloud_output["frame_end"]-cloud_output["frame_start"];
            client.publish(topic=iot_topic, payload=json.dumps(cloud_output))
    except Exception as ex:
        print('Error in face detection lambda: {}'.format(ex))

greengrass_infinite_infer_run()

# This is a dummy handler and will not be invoked
# Instead the code above will be executed in an infinite loop for our example
def function_handler(event, context):
    return
