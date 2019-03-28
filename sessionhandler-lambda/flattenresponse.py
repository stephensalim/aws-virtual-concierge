import json
import os
import boto3
import logging
import smtoolkit as vcsm

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.trigger={}'.format(json.dumps(event)))
       
        if type(event) == list:
            flattenvent = {}
            flattenvent['PreviousStateOutput'] = vcsm.flatten_jsonlist(event)
            flattenvent['SumerianMessageType'] = flattenvent['PreviousStateOutput']['SumerianMessageType']
            flattenvent['PreviousStateOutput'].pop('SumerianMessageType', None)
            result = flattenvent
       
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while looking for appointments")
        raise e
