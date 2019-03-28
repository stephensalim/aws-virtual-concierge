DevLabs

In this Labs we will be creating a Virtual Concierge Environment that will greet you based on the face that are detected.

Architectual diagram

Frist thing first is Roles and Identity, You can do anything without this
1. Deploy IAM Roles & IdentityPool CFN

Next thing is we will create the Messaging layer of the architecture, this layer will be responsible to handle all messaging that will interact with the workflow.
2. Deploy Interfacing Layers (SQS SNS) CFN

Next thing we will start creating the workflow that will be responsible to orchestrate the decission making on what should our sumerian host say and do.
3. Create S3 bucket to Store all Codes.
   Deploy WorkFlow & DynamoDBs CFN

aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml

 aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"

4. Connect the SNS topic.

5. Import Sumerian Scene. Deploy Scene


=====


246  git clone https://sssalimbitbucket@bitbucket.org/sssalimbitbucket/devlabs-virtualconcierge.git
  247  cd devlabs-virtualconcierge/
  248  git add -A
  249  git commit -m "DevLabs"
  250  git push 
  251  git push origin master
  252  aws cloudformation --region ap-southeast-2 create-stack vc-identitiy
  253  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-identity --template-name file://vc-identity.yaml
  254  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-identity --template-body file://vc-identity.yaml
  255  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-identity --template-body file://vc-identity.yaml --capabilities CAPABILITY_IAM
  256  aws cloudformation --region ap-southeast-2 update-stack --stack-name vc-identity --template-body file://vc-identity.yaml --capabilities CAPABILITY_IAM
  257  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-identity --template-body file://vc-messaging.yaml --capabilities CAPABILITY_IAM
  258  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-messaging --template-body file://vc-messaging.yaml --capabilities CAPABILITY_IAM
  259  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-codebucket --template-body file://vc-codebucket.yaml --capabilities CAPABILITY_IAM
  260  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-codebucket --template-body file://vc-codebucket.yaml --capabilities CAPABILITY_IAM --parameters  YourFullName=sssalim
  261  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-codebucket --template-body file://vc-codebucket.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=YourFullName,ParameterValue=sssalim
  262  ls
  263  cd sessionhandler-lambda/
  264  ls
  265  aws cloudformation --region ap-southeast-2 update-stack --stack-name vc-identity --template-body file://vc-identity.yaml --capabilities CAPABILITY_IAM
  266  cd ..
  267  aws cloudformation --region ap-southeast-2 update-stack --stack-name vc-identity --template-body file://vc-identity.yaml --capabilities CAPABILITY_IAM
  268  aws cloudformation --region ap-southeast-2 update-stack --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_IAM
  269  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_IAM
  270  aws cloudformation --region ap-southeast-2 update-stack --stack-name vc-messaging --template-body file://vc-messaging.yaml --capabilities CAPABILITY_IAM
  271  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  272  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole --capabilites CAPABILITY_AUTO_EXPAND
  273  aws cloudformation --region ap-southeast-2 create-stack --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  274* aws cloudformation --region ap-southeast-2 pac --stack-name vc-workflow --template-body file://vc-workflow.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  275  aws cloudformation --region ap-southeast-2 package --template-file file://vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file vc-workflow-output.yml 
  276  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file vc-workflow-output.yml 
  277  aws cloudformation --region ap-southeast-2 deploy --stack-name vc-workflow --template-file vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  278  aws cloudformation deploy --region ap-southeast-2 deploy --stack-name vc-workflow --template-file vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameters ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  279  aws cloudformation deploy --region ap-southeast-2 deploy --stack-name vc-workflow --template-file vc-workflow-output.yaml --parameter-overrides ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole --capabilities CAPABILITY_AUTO_EXPAND 
  280  aws cloudformation deploy
  281  aws cloudformation deploy --region ap-southeast-2 deploy --stack-name vc-workflow --template-file vc-workflow-output.yaml
  282* aws cloudformation deploy --region ap-southeast-2 deploy --stack-name vc-workflow --template-fi
  283  aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  284  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yml 
  285  aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  286  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml 
  287  aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides ParameterKey=SumerianMessageQueueFIFO,ParameterValue="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" ParameterKey=WorkflowNotificationSNSTopic,ParameterValue=WorkflowNotificationSNSTopic ParameterKey=WorkflowFunctionsExecutionRole,ParameterValue=WorkflowFunctionsExecutionRole
  288  aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole=WorkflowFunctionsExecutionRole
  289   aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"
  290  aws cloudformation --region ap-southeast-2 package --template-file file://vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmpvc-workflow-output.yml 
  291  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yml 
  292  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml 
  293   aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"
  294  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml 
  295   aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"
  296  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml 
  297   aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"
  298  aws cloudformation --region ap-southeast-2 package --template-file vc-workflow.yaml --s3-bucket sssalim-workflowcodebucket-ap-southeast-2-022787131977 --output-template-file /tmp/vc-workflow-output.yaml ;aws cloudformation deploy --region ap-southeast-2 --stack-name vc-workflow --template-file /tmp/vc-workflow-output.yaml --capabilities CAPABILITY_AUTO_EXPAND --parameter-overrides SumerianMessageQueueFIFO="https://sqs.ap-southeast-2.amazonaws.com/022787131977/SumerianMessageQueueFIFO.fifo" WorkflowNotificationSNSTopic=WorkflowNotificationSNSTopic WorkflowFunctionsExecutionRole="arn:aws:iam::022787131977:role/vc-identity-WorkflowFunctionsExecutionRole-1FHMIM906V56K"
  299  history

