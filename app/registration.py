import json
import os

from flask import redirect, request, render_template

from app import app

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/registration-submit', methods=['POST'])
def registration_submit():
    return "Success! You have been registered!"
