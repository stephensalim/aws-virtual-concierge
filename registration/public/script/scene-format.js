class SceneFormat {

  // Constructor to intialize with skin
  constructor(settings) {
    this.settings = settings;
  }

  speakSsml(props) {
    var ssml = new Speak(this.settings.theme, props)[props["MessageType"]]()
    return `<speak>${ssml}</speak>`;
  }

  screenHtml(props) {
    if (props) {
      // Clear timeout before writing to screen
      this.clearTimeout();

      var visitor = props["Name"];
      var message = new Speak(this.settings.theme, props)[props["MessageType"]]()
      // Add orientation to rotate photo if required
      return `<div id="photo">
    <img class="photo ${props.OrientationCorrection}" src="${props.PhotoUrl}"></img>
  </div>
  <div id="message">
    <div class="visitor"><strong>Name:</strong> ${visitor}</div>
    <div class="message"><strong>Message:</strong> ${message}</div>
  </div>`;
    } else {
      // Return a QR code for the scan to pop up the registration page
      return `<div class="qrcode"/>`;
    }
  }

  camHtml() {
    var camUrl = "https://dummyimage.com/1280x629/000000/0011ff&text=AWS+Deep+Lens"
    if (this.settings.ip) {
      camUrl = `https://${this.settings.ip}:4000/video_feed_proj`;
    }
    // TODO: Consider if we need to include link for css as part of html
    return `<img class="cam" src="${camUrl}"></img>`
  }

  logoHtml() {
    // Use CSS to redner the logo div with image etc
    var baseUrl = this.settings.baseUrl || "https://s3.amazonaws.com/virtual-concierge-amplify-us-east-1/"
    return `<link href="${baseUrl}css/scene-style.css" type="text/css" rel="stylesheet">
<div class="logo"/>`
  }

  done(element) {
    // Set timeout so that in 60 seconds
    var screenHtml = this.screenHtml()
    var restore = function(element, html) {
      element.innerHTML = html
      console.log('restored', element)
    }
    var duration = 60*1000;
    console.log('set timeout', duration)
    self.doneTimeout = setTimeout(function() { restore(element, screenHtml); }, duration);
  }

  clearTimeout() {
    if (this.doneTimeout) {
      console.log('clear timeout')
      self.clearTimeout(this.doneTimeout);
    }
  }

}

class Speak {

  // Constructor to intialize with properties
  constructor(theme, props) {
    this.theme = theme;
    this.props = props;
  }

  organisation() {
    // Use the theme for organisation if not default
    switch (this.theme) {
      case "default":
      case "light":
      case "dark": return "Amazon Web Services";
      default: return this.theme;
    }
  }

  firstName(name) {
    return name.split(' ')[0]
  }

  timeSince(fromSeconds, toSeconds) {
    var seconds = Math.floor((toSeconds || Date.now()/1000) - fromSeconds);
    return this.formatSeconds(seconds)
  }

  formatSeconds(seconds) {
    var interval = Math.floor(seconds / 86400);
    if (interval > 1) {
      return interval + " days";
    }
    interval = Math.floor(seconds / 3600);
    if (interval > 1) {
      return interval + " hours";
    }
    interval = Math.floor(seconds / 60);
    if (interval > 1) {
      return interval + " minutes";
    }
    return Math.floor(seconds) + " seconds";
  }

  guestWelcome() {
    return `Hello <mark name='gesture:wave'/> ${this.firstName(this.props.Name)}! <mark name='gesture:big'/> ` +
           `Welcome to ${this.organisation()}, <mark name='gesture:generic_b'/> let me check if you have any appointment.`
  }

  guestUnknown() {
    return `Sorry,<mark name='gesture:defense'/> I cannot detect who <mark name='gesture:you'/> you are. ` +
           `<mark name='gesture:generic_b'/> let me send a message to the group to attend to you.`
  }

  appointmentFound() {
    return `Alright, I have found your appointment with <mark name='gesture:generic_c'/> ${this.firstName(this.props.Host)}. `+
           `<mark name='gesture:generic_a'/> Please take a seat, while I notify your arrival.`
  }

  appointmentNotFound() {
    return `Sorry,<mark name='gesture:defense'/> unfortunately you do not have an appointment with anyone, ` +
           `<mark name='gesture:generic_a'/> our visiting policy is by appointment only, please make a booking and come again.`
  }

  hostWaiting() {
    return `Hi ${this.firstName(this.props.Name)}, unfortunately your host has not responded yet. Let me send a reminder.`
  }

  hostArriving() {
    if (this.props.HostArrivingIn) {
      var when = this.formatSeconds(this.props.HostArrivingIn)
      return `Hi ${this.firstName(this.props.Name)}! Your host is coming out to get you in ${when}.`
    }
    return `Hi ${this.firstName(this.props.Name)}! Your host is coming out to get you now.`
  }

  hostArrived() {
    var since = 'a while';
    if (this.props.VisitorArrivedAt && this.props.HostArrivedAt) {
      since = this.timeSince(this.props.VisitorArrivedAt, this.props.HostArrivedAt);
    }
    return `Hi ${this.firstName(this.props.Host)}! Good to see you have finally come out. Your guest has been waiting for ${since} !`
  }

}
