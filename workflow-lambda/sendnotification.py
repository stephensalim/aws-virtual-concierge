import json
import os
import time
import logging
import smtoolkit as vcsm

# Set logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.trigger={}'.format(json.dumps(event)))
        
        ### Message Payload
        newevent = {}
        newevent.update(event['PreviousStateOutput'])
        event.pop('PreviousStateOutput', None)
        newevent.update(event)
        event = newevent
        result = {}
        
        # Clean up Payload related to previous token
        if 'HostNotification' in event:
            event.pop('HostNotification', None)
        
        if event['Activity'] == 'HostResponse':
            time.sleep(5)
            token = vcsm.get_activitiy_token(os.environ['ActivityHostResponseArn'])
            result['HostNotification'] = {}
            now_response = os.environ['ResponseUrl'] + "?"+ vcsm.generate_params('now_response',token)
            soon_response = os.environ['ResponseUrl'] + "?"+ vcsm.generate_params('soon_response',token)
            result['HostNotification']['Token'] = token
            result['HostNotification']['ResponseOption'] = {}
            result['HostNotification']['ResponseOption']['now_response'] = now_response
            result['HostNotification']['ResponseOption']['soon_response'] = soon_response

            ################
            # FORM EMAIL MESSAGE
            ################
            msg = """ 
            ===============================================
            You have a guest !
            Please click on one of the response link below.
            ===============================================
            Coming out now = {}
            Coming out soon = {}
            """.format(now_response,soon_response)
            
            ################
            # SEND JSON MESSAGE
            ################
            # msg = event['Visitor']
            # msg['HostNotification'] = {}
            # msg['HostNotification']['ResponseOption'] = {}
            # msg['HostNotification']['ResponseOption']['now_response'] = now_response
            # msg['HostNotification']['ResponseOption']['soon_response'] = soon_response
            
            vcsm.update_session(event['Visitor']['FaceId'],'HostNotificationToken',token,os.environ['SessionTable'])
            vcsm.send_sns(msg,os.environ['SNSTopic'])

        
        event.pop('Activity', None)
        result.update(event)
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Error while sending SNS")
        raise e
