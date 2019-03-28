from score import Scorer
import cv2

# Get the updated scorer
model_dir = '../models'
scorer = Scorer(model_dir)
print(scorer.vecs.shape)

# get vectorized image
img = cv2.imread('../people/julbrigh_rotated.jpeg')
bounding_box = {'Width': 0.5240384340286255, 'Height': 0.7045895457267761, 'Left': 0.23557692766189575, 'Top': 0.16806723177433014}
rotate = 270
margin = 0
bbox = scorer.get_bbox(img, bounding_box)
print('bbox', bbox)
aligned, vec = scorer.vectorize(img, bbox, rotate)
print(vec.shape, vec.tolist())

# get the similar records
sim, z_score, prob, name = scorer.similar(vec)
print(sim, z_score, prob, name)
