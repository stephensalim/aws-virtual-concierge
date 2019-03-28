import os
import time
import mxnet as mx
import numpy as np
from math import erf, sqrt
import cv2

print('intialize mxnet: {}, np: {}, cv2: {}'.format(mx.__version__, np.__version__, cv2.__version__))

class Scorer():

    def __init__(self, model_dir, image_size=(112,112)):
        # Load the mobilenet face model
        model_start = time.time()
        self.image_size = image_size
        model_str = os.path.join(model_dir, 'mobilenet1,0')
        print('loading face model {}, size: {}'.format(model_str, image_size))
        self.model = self.get_model(mx.cpu(), image_size, model_str, 'fc1')
        print('face model loaded in {}'.format(time.time()-model_start))
        # Load people database, if we can't find or an error, create new db
        people_start = time.time()
        try:
            self.people_path = os.path.join(model_dir, 'people.npz')
            print('loading face db {}'.format(self.people_path))
            people_db = np.load(self.people_path)
            self.vecs = people_db['vecs']
            self.names = people_db['names']
        except FileNotFoundError as e:
            print('initialize face db', e)
            self.clear_model()
        print('face db loaded in {}s, vecs:{}'.format(time.time()-people_start, self.vecs.shape))

    def clear_model(self):
        self.vecs = np.zeros((0,128), dtype=float)
        self.names = np.zeros((0), dtype=str)

    def append_model(self, vec, name):
        # Flatten vec into 2d array to append to vecs
        vec = np.reshape(vec, (1, -1))
        assert self.vecs.shape[1]==vec.shape[1]
        self.vecs, self.names = np.append(self.vecs, vec, axis=0), np.append(self.names, name)

    def save_model(self):
        people_start = time.time()
        np.savez(self.people_path, vecs=self.vecs, names=self.names)
        print('face db saved in {}s, vecs:{}'.format(time.time()-people_start, self.vecs.shape))
        return self.people_path

    def get_model(self, ctx, image_size, model_str, layer):
        _vec = model_str.split(',')
        assert len(_vec)==2
        prefix = _vec[0]
        epoch = int(_vec[1])
        sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
        all_layers = sym.get_internals()
        sym = all_layers[layer+'_output']
        model = mx.mod.Module(symbol=sym, context=ctx, label_names = None)
        #model.bind(data_shapes=[('data', (args.batch_size, 3, image_size[0], image_size[1]))], label_shapes=[('softmax_label', (args.batch_size,))])
        model.bind(data_shapes=[('data', (1, 3, image_size[0], image_size[1]))])
        model.set_params(arg_params, aux_params)
        return model

    def get_input(self, image_size, img, bbox=None, rotate=0, margin=44):
        # Call preprocess() to generate aligned images
        if bbox is None:
            det = np.zeros(4, dtype=np.int32)
            det[0] = int(img.shape[1]*0.0625)
            det[1] = int(img.shape[0]*0.0625)
            det[2] = img.shape[1] - det[0]
            det[3] = img.shape[0] - det[1]
        else:
            det = bbox
        # Crop
        bb = np.zeros(4, dtype=np.int32)
        bb[0] = np.maximum(det[0]-margin/2, 0)
        bb[1] = np.maximum(det[1]-margin/2, 0)
        bb[2] = np.minimum(det[2]+margin/2, img.shape[1])
        bb[3] = np.minimum(det[3]+margin/2, img.shape[0])
        img = img[bb[1]:bb[3],bb[0]:bb[2],:]
        # Rotate if required
        if 0 < rotate and rotate < 360:
            rows,cols,_ = img.shape
            M = cv2.getRotationMatrix2D((cols/2,rows/2),360-rotate,1)
            img = cv2.warpAffine(img,M,(cols,rows))
        # Resize and transform
        img = cv2.resize(img, (image_size[1], image_size[0]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        aligned = np.transpose(img, (2,0,1))
        return aligned

    def get_feature(self, model, aligned):
        def l2_normalize(X):
            norms = np.sqrt((X * X).sum(axis=1))
            X /= norms[:, np.newaxis]
            return X
        input_blob = np.expand_dims(aligned, axis=0)
        data = mx.nd.array(input_blob)
        db = mx.io.DataBatch(data=(data,))
        model.forward(db, is_train=False)
        embedding = model.get_outputs()[0].asnumpy()
        embedding = l2_normalize(embedding).flatten()
        return embedding

    def get_bbox(self, img, box):
        # Return the relative bounding boxes for each face
        if box != None and 'Left' in box and 'Top' in box and 'Width' in box and 'Height' in box:
            height, width, _ = img.shape
            x1 = int(box['Left'] * width)
            y1 = int(box['Top'] * height)
            x2 = int(box['Left'] * width + box['Width'] * width)
            y2 = int(box['Top'] * height + box['Height']  * height)
            return (x1, y1, x2, y2)
        return None

    def vectorize(self, img, bbox=None, rotate=0, margin=0):
        aligned = self.get_input(self.image_size, img, bbox=bbox, rotate=rotate, margin=margin)
        vec = self.get_feature(self.model, aligned)
        return aligned, vec

    def similar(self, vec):
        def phi(x):
            #'Cumulative distribution function for the standard normal distribution'
            return (1.0 + erf(x / sqrt(2.0))) / 2.0
        assert self.vecs.shape[1]==vec.shape[0]
        sims = np.dot(self.vecs, vec)
        sim_idx = np.argmax(sims)
        sim = sims[sim_idx]
        z_score = (sim - sims.mean()) / sims.std()
        return sim, z_score, phi(z_score), self.names[sim_idx]
