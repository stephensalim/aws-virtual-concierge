import json
import logging
import os
import smtoolkit as vcsm

# Set logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sessiontable = os.environ['sessiontable']

def lambda_handler(event, context):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.lambda_handler.trigger={}'.format(json.dumps(event)))
        result = {}
        result = event
        
        vcsm.deletesession_session(event['Visitor']['FaceId'],sessiontable)

        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.lambda_handler.result={}'.format(json.dumps(result)))
        return(result)  
    except Exception as e:
        print(e)
        print("Exception error while checking if face are detected")
        raise e
    