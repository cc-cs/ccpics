
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/')
def root():
    return '<h1>Welcome to the PiCS website!</h1>'

@app.route('/register')
def register():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PiCS Register</title>
    </head>
    <body>
        <h1>This is the registration page!</h1>
        <form method="POST" action="/registersubmit">
            <table>
                <tr>
                    <td>Username:</td>
                    <td>
                        <input type="text" id="username" name="username" placeholder="Your username..." />
                    </td>
                </tr>
                <tr>
                    <td>Password:</td>
                    <td>
                        <input type="password" id="password" name="password" placeholder="Your password..." />
                    </td>
                </tr>
                <tr>
                    <td>Email:</td>
                    <td>
                        <input type="email" id="email" name="email" placeholder="Your email address..." />
                    </td>
                </tr>
                <tr>
                    <td>
                        <input type="submit" value="Submit" name="submit" id="submit" />
                    </td>
                </tr>
            </table>
        </form>
    </body>
    </html>
'''

@app.route('/registersubmit', methods=['POST'])
def registersubmit():
    pass
