# Virtual concierge

## Overivew

Virtual cocierge is an integrated solution that provide facial rekogition at the edge powered by Deep Lens and AI in the cloud to greet a user with a Summerian host.

## Lambda functions

### Deeplens Face detection

This lambda runs on the deeplens camera and is responsible for the inference that detects faces
in frame of a video stream. For each face it detects it pushed the croped face image to S3 for matching.

### Rekognition Detect faces

This lambda is triggered by a putObject event from the deeplens face detection lambda and calls
[AWS Rekognition](https://aws.amazon.com/rekognition/) to get a list of faces looked up against dynamodb.

It will then raise an SNS with the topic that matches the IoT Topic, and includes Faces, or Words eg:

```
{
  "TopicUrl": "$aws/things/XXXXXXX/shadow/get",
  "Url": "https://s3.amazonaws.com/x/y.jpg",
  "Faces": [
    {
      "RekognitionId": "aaaa-bbbb-cccc",
      "Name": "First Last",
      "Confidence": 0.995
    }
  ]
}
```

### Rekognition Index faces

This lambda will index a face into Rekognition, and store the name pulled from metadata into dynamodb.

## Development and Testing

Setup your deeplens camera and create all the required IAM roles.  

Build and deploy the greengrass face detection template, and publish version 1.

We will then create following resources:
* 2 lambda functions (index & detect)
* 2 S3 bucket (index & faces)
* 1 DynamoDB table

Using [AWS Serverless Application Model, or SAM](https://github.com/awslabs/serverless-application-model) deploy the above resources.

### Build

To build the lambda source packages run the following command:

```
make package-rekognition profile=<your_aws_profile>
```

### Deployment

To deploy the lambda functions run the following command:

```
make deploy-rekognition profile=<your_aws_profile>
```


### Actions

Below is a sequence of events which include the register flow

#### Registration Selfie

1. GET Page with ThingName as query string
2. Page requests available hosts rekogitionId as value.
3. User specifies name (FUTURE: signs in with OAuth)
4. User specifies host
5. User takes photo
6. Page sends API payload (thing_name, visitor_name, host_id, photo_bytes)
7. API confirms photo is selfie with 1 face.
8. API rekognises face, creates new rekognition if not exists
9. API creates DDB record with payload
10. API uploads face to S3 with Metadata
11. API publishes RegisterComplete SQS
12. Publish FaceRecognised SNS

#### Deeplens frame

1. Update frame to S3 with payload (thing_name, visitor_name)
2. Verify visitor with Rekognition
3. Publish FaceRecognised SNS

#### Registration Deployment

1. Subscribe Lambda to RegistrationComplete SQS
2. Load model from S3
3. Call Model Server API to vectorize Face with Boundary box & Rotation.
4. Add Name and vectorized content to model
5. Upload model to S3
6. Publish ModelUpdated SNS
7. Subscribe email to ModelUpdated SNS
8. Manually deploy Deeplens Model

#### Receptionist Workflow

1. Subscribe to FaceRecognised SNS
2. Start step function
