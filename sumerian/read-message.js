'use strict';

function playSpeech(body, type, voice, ctx) {

    const speech = new sumerian.Speech();
    ctx.entityData.host.getComponent('SpeechComponent').addSpeech(speech);
    speech.updateConfig({
        entity: ctx.entityData.host,
        body: body,
        type: type,
        voice: voice
    });
    return speech;
}

function writeInfo(msgjson,message, ctx) {
    const userdetails = '<strong>Name   : </strong>' + msgjson.UserDetail.Name + '</br></br>'
	const userstatus  = '<strong>Message: </strong> </br>' + String(msgjson.SumerianHost.Message) + '</br>'
    const userphoto = '<img src=' + msgjson.UserDetail.PhotoUrl + ' width="344" height="463">'
    var spanElementbody = document.getElementById('message_box_body');
    var spanElementphoto = document.getElementById('message_box_photo');
	var spanElementstatus = document.getElementById('message_box_status');
    spanElementbody.innerHTML = userdetails;
    spanElementphoto.innerHTML = userphoto;
	spanElementstatus.innerHTML = userstatus;
	console.log(String(msgjson.SumerianHost.Message))
    ctx.entityData.InformationBox = ctx.world.getManager('EntityManager').getEntityByName('InformationBox');
    ctx.entityData.InformationBox.show();
}


function enter(args, ctx) {
    ctx.entityData.host = ctx.world.getManager('EntityManager').getEntityByName('Cristine');
    var mesg = ctx.behaviorData.Message;
    var msgjson = JSON.parse(mesg);
    var message = msgjson.SumerianHost.Message;
    var msgtype = msgjson.SumerianHost.MsgType;

    var body = '<speak>' + message + '</speak>';
    if (msgtype === 'greeting') {writeInfo(msgjson,"Hello..", ctx);}
    if (msgtype === 'reject') {console.log("No Booking");}
    if (msgtype === 'checkagain') {console.log("unable to see face");}
    if (msgtype === 'notify') {writeInfo(msgjson,"Appointment Found.. notifying host.", ctx);}
    if (msgtype === 'comingoutsoon') {writeInfo(msgjson,"Host will be with your soon.", ctx);}
    if (msgtype === 'comingout') {writeInfo(msgjson,"Host is coming out to get you.", ctx);}
	if (msgtype === 'assureguest') {writeInfo(msgjson,"Sending Reminder to host.", ctx);}
    var speech = playSpeech(body, 'ssml', 'Amy', ctx);
    speech.play()
        .then(() => {
            console.log("Summerian Host have said the welcome line, ready to record");
            ctx.behaviorData.UserDetails = msgjson
            ctx.transitions.success();
        });

}


function fixedUpdate(args, ctx) {}


function update(args, ctx) {}


function lateUpdate(args, ctx) {}

function exit(args, ctx) {}


function cleanup(args, ctx) {}


var parameters = [];
