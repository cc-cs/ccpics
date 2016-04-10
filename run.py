#!venv/bin/python

import os

from flask import url_for

from app import app

if __name__ == "__main__":
    DATA_MODELS = ['question', 'solution', 'user', 'submission', 'result']
    for model in DATA_MODELS:
        directory_path = os.path.join(app.config['DATA_PATH'], model)
        if not os.path.isdir(directory_path):
            try:
                os.makedirs(directory_path, exist_ok=False)
            except OSError:
                print("Directory already exists!")

    app.run(debug=True, threaded=True)
