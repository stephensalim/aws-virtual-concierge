import datetime
import time
try:
    import Queue as queue # Pytnon2-3 compatability
except ImportError:
    import queue
from threading import Thread, Event
import cv2

class ImageUploader(Thread):
    """ ImageUploader class
    The run() method will listen to a queue of fixed size and upload to s3
    """

    def __init__(self, s3_client, s3_bucket, iot_client, iot_topic, queue_size=3):
        # Initialize the base class, so that the object can run on its own thread
        super(ImageUploader, self).__init__()
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.iot_client = iot_client
        self.iot_topic = iot_topic
        self.q = queue.Queue(maxsize=queue_size)

    def log(self, msg):
        if self.iot_client and self.iot_client:
            return self.iot_client.publish(topic=self.iot_topic, payload=msg)
        print(msg)

    # define a fucntion to return a crop farme to target size of badge image
    def crop(self, img, xmin, ymin, xmax, ymax, image_height=160, image_width=119):
        ymin, ymax = max(0, ymin-(ymax-ymin)), min(ymax+(ymax-ymin), img.shape[0])
        xmin, xmax = max(0, int(xmin-0.5*(xmax-xmin))), min(int(xmax+0.5*(xmax-xmin)), img.shape[1])
        return img[ymin:ymax, xmin:xmax] #return without resize
        #return cv2.resize(img[ymin:ymax, xmin:xmax], (image_width, image_height))

    def upload(self, img, index, timestamp, metadata={}):
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            success, jpg_data = cv2.imencode('.jpg', img, encode_param)
            if success:
                now = datetime.datetime.now()
                key = "faces/{:04d}_{:02d}_{:02d}/{:02d}_{:02d}/{}_{}.jpg".format(
                    now.year, now.month, now.day, now.hour, now.minute, int(timestamp), index)
                item = {
                    'bucket':self.s3_bucket,
                    'key':key,
                    'body':jpg_data.tostring(),
                    'metadata': metadata
                }
                self.q.put_nowait(item)
                return item
        except queue.Full:
            print('upload queue full')
        except Exception as e:
            print('upload error: {}'.format(e))
        return None

    def run(self):
        while True:
            item = self.q.get()
            try:
                start_time = time.time()
                response = self.s3_client.put_object(
                    Body=item['body'], #ACL='public-read',
                    Bucket=item['bucket'],
                    Key=item['key'],
                    Metadata=item['metadata'])
                image_url = 'https://s3.amazonaws.com/'+item['bucket']+'/'+item['key'];
                msg = 'upload {} in {}'.format(image_url, time.time()-start_time)
                self.log(msg)
            except Exception as e:
                self.log('error uploading: {}'.format(e))
            self.q.task_done()

    def join(self):
        self.q.join()
