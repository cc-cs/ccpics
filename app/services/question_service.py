import os

from flask import abort, json, jsonify

from .. import app

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'question')

@app.route('/pics-service/api/v1.0/questions', methods=['GET'])
def get_questions():
    data_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)]
    question_files = [f for f in data_files if os.path.isfile(f)]

    # list of things to return when requested all questions, keep it small
    essentials = set(['id', 'title', 'languages']) 
    questions = []
    for question_file in question_files:
        with open(question_file, 'r') as f:
            data = json.load(f)
            questions.append({k: data.get(k, None) for k in essentials})
    return jsonify({'questions': questions})

@app.route('/pics-service/api/v1.0/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    question_file = os.path.join(DATA_DIR, '{}.txt'.format(question_id))
    try:
        with open(question_file, 'r') as f:
            data = json.load(f)
    except EnvironmentError:
        abort(404)
        
    return jsonify({'question': data})
        
