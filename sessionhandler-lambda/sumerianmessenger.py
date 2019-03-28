import json
import os
import logging
import smtoolkit as vcsm

# Set logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sqs_queue = os.environ['QueueUrl']


def lambda_handler(event, context):
    try:
            logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.sumerianhostmessager.trigger={}'.format(json.dumps(event)))

            if type(event) == list:
                flattenvent = {}
                flattenvent['PreviousStateOutput'] = vcsm.flatten_jsonlist(event)
                flattenvent['SumerianMessageType'] = flattenvent['PreviousStateOutput']['SumerianMessageType']
                flattenvent['PreviousStateOutput'].pop('SumerianMessageType', None)
                event = flattenvent
            
            result = {}
            result = event
            #result['SumerianHost'] = {}
            previousoutput = result['PreviousStateOutput']
            visitorface = {}
            
            if previousoutput['Visitor'] != None:
                visitorface = previousoutput['Visitor']
                fullname = visitorface['Name']
            
            speech = ""
            hostfullname = ""
            
            
            
            if event['SumerianMessageType'] == "UnknownGuest":
                speech = "Hello there ! <mark name='gesture:wave'/> It looks like this is the first time you are here ! <mark name='gesture:generic_a'/> Please go ahead and register and appointment ! <mark name='gesture:generic_b'/>"
                mode = 'unknown'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            
            if event['SumerianMessageType'] == "NoAppointment":
                speech = vcsm.get_name(fullname,'first') + " ! It looks like you don't have any appointment registered. <mark name='gesture:generic_a'/> Please go ahead and register and appointment ! <mark name='gesture:generic_b'/>"
                mode = 'unknown'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            
            
            if event['SumerianMessageType'] == "GreetGuest":
                speech = "Hello <mark name='gesture:wave'/> " +  vcsm.get_name(fullname,'first') + " ! <mark name='gesture:big'/> Welcome to Sydney Summit front desk, <mark name='gesture:generic_b'/> let me check if you have any appointment."
                mode = 'greeting'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            
            if event['SumerianMessageType'] == "RemindHost":
                speech = "Hi " +  vcsm.get_name(fullname,'first') + " ! <mark name='gesture:small'/> Sorry to keep you waiting ! It looks like your host has not responded yet. Let me send a reminder of your arrival !"
                mode = 'remindhost'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
            
                
            if event['SumerianMessageType'] == "NotifyHost":
                if 'Appointment' in previousoutput:
                    hostfullname = vcsm.find_employee_name(previousoutput['Appointment']['EmployeeId'])
                speech = "Alright, I have found your appointment with  <mark name='gesture:generic_c'/> " + hostfullname + ". <mark name='gesture:generic_a'/> Please take a seat, while I notify your arrival."
                mode = 'notify'
                visitorface['Appointment'] = {}
                visitorface['Appointment']['HostName'] = hostfullname
                visitorface['Appointment']['RoomName'] = previousoutput['Appointment']['Room']
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            
            if event['SumerianMessageType'] == "NotifyGuest":
                if 'HostResponse' in previousoutput:
                    if previousoutput['HostResponse'] == 'now_response':
                        speech = fullname + "! your host is coming out to get you now."
                    if previousoutput['HostResponse'] == 'soon_response':
                        speech = fullname + "! your host is coming out to get you in a couple of minutes."
                mode = 'notify'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            
            if event['SumerianMessageType'] == "HostArrived":
                if 'HostResponse' in previousoutput:
                    if 'Appointment' in previousoutput:
                        hostfullname = vcsm.find_employee_name(previousoutput['Appointment']['EmployeeId'])
                        roomname = previousoutput['Appointment']['Room']
                    if previousoutput['HostResponse'] == 'arrived':
                        speech =  vcsm.get_name(hostfullname,'first') + "! Thank you for finally coming out. Your meeting is in room " + roomname + ". Have a nice day !!" 
                    if previousoutput['HostResponse'] == 'cancelled':
                        speech = "No worries " +  vcsm.get_name(hostfullname,'first') + "! I'll cancel the meeting and free up the room. Have a great day !"
                mode = 'arrive'
                sendmsgrespone = vcsm.send_sumerian_message(visitorface,mode,speech,sqs_queue)
                result = previousoutput
                #result['SumerianHost'] = sendmsgrespone
            logger.debug('event.'+ os.environ['AWS_LAMBDA_FUNCTION_NAME'] + '.sumerianhostmessager.result={}'.format(json.dumps(result)))
            return(result)
        
    except Exception as e:
        print(e)
        print("Exception error while sending message to sumerian")
        raise e