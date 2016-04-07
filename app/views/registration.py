from flask import flash, json, redirect, request, render_template, url_for

from .. import app
from ..services import user_service

USER_SERVICE_URL = app.config['SERVICE_URL'] + 'users'

@app.route('/registration')
def registration():
    print(app.config['SERVICE_URL'])
    return render_template('registration.html')

@app.route('/registration-submit', methods=['POST'])
def registration_submit():
    error = None

    # TODO: This logic is repeated in user_service, ??? (frontend?),
    # we probably want to handle something similar for all services as well.
    essentials = set(['username', 'password', 'email'])
    if essentials - set(request.form):
        error = "Please fill out the form."

    # TODO: Remember the fields that were filled.
    for essential in essentials:
        if not request.form[essential]:
            error = "Please provide your {}.".format(essential)

    if not error:
        # TODO: Switch to web requests for the service??? Check below for howto.
        # import requests
        # reg_req_url = request.url_root + USER_SERVICE_URL
        # reg_req = requests.post(url=reg_req_url, json=form_data)
        # if reg_req.status_code == 201:
        #     flash("You have been registered!", "success")
        #     return redirect(url_for('index'))
        # reg_req_reply = reg_req.json()

        form_data = json.loads(json.dumps(request.form))
        form_data.pop("submit", None)
        registration_request_response = user_service.add_user(user_data=form_data)
        if 'error' in registration_request_response:
            error = registration_request_response['error']
        else:
            flash("You have been registered!", "success")
            return redirect(url_for('index'))

    error = error if error else "Sorry, something went wrong. Please try again later."
    flash(error, 'error')

    return render_template('registration.html')


