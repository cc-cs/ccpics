
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, request, render_template, url_for, session 
import json
from os import listdir
from os.path import isfile, join

app = Flask(__name__)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registersubmit', methods=['POST'])
def registersubmit():
    user_dir = "/home/ccpics42/mysite/pics/data/user/"
    user_files = [f for f in listdir(user_dir) if isfile(join(user_dir, f))]
    error = False


    # Get the largest user ID
    max_id = 0
    for user_file in user_files:
        user_id = int(user_file[:8])

        if user_id > max_id:
            max_id = user_id

    # Read the files to check if the user exists.
    # Use email address for uniqueness.
    for user_file in user_files:
        with open(user_dir + user_file, 'r') as f:
            data = json.load(f)

            if request.form["email"] == data["email"]:
                error = True

        if error:
            break

    if error:
        return "Error: User already exists"
    else:
        new_file_path = user_dir + "{0:08d}".format(max_id + 1) + ".txt"

        with open(new_file_path, 'w') as write_file:
            user_data = {}
            user_data["username"] = request.form["username"]
            user_data["password"] = request.form["password"]
            user_data["email"] = request.form["email"]
            json.dump(user_data, write_file)

        return "Success! You have been registered!"


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loginsubmit', methods=['POST'])
def loginsubmit():
    user_dir = "/home/ccpics42/mysite/pics/data/user/"
    user_files = [f for f in listdir(user_dir) if isfile(join(user_dir, f))]
    user_id = -1

    for user_file in user_files:
        with open(user_dir + user_file, 'r') as f:
            data = json.load(f)

            if request.form["username"] == data["username"]:
                user_id = int(user_file[:8])

        if user_id != -1: 
            break
    
    if user_id == -1:
        return "Error: User name does not exist"
    
    information_file = user_dir + "{0:08d}".format(user_id) + ".txt"
    
    with open(information_file, 'r') as read_file:
        user_data = json.load(read_file)
        
        if user_data["password"] != request.form["password"]:
            return "Error: User name or password is incorrect"
        else:
            session["logged_in"] = True 
            session["user_id"] = user_id 
            return "Success! You have logged in!"

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('root'))

app.secret_key = b"\x9d\x00\xb1\x80b\xd6\t'\x853V\xbf\xac2\xcd\x98Y\x88\xf3BKO\x9c\xa3"

if __name__ == '__main__':
    app.debug = True 
    app.run()
