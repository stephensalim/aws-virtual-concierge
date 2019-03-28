import boto3

s3 = boto3.resource('s3', region_name='ap-southeast-2')

# Get list of people for indexing
with open('people.tsv','r') as tsv:
    images = [line.strip().split('\t') for line in tsv]

# Iterate through list to upload objects to S3, so lambda triggers training
for image in images:
    fn = 'images/{}.jpeg'.format(image[0])
    file = open(fn,'rb') # with open(fn,'rb') as file:
    object = s3.Object('virtual-concierge-index-ap-southeast-2','index/'+ image[0]+'.jpg')
    md = {'FullName':image[1]}
    if len(image) == 4: # add fully qualified details if they are available
        md = {
            'FullName':image[1],
            'JobTitle':image[2],
            'DepartmentlName':image[3],
        }
    ret = object.put(Body=file, Metadata=md)
    print('uploaded: {}'.format(image[1]))
