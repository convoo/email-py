#!/usr/bin/python
# coding: utf-8

# using SendGrid - https://github.com/sendgrid/sendgrid-python
# using Pyrebase - https://github.com/thisbejim/Pyrebase

# [START app]
import time, logging, configparser
import threading
import pyrebase
import sendgrid
from flask import Flask, jsonify, render_template, request, redirect, url_for
from sendgrid.helpers.mail import *


# environment variables 
config = configparser.ConfigParser()
config.read('.env')

app = Flask(__name__, template_folder='views', static_folder='public')

# firebase config
firebaseConfig = {
    "apiKey": config['FIREBASE']['KEY'],
    "authDomain": "convoofire.firebaseapp.com",
    "databaseURL": "https://convoofire.firebaseio.com",
    "storageBucket": "convoofire.appspot.com",
}
# Get a reference to the auth service
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password(config["FIREBASE"]["EMAIL"], config["FIREBASE"]["PASSWORD"])
db = firebase.database()
token = user['idToken']


# Fired when an email is added to the queue
def stream_handler(post):
    if post["data"]:    
        if 'toEmail' in post['data']:
            checkEmail(post["path"], post["data"])
        else:
            for i in post["data"]:
                checkEmail(i, post["data"][i])



# watch the queue 
def startStream (): 
    db.child("email/logs").push({"status":"starting", "time": int(time.time())})
    threading.Timer(int(config['TIMER']['INTERVAL']), startStream).start ()
    db.child("email/logs").push({"status":"starting stream", "time": int(time.time())})
    my_stream = db.child("email/queue/").stream(stream_handler, token)
    db.child("email/logs").push({"status":"closing stream", "time": int(time.time())})
    my_stream.close()
    db.child("email/logs").push({"status":"starting stream", "time": int(time.time())})
    my_stream = db.child("email/queue/").stream(stream_handler, token)
startStream()


# prepare email -- Maybe we should check of the toEmail and the Subject are the same when preventing emails??
def checkEmail(path, data):
    sendToEmail = (data['toEmail'])
    timeBefore = int(time.time()) - 84946 #24 hours ago
    timeNow = int(time.time())
    sentToday = db.child("email/sent").order_by_child("time").start_at(timeBefore).end_at(timeNow).get(token)
    todaysRecipients = list(set([i.val()['toEmail'] for i in sentToday.each()]))
    if config['SENDGRID']['DUPLICATES'].lower() == 'false':
        if sendToEmail not in todaysRecipients:
            sendEmail(data)
        else:
            print('We Sent this person an email today already!')
    else:
        sendEmail(data)
    db.child("email/sent").push(data, token)
    db.child("email/queue").child(path).remove(token)

# send email 
def sendEmail(data):
    #data['fromEmail'], data['subject'], data['toEmail'], data['contentType'], data['mailContent']
    if data['fromEmail'] and data['subject'] and data['toEmail'] and data['contentType'] and data['mailContent']:
        sg = sendgrid.SendGridAPIClient(apikey=config['SENDGRID']['KEY'])
        from_email = Email(data['fromEmail'])
        to_email = Email(data['toEmail'])
        content = Content(data['contentType'], data['mailContent'])
        mail = Mail(from_email, data['subject'], to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
    else:
        db.child("email/sent").push(data, token)

# place an email in the queue for testng 
@app.route('/test')
def test(): 
    db.child("email/queue").push({"fromEmail":"teamconvoo@gmail.com","subject":"You are officially on the Beta List!", "toEmail":"email.will.in.china@gmail.com", "contentType":"text/plain", "mailContent":"Woohoo!", "time": int(time.time())})
    return jsonify({'message': "We sent a test email!"})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        url = request.form['url']
        username = request.form['username']
        password = request.form['password']
        apiKey = request.form['apiKey']
        adminUsername = request.form['adminUsername']
        adminPassword = request.form['adminPassword']
        print(url)
        return redirect(url_for('pay'))
    else:
        return render_template('register.html')

@app.route('/pay')
def pay():
    return render_template('pay.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# handle errors
@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return jsonify({'message':'An internal error occurred.','status': 500})

# run the app --- debug true results in the stream being triggered twice!
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)

# [END app]