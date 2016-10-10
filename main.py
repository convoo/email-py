#!/usr/bin/python
# coding: utf-8

# using SendGrid - https://github.com/sendgrid/sendgrid-python
# using Pyrebase - https://github.com/thisbejim/Pyrebase

# [START app]
import time, logging, configparser 
import pyrebase
import sendgrid
from flask import Flask, jsonify, render_template
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
            prepareEmail(post["path"], post["data"])
        else:
            for i in post["data"]:
                prepareEmail(i, post["data"][i])

# watch the queue 
my_stream = db.child("email/queue/").stream(stream_handler)

# prepare email
def prepareEmail(path, data):
    print(data['fromEmail'])
    db.child("email/sent").push(data)
    db.child("email/queue").child(path).remove()
    timeNow = int(time.time())
    timeBefore = int(time.time()) - 84946 #24 hours ago
    # Have we sent this gut an email before?
    #sentToday = db.child("email/sent").order_by_child("time").start_at(timeNow).end_at(timeBefore).get()
    #print(sentToday)
    sendEmail(data['fromEmail'], data['subject'], data['toEmail'], data['contentType'], data['mailContent'])

# send email 
def sendEmail(fromEmail, subject, toEmail, contentType, mailContent):
    if fromEmail and subject and toEmail and contentType and Content:
        print('SENDING')
        # sg = sendgrid.SendGridAPIClient(apikey=config['SENDGRID']['KEY'])
        # from_email = Email(fromEmail)
        # to_email = Email(toEmail)
        # content = Content(contentType, mailContent)
        # mail = Mail(from_email, subject, to_email, content)
        # response = sg.client.mail.send.post(request_body=mail.get())

# place an email in the queue for testng 
@app.route('/test')
def hello(): 
    db.child("email/queue").push({"fromEmail":"teamconvoo@gmail.com","subject":"You are officially on the Beta List!", "toEmail":"email.will.in.china@gmail.com", "contentType":"text/plain", "mailContent":"Woohoo!", "time": int(time.time())})
    return jsonify({'message': "We sent a test email!"})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
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