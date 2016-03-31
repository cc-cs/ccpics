import os
import requests

from flask import flash, json, redirect, request, render_template, url_for

from .. import app

USER_SERVICE_URL = app.config['SERVICE_URL'] + 'users'

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/registration-submit', methods=['POST'])
def registration_submit():
    error = None
    
    essentials = set(['username', 'password', 'email'])
    if essentials - set(request.form):
        print("hey now")
        error = "Please fill out the form."

    # TODO: Remember the fields that were filled.
    for essential in essentials:
        if not request.form[essential]:
            error = "Please provide your {}.".format(essential)

    if not error:        
        reg_req_url = request.url_root + USER_SERVICE_URL
        data = json.loads(json.dumps(request.form))
        data.pop("submit")
        headers = {'Content-Type': 'application/json'}
        reg_req = requests.post(url=reg_req_url,
                                headers=headers,
                                data=json.dumps(data))
        print("resp:", reg_req)
        if reg_req.status_code == 201:
            flash("You have been registered!", "success")
            return redirect(url_for('index'))
        reg_req_reply = reg_req.json()
        error = reg_req_reply['error'] if 'error' in reg_req_reply else error
        
    error = error if error else "Sorry, something went wrong. Please try again later."
    flash(error, 'error')

    return render_template('registration.html')


