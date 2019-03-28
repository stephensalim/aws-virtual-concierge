import json
import os
import boto3
import logging
import smtoolkit as vcsm
import uuid
 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def process_payload(facerec):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.process_payload.trigger={}'.format(json.dumps(facerec)))
        tablename = os.environ['sessiontable']
        visitorid = facerec['Visitor']['FaceId']
        searchresult = vcsm.find_session(visitorid,tablename)
        print(searchresult)
        #Find Session
        
        if 'Item' in searchresult and searchresult['Item'] != None:
            print(searchresult)
            sessionid = searchresult['Item']['SessionId']
            hostnotiftoken = searchresult['Item']['HostNotificationToken']
            hostarrivtoken = searchresult['Item']['HostArrivalToken']        
            remind_host = os.environ['ResponseUrl'] + "?"+ vcsm.generate_params('remind_host',hostnotiftoken)
            vcsm.trigger_continue_workflow(remind_host)
        else:
            sfnexecid = "vc-session-" + str(uuid.uuid4())
            facerec['SessionId'] = sfnexecid
            vcsm.start_workflow_execution(sfnexecid,facerec)

    except Exception as e:
        print(e)
        print("Exception error while checking for payloads")
        raise e

def process_blankpayload(facerec):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.process_blankpayload.trigger={}'.format(json.dumps(facerec)))
        sfnexecid = "blank-vc-session-" + str(uuid.uuid4())
        vcsm.start_workflow_execution(sfnexecid,facerec)

    except Exception as e:
        print(e)
        print("Exception error while checking for payloads")
        raise e

def lambda_handler(event, context):
    
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.trigger={}'.format(json.dumps(event)))
        
        for rec in event['Records']:
            if rec['EventSource'] == "aws:sns":
                facerec = rec['Sns']['Message']
                
                payload = json.loads(facerec)
                
                if 'Visitor' in payload:
                    if payload['Visitor'] != None:
                        process_payload(json.loads(facerec))
                    else:
                        process_blankpayload(json.loads(facerec))
        result = facerec
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Exception error registering session")
        raise e
