import json
import boto3
import os
import time
import base64
import zlib
import os
from boto3.dynamodb.conditions import Key, Attr
import logging
import smtoolkit as vcsm
import base64


# # Set logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    try:
        result = {}
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + 'get_activitiy_token.trigger={}'.format(json.dumps(event)))
        
        if 'HostResponse' in event:
            print('Host Response detected')
            t = event['HostResponse']['ActivityToken']
            res = event['HostResponse']['Response']
            token = t.replace(" ","+")
            
            if res == 'now_response' or res == 'soon_response':
                resjson = { 'SumerianMessageType' : 'NotifyGuest' , 'HostResponse' : res }
                vcsm.send_activitiy_success(token,resjson)
            if res == 'arrived' or res == 'cancelled':
                resjson = { 'SumerianMessageType' : 'HostArrived' , 'HostResponse' : res }
                vcsm.send_activitiy_success(token,resjson)
            if res == 'remind_host' :
                resjson = { 'SumerianMessageType' : 'RemindHost' , 'HostResponse' : res }
                vcsm.send_activitiy_success(token,resjson)

            vcsm.respond(None,"Thank You for your respond, we will notify guest")
        
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + 'get_activitiy_token.result={}'.format(json.dumps(result)))
        return event
    except Exception as e:
        print(e)
        print("Error Managing Session")
        raise e


        # session_throttle_milsec = os.environ['session_throttle_milsec']
        # msg = {}
        # print(json.dumps(event))
        # #Check if this the end of Session.
        # if 'Complete' in event:
        #     if event['Complete'] == True:
        #         delete_session(event['Faces'][0]['RekognitionId'],'virtual-concierge-session')
        #     msg = event
        
        # #Check if this session is from SNS
        # if 'Records'in event:
        #     msgstr = get_message(event)
        #     msgx = msgstr
        #     if 'DeepLens' in msgx:
        #         msg = msgx['DeepLens']
        #         if 'Faces' in msg:
        #             f = msg['Faces']
        #             if len(f) > 0:

        #                     #######################################
        #                     # CHECK IF SESSION IS ALREADY RUNNING.
        #                     #######################################
        #                     x = get_session(msg['Faces'][0]['RekognitionId'],'virtual-concierge-session')
        #                     print(x)
        #                     if 'Item' in x:

        #                         #Check if Session timeout.
        #                         lastexttime = x['Item']['LastActiveAt']
        #                         nextextime = int(lastexttime) + int(session_throttle_milsec)
        #                         currenttime = int(round(time.time() * 1000))
        #                         exptime =  x['Item']['ExpireAt']
                                
        #                         #Expiry Hack take procedure out of function
        #                         if currenttime < int(exptime):
        #                             print(currenttime)
        #                             if currenttime > nextextime:
        #                                 #Session already exist, remind Host that guest is waiting.
        #                                 print("SessionExist Sending Friendly Reminder to Host")
        #                                 update_status(
        #                                     msg['Faces'][0]['RekognitionId'],
        #                                     'remindhost',
        #                                     'virtual-concierge-session'
        #                                 )
        #                                 update_lastactiveat(msg['Faces'][0]['RekognitionId'], currenttime ,'virtual-concierge-session')
        #                             else:
        #                                 print("throttled")
        #                         else:
        #                             print("Session has expired, this is a hack for demo purpose, please delete record to proceed")
                           
        #                     else:
        #                         #########################################
        #                         # CHECK DETECTED FACE IS A HOST ATTENDING
        #                         #########################################
        #                         y = get_hostid_session(msg['Faces'][0]['RekognitionId'],'virtual-concierge-session')
        #                         print(y)
        #                         if len(y['Items']) > 0:
        #                             print(y['Items'])
        #                             for i in y['Items']:
        #                                 update_status(
        #                                     i['RekognitionId'],
        #                                     'hostdetected',
        #                                     'virtual-concierge-session'
        #                                 )
        #                             face = json.dumps(msg['Faces'])
        #                             xtime = int(round(time.time() * 1000))
        #                             update_expireat(y['Items'][0]['RekognitionId'], xtime ,'virtual-concierge-session')
        #                             update_lastactiveat(y['Items'][0]['RekognitionId'], xtime,'virtual-concierge-session')
        #                             update_hostface(y['Items'][0]['RekognitionId'],face,'virtual-concierge-session')
        #                         else:
        #                             #Session doesn't exist, create guest.
        #                             print("Creating Session & Executing StepFunction")
        #                             execarn = execute_sfn(json.dumps(msg))
        #                             create_session(
        #                                 {
        #                                     'SfnExecArn': execarn ,
        #                                     'RekognitionId': msg['Faces'][0]['RekognitionId'],
        #                                     'TTL': 60 ,
        #                                     'HostResponse': 'waiting'
        #                                 },
        #                                 'virtual-concierge-session'
        #                                 )
        #                             msg['SfnExecArn'] = execarn
        #                             xtime = int(round(time.time() * 1000))
        #                             exptime = xtime+(86400*1000)
        #                             update_lastactiveat(msg['Faces'][0]['RekognitionId'], xtime,'virtual-concierge-session')
        #                             update_expireat(msg['Faces'][0]['RekognitionId'], exptime ,'virtual-concierge-session')
        #                             update_createat(msg['Faces'][0]['RekognitionId'], xtime ,'virtual-concierge-session')
                                
        #             else:
        #                 execarn = execute_sfn(json.dumps(msg))
        #                 msg['SfnExecArn'] = execarn
        #                 return("No Face Detected")
        #     if 'SlackResponse' in msgx:
        #         msg = msgx['SlackResponse']
        #         update_status(
        #             msg['RekognitionId'],
        #             msg['HostResponse'],
        #             'virtual-concierge-session'
        #             )
        #         msg = respond(None,"Thank You! I will notify guest")
        # return(msg)


# def get_message(event):
#     try:
#         records = event['Records']
#         for rec in records:
#             msgstr = rec['Sns']['Message']
#         return(json.loads(msgstr))
#     except Exception as e:
#         print(e)
#         print('Error Capturing Message from topic')
        
# def execute_sfn(msgstr):
#     try:
#         msg = json.loads(msgstr)
#         executionid = msg['ThingName'] + '-' + str(int(round(time.time() * 1000)))
#         execution = sfn_client.start_execution(stateMachineArn=os.environ['session_sfn'],name=executionid,input=msgstr)
#         return(execution['executionArn'])
#     except Exception as e:
#         print(e)
#         print('Error Sending message to StepFunction')

# def delete_session(rekid,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.delete_item(Key={'RekognitionId': rekid})

# def update_status(rekid,status,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.update_item(Key={'RekognitionId': rekid},UpdateExpression='SET HostResponse = :val1',ExpressionAttributeValues={':val1': status})

# def update_lastactiveat(rekid,status,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.update_item(Key={'RekognitionId': rekid},UpdateExpression='SET LastActiveAt = :val1',ExpressionAttributeValues={':val1': status})

# def update_expireat(rekid,status,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.update_item(Key={'RekognitionId': rekid},UpdateExpression='SET ExpireAt = :val1',ExpressionAttributeValues={':val1': status})

# def update_createat(rekid,status,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.update_item(Key={'RekognitionId': rekid},UpdateExpression='SET CreatedAt = :val1',ExpressionAttributeValues={':val1': status})

# def update_hostface(rekid,payload,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.update_item(Key={'RekognitionId': rekid},UpdateExpression='SET HostFacePayload = :val1',ExpressionAttributeValues={':val1': payload})


# def create_session(item,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.put_item(Item=item)

# def get_session(rekid,tablename):
#     ddbtable = dynamodb.Table(tablename)
#     return ddbtable.get_item(Key={'RekognitionId': rekid})

# def get_hostid_session(hostid,tablename):
#     ddbtable = dynamodb.Table('virtual-concierge-session')
#     response = ddbtable.query(
#         IndexName='AppointmentHost-RekognitionId-Index',
#         KeyConditionExpression=Key('AppointmentHost').eq(hostid) 
#     )
#     return  response
