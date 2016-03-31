import json
import os

from flask import abort, redirect, request, render_template, url_for, session

from app import app

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login-submit', methods=['POST'])
def login_submit():
    user_dir = os.path.join(app.config['DATA_PATH'], "user")
    user_files = [os.path.join(user_dir, f) for f in os.listdir(user_dir)]
    user_files = [f for f in user_files if os.path.isfile(f)]

    for user_file in user_files:
        with open(user_file, 'r') as f:
            data = json.load(f)
            if request.form["username"] == data["username"]:
                user_id = data["id"]
                break
    else: # no break
        return "Error: User name does not exist"
    
    information_file = os.path.join(user_dir, "{}.txt".format(user_id))
    try:
        with open(information_file, 'r') as read_file:
            user_data = json.load(read_file)
            if user_data["password"] != request.form["password"]:
                return "Error: User name or password is incorrect"
    except EnvironmentError:
        abort(500)

    session["logged_in"] = True 
    session["user_id"] = user_id 

    return "Success! You have logged in!"

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))
