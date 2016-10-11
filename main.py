#!/usr/bin/python
# coding: utf-8

# using SendGrid - https://github.com/sendgrid/sendgrid-python
# using Pyrebase - https://github.com/thisbejim/Pyrebase

# [START app]
import time, logging, configparser
import pyrebase
import sendgrid
from flask import Flask, jsonify, render_template, request, redirect, url_for
from utils import test
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
    "serviceAccount": "convoofire.json" # We should change this to login by email 
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# Fired when an email is added to the queue
def stream_handler(post):
    if post["data"]:    
        dataSize = (len(post["data"]))
        if dataSize == 6: # this number represents the number of keys in the json its nasty but it works
        # if the queue stops for any reason and emails back up we still need to go through the ones we havent sent
            checkEmail(post["path"], post["data"])
        else:
            for i in post["data"]:
                checkEmail(i, post["data"][i])

# watch the queue 
my_stream = db.child("email/queue/").stream(stream_handler)

# prepare email
def checkEmail(path, data):
    sendToEmail = (data['toEmail'])
    timeBefore = int(time.time()) - 84946 #24 hours ago
    timeNow = int(time.time())
    sentToday = db.child("email/sent").order_by_child("time").start_at(timeBefore).end_at(timeNow).get()
    todaysRecipients = []
    for i in sentToday.each():
        if i.val()['toEmail'] not in todaysRecipients:
            todaysRecipients.append(i.val()['toEmail'])
    if sendToEmail not in todaysRecipients:
        sendEmail(data['fromEmail'], data['subject'], data['toEmail'], data['contentType'], data['mailContent'])
    else:
        print('We Sent this person an email today already!')
    db.child("email/sent").push(data)
    db.child("email/queue").child(path).remove()

# send email 
def sendEmail(fromEmail, subject, toEmail, contentType, mailContent):
    if fromEmail and subject and toEmail and contentType and mailContent:
        print('SENDING')
        # sg = sendgrid.SendGridAPIClient(apikey=config['SENDGRID']['KEY'])
        # from_email = Email(fromEmail)
        # to_email = Email(toEmail)
        # content = Content(contentType, mailContent)
        # mail = Mail(from_email, subject, to_email, content)
        # response = sg.client.mail.send.post(request_body=mail.get())

# place an email in the queue for testng 
@app.route('/test')
def test(): 
    db.child("email/queue").push({"fromEmail":"teamconvoo@gmail.com","subject":"You are officially on the Beta List!", "toEmail":"email3.will.in.china@gmail.com", "contentType":"text/plain", "mailContent":"Woohoo!", "time": int(time.time())})
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