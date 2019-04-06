import json
import boto3
import os
import time
import logging
import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import uuid
from urllib import request

# Set logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sfnclient = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
sqsclient = boto3.client('sqs')
snsclient = boto3.client('sns')
sfnclient = boto3.client('stepfunctions')

def start_workflow_execution(sfnexecid,sfrnarn,event):
    try:
        response = sfnclient.start_execution(
            stateMachineArn=sfrnarn,
            name= sfnexecid,
            input= json.dumps(event)
        )
    except Exception as e:
        print(e)
        print("Exception error while triggering continue workflow")
        raise e
        
def trigger_continue_workflow(url):
    try:
        req =  request.Request(url)
        resp = request.urlopen(req)
        result = resp
        return result
    except Exception as e:
        print(e)
        print("Exception error while triggering continue workflow")
        raise e
        
        
        
def find_session(visitorid,tablename):
    try:
        ddbtable = dynamodb.Table(tablename)
        return ddbtable.get_item(Key={'VisitorId': visitorid}, AttributesToGet = [ 'SessionId','HostNotificationToken','HostArrivalToken' ] )
    except Exception as e:
        print(e)
        print("Exception error while updating session")
        raise e

def update_session(visitorid,attribute,value,tablename):
    try:
        ddbtable = dynamodb.Table(tablename)
        timestamp = Decimal(datetime.datetime.now().timestamp())
        return ddbtable.update_item(Key={'VisitorId': visitorid},UpdateExpression='SET '+ attribute +' = :val1, UpdateAt = :val2', ExpressionAttributeValues={':val1': value , ':val2': timestamp })
    except Exception as e:
        print(e)
        print("Exception error while updating session")
        raise e
        
def create_session(visitorid,sessionid,tablename):
    try:
        ddbtable = dynamodb.Table(tablename)
        timestamp = Decimal(datetime.datetime.now().timestamp())
        return ddbtable.put_item(Item={'VisitorId': visitorid, 'SessionId' : sessionid ,'StartAt' : timestamp, 'UpdateAt' : timestamp , 'HostNotificationToken' : "empty" , 'HostArrivalToken' : "empty" })
    except Exception as e:
        print(e)
        print("Exception error while creating session")
        raise e

def deletesession_session(visitorid,tablename):
    try:
        ddbtable = dynamodb.Table(tablename)
        timestamp = Decimal(datetime.datetime.now().timestamp())
        return ddbtable.delete_item(Key={'VisitorId': visitorid})
    except Exception as e:
        print(e)
        print("Exception error while deleting session")
        raise e
  
def find_employee_name(employeeid):
    try:
        employeetable = dynamodb.Table(os.environ['employeetable'])
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.find_employee_name.trigger={}'.format(json.dumps(employeeid)))
        getitemresponse = employeetable.get_item(Key={'EmployeeId': str(employeeid)})
        result = getitemresponse['Item']['Name']
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.find_nearst_scheduled_appointment.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while finding employee name")
        raise e

def get_name(fullname,mode):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.get_name.trigger={}'.format(json.dumps(fullname+","+mode)))     
        name = fullname.split(" ")
        if mode == 'first':
            result = name[0]
        if mode == 'last': 
            result = name[1]
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.get_name.result={}'.format(json.dumps(fullname+","+mode)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while getting first / last name")
        raise e

def send_sumerian_message(visitorface,mode,speech,sqs_queue):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_sumerian_message.trigger.mode={}.speech={}.sqs_queue={}'.format(mode,speech,sqs_queue))     
        result = {}
        sumerianpayload = {}
        sumerianpayload['VisitorFace'] = visitorface
        sumerianpayload['MsgType'] = mode
        sumerianpayload['Message'] = speech
        sqs_resp = sqsclient.send_message( 
                        QueueUrl=sqs_queue ,
                        MessageBody=json.dumps(sumerianpayload), 
                        MessageGroupId='SumerianHostMessage', 
                        MessageDeduplicationId= str(uuid.uuid4())
                        )
        result = sumerianpayload
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_sumerian_message.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while sending message to queue")
        raise e

def flatten_faces(Faces):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.flatten_faces.trigger={}'.format(json.dumps(Faces)))
        
        if len(Faces) > 0:
            print('multiple faces detected flattening Faces')
            result = Faces[0]
        else:
            result = Faces[0]
            
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.flatten_faces.result={}'.format(json.dumps(Faces)))
        return result
    except Exception as e:
        print(e)
        print("Exception error while flattening Faces")
        raise e

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else res,
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def find_nearest_date(items, pivot):
    try:
        result = items.index(min(items, key=lambda x: abs(x - Decimal(pivot))))
        return result
    except Exception as e:
        print(e)
        print("Exception finding nearst date")
        raise e

# def find_nearst_scheduled_appointment(guestid,appointmenttable):
#     try:
#         logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.find_nearst_scheduled_appointment.trigger={}'.format(json.dumps(guestid)))
#         getitemresponse = appointmenttable.get_item(Key={'GuestId': str(guestid)}, AttributesToGet=['Appointments'])
#         if 'Item' in getitemresponse:
#             appointments = getitemresponse['Item']['Appointments']
#             datearray = []
#             for dateval in appointments:
#                 datearray.append(Decimal(dateval['DateTime']))
#             index = find_nearest_date(datearray,datetime.datetime.now().timestamp())
#             result = appointments[index]
#         else:
#             result = None
#         logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.find_nearst_scheduled_appointment.result={}'.format(json.dumps(result)))
#         return result
#     except Exception as e:
#         print(e)
#         print("Exception error while finding nearst appointments appointments")
#         raise e

def send_activitiy_success(token,res):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_activitiy_success.trigger={}'.format(token))
        response = sfnclient.send_task_success(
            taskToken=token,
            output=json.dumps(res)
            )
        result = response
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_activitiy_success.trigger={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Error while sending activity success")
        raise e

def flatten_jsonlist(jsonlist):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.flatten_jsonlist.trigger={}'.format(jsonlist))
        result = {}
        for i in jsonlist:
            result.update(i)
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.flatten_jsonlist.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Error while getting activity token")
        raise e


def get_activitiy_token(activityarn):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.get_activitiy_token.trigger={}'.format(json.dumps(activityarn)))
        response = sfnclient.get_activity_task(activityArn=activityarn)
        result = response['taskToken']
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.get_activitiy_token.trigger={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Error while getting activity token")
        raise e
        
def send_sns(message,snstopicarn):
    try:
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_sns.trigger={}'.format(json.dumps(message)))
        response = snsclient.publish(TargetArn=snstopicarn,Message= message)
        result = response
        logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.send_sns.result={}'.format(json.dumps(result)))
        return result
    except Exception as e:
        print(e)
        print("Error while sending SNS Notification")
        raise e

def generate_params(message,token):
    tokenparam = "&token=" + token
    messageparam = "&state=" + message
    response = tokenparam + messageparam   
    return response
