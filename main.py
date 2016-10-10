#!/usr/bin/python
# coding: utf-8

# [START app]
import logging
import configparser
from flask import Flask, jsonify

# settings.py
import os
from os.path import join, dirname
#from dotenv import load_dotenv
#dotenv_path = join(dirname(__file__), '.env')
#load_dotenv(dotenv_path)


# environment variables 
config = configparser.ConfigParser()
config.read('.env')


# using SendGrid's Python Library - https://github.com/sendgrid/sendgrid-python
import sendgrid
from sendgrid.helpers.mail import *

app = Flask(__name__)

# routes
@app.route('/')
def hello():
    return jsonify({'message': "Hello!"})


@app.route('/email')
def email():
    sg = sendgrid.SendGridAPIClient(apikey=config['SENDGRID']['KEY'])
    from_email = Email("teamconvoo@gmail.com")
    subject = "Hello World from the SendGrid Python Library!"
    to_email = Email("people@gmail.com")
    content = Content("text/plain", "Hello, Email!")
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return jsonify({'message': "Email sent!"})


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return jsonify({'message':'An internal error occurred.','status': 500})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)


# [END app]