
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import request
from flask import render_template
import json
from os import listdir
from os.path import isfile, join

app = Flask(__name__)

@app.route('/')
def root():
    return '<h1>Welcome to the PiCS website!</h1>'

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
