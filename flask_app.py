
# A very simple Flask Hello World app for you to get started with...

from flask import Flask

app = Flask(__name__)

@app.route('/')
def root():
    return '<h1>Welcome to the PiCS website!</h1>'

