from flask import Flask, request, render_template, url_for, redirect, abort
from twilio.util import RequestValidator
from boto3.dynamodb.conditions import Key, Attr
import twilio.twiml
from twilio.rest import TwilioRestClient
import boto3
import os
import datetime
import time

app = Flask(__name__)
app.config.from_pyfile('local_settings.py')

"""This is our connection object to Amazon dynamoDB table 'call_logs'"""
client = boto3.resource('dynamodb',
                      aws_access_key_id= 'AMAZON CREDENTIAL1',
                      aws_secret_access_key= 'AMAZON CREDENTIAL2',
                      region_name='us-west-2')
table = client.Table('call_logs')

@app.route('/', methods = ['GET', 'POST'])
def app_portal():
    direction = request.values.get('Direction', None)
    if direction == 'inbound': #If calls made to app, skip to call handling
        return redirect('/handle_call')

    else:
        results = table.scan()
        list_of_logs = results['Items']
        sorted_list_of_logs = sorted(list_of_logs, key = byDateTime)
        sorted_list_of_logs.reverse()
        return render_template('index.html', call_history = sorted_list_of_logs)


@app.route("/make_call", methods=['GET', 'POST'])
def handle_make_call():
    """Makes a delayed call to the player, where delay can be 0."""
    number=request.form["yournumber"]
    delay=request.form["time"]
    #Make sure to change TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to the one belonging to the linked
    # Twilio account. Change this in local_settings.py
    delay_interval = 0
    if delay[0] == 's':
        delay_interval = int(delay[1:])
    elif delay[0] == 'm':
        delay_interval = 60*int(delay[1:])
    elif delay[0] == 'h':
        delay_interval = 60*60*int(delay[1:])
    # Make the call
    time.sleep(delay_interval)
    ACCOUNT_SID = app.config['TWILIO_ACCOUNT_SID']
    AUTH_TOKEN = app.config['TWILIO_AUTH_TOKEN']

    Client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

    call = Client.calls.create(
                            	to=number,
                            	from_=app.config['TWILIO_CALLER_ID'],
                            	url= "https://warm-sierra-8108.herokuapp.com/handle_call",
                            	method="GET",
                            	fallback_method="GET",
                            	status_callback_method="GET",
                            	record="false")
    print (call.sid)
    return redirect('/')

@app.route("/handle_call", methods=['GET', 'POST'])
def taking_user_input():
    """Both calls made to our app and calls made by our app lead here.
       This is a Twilio request to our app, needs verificaiton!"""
    """if not twilio_validator_function(request):
        abort(401)""" #Uncomment this validator once server and Twilio account are properly configured.
    resp = twilio.twiml.Response()
    resp.say("Let's play a game of FizzBuzz.")
    #Ask user for number input. Nested a say verb inside the gather verb
    resp.gather(action = "/handle_input", timeout=25).say("Please enter a number to play fizz_buzz. When you are done, press pound or wait 25 seconds.")
    return str(resp)

@app.route("/handle_input", methods=['GET', 'POST'])
def responding_to_input():
    """Handle key press from a user.
       This is a Twilio request to our app, needs verification!"""
    # Get the digit pressed by the user
    """if not twilio_validator_function(request):
        abort(401)"""  #Uncomment this validator once server and Twilio account are properly configured.
    digit_pressed = request.values.get('Digits', None)
    resp = twilio.twiml.Response()
    try:
        n = int(digit_pressed)
    except ValueError:
        resp.say("That was not an integer. Please try again.")
        # Caller is redirected to homepage if number not valid
        return redirect("/")
    resp.say(fizz_buzz(n))
    # Gathering call information to log it
    Datetime = repr(datetime.datetime.now())
    call_direction = request.values.get('Direction')
    PhoneNumber = 0
    if call_direction == 'inbound':
        PhoneNumber = request.values.get('From')
    else:
        PhoneNumber = request.values.get('To')
    UserInput = str(n)

    call_item = {
                'Datetime': Datetime,
                'PhoneNumber' : PhoneNumber,
                'UserInput' : UserInput
                }
    table.put_item(Item = call_item)
    return str(resp)



@app.route("/call_replay", methods=['GET', 'POST'])
def handle_call_replay():
    """Replicates a call when user clicks call_replay button"""
    phoneNumber = request.form['PhoneNumber']
    number = request.form['UserInput']
    delay=5
    #Make sure to change TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to the one belonging to the linked
    # Twilio account. Change this in local_settings.py
    Client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'],app.config['TWILIO_AUTH_TOKEN'])

    #

    # Make the call
    time.sleep(delay)
    call = Client.calls.create(
                            	to=phoneNumber,
                            	from_="+17606542884",
                            	url= "https://warm-sierra-8108.herokuapp.com/call_replay_response/{}".format(number),
                            	method="GET",
                            	fallback_method="GET",
                            	status_callback_method="GET",
                            	record="false")

    return redirect('/')

@app.route("/call_replay_response/<number>", methods=['GET', 'POST'])
def handle_call_replay_reponse(number = 0):
    "Replicates call. This call doesn't get re-recorded into logs."
    n = int(number)
    resp = twilio.twiml.Response()
    resp.say(fizz_buzz(n))
    return str(resp)


def fizz_buzz(n):
    """Outputs a string (with spacing) with the results of FizzBuzz from 1 to n"""
    fizz_string = ""
    counter = 1
    while counter <= n:
        truth_tuple = (counter % 3 == 0, counter % 5 == 0)
        if truth_tuple == (True, True):
            fizz_string += "FizzBuzz "
        elif truth_tuple == (True, False):
            fizz_string += "Fizz "
        elif truth_tuple == (False, True):
            fizz_string += "Buzz "
        else:
            fizz_string += "{} ".format(counter)
        counter += 1
    return fizz_string

def twilio_validator_function(request):
    """returns true for authentic Twilio request, false for unauthenticated request"""
    validator = RequestValidator(app.config['TWILIO_AUTH_TOKEN'])
    URL = request.url
    params = {}
    if request.method == 'POST':
        params = request.values
    else:
        params = request.args
    twilio_signature = request.headers.get('X-Twilio-Signature')
    return validator.validate(URL, params, twilio_signature)

def byDateTime(call_log):
    '''I will use datetime.now() to construct these attributes'''
    return eval(call_log['Datetime'])


if __name__ == "__main__":
    app.run(debug=True)
