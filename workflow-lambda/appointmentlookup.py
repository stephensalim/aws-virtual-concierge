import json
import os
import boto3
import logging
import smtoolkit as vcsm

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.trigger={}'.format(json.dumps(event)))
        guestid = event['Visitor']['FaceId']
        result = event
        result['Appointment'] = {}
        
        ##############
        # Demo Code - This section should ber where the function Search for appointment and return Hostname
        #############
        result['Appointment']['HostName'] = "Stephen Salim"
        result['Appointment']['Room'] = "BruceLee"
        result['Appointment']['Found'] = "True"
        
        if result['Appointment'] is not None:
            result['Appointment']['Found'] = "True"            
        else:
            result['Appointment'] = {}
            result['Appointment']['Found'] = "False"
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while looking for appointments")
        raise e
