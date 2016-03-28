
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

@app.route('/')
def root():
    return '<h1>Welcome to the PiCS website!</h1>'

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registersubmit', methods=['POST'])
def registersubmit():
    pass
