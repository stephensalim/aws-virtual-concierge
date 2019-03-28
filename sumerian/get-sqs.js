'use strict';


function getSQSMessage(params,ctx,thingname,callback){
	 	var sqs = new AWS.SQS();
		sqs.receiveMessage(params, function(err, data) {
			var rtn = {};
			if (err) {console.log(err, err.stack); }
			else
			{
				var payload = JSON.stringify(data);
				//console.log(payload);
				var jsonmsg = data.Messages;
				//console.log(jsonmsg.length);
				if ( jsonmsg === undefined || jsonmsg.length == 0) {
					//console.log("no message");
				}
				else
				{
					var attributes = jsonmsg[0]['Attributes'];
					if (attributes['MessageGroupId'] === thingname){

					var message = jsonmsg[0]['Body']
					var receipthandle = jsonmsg[0]['ReceiptHandle']
					var messageid = jsonmsg[0]['MessageId']
					rtn['Message'] = message;
					rtn['ReceiptHandle'] = receipthandle;
					rtn['MessageId'] = messageid;

					}

				}

			callback(rtn);
			}

		});

}


function delSQSMessage(delparams,ctx,callback){
	 	var sqs = new AWS.SQS();
		sqs.deleteMessage(delparams, function(err, data) {
			var rtn = {};
			if (err) {console.log(err, err.stack);}
			else {callback(data);}
		});

}

function isEmpty(obj) {return Object.keys(obj).length === 0;}

function enter(args, ctx) {
		var sqsurl = 'https://sqs.us-west-2.amazonaws.com/882607831196/SumerianMessageQueue.fifo';
		var thingname = 'deeplens_zz8BbGbNSVuHCsyqtWOM4Q';
	 	var params = {QueueUrl: sqsurl, MaxNumberOfMessages:1,WaitTimeSeconds:20,AttributeNames:['MessageGroupId']};
		getSQSMessage(params,ctx,thingname,(msg) => {
			//console.log(msg);
			if (isEmpty(msg)){ctx.transitions.failure();}
			else
			{
				console.log(msg);
				console.log("message received");
				ctx.behaviorData.Message = msg.Message;
				var delparams = {QueueUrl: params.QueueUrl, ReceiptHandle: msg.ReceiptHandle};
				//console.log(delparams);
				delSQSMessage(delparams,ctx,(delmsg) => {console.log("message deleted");});
				ctx.transitions.success();
			}
		});
}

var parameters = [];

function exit(args, ctx) {
}
