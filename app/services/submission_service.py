import os

from datetime import datetime

from flask import abort, json, jsonify

from .. import app

# TODO: Abstract away all the data operations into a Model interface.
# TODO: Remove all this duplication between services!!!
# TODO: Add authentication for some of these info.

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'submission')
ESSENTIALS = set(['question-id', 'user-id', 'language', 'source-code'])
UNIQUES = set([])
PUBLIC = set(['id', 'language', 'question-id', 'question-title', 'user-id', 'timestamp', 'status']) 
HIDDEN = set([])
FIELDS = ESSENTIALS | UNIQUES | PUBLIC | set([])


##############################################################################
# Helpers
##############################################################################
def fetch_submission_ids():
    '''Return all the submission ids we have so far.'''

    return [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]

def fetch_max_submission_id():
    '''Return the largest submission id created so far AS AN INT.'''

    submission_ids = fetch_submission_ids()

    return int(max(submission_ids)[:8]) if submission_ids else -1

def fetch_submission_files():
    '''Return all valid submission data files.'''
    
    submission_ids = fetch_submission_ids()
    data_files = [os.path.join(DATA_DIR, id_) for id_ in submission_ids]
    submission_files = [f for f in data_files if os.path.isfile(f)]

    return submission_files

def check_presence(keys=ESSENTIALS, data=None):
    '''Check if the given data contains information for the required set of keys.'''

    if not data or keys - set(data):
        return {'status': 400, 'error': "Required fields not present."}
    
    for key in keys:
        if not data[key]:
            return {'status': 400, 'error': "{} is required.".format(key)}

    return {'status': 200}

def check_uniqueness(keys=UNIQUES, data=None):
    '''Check if the given data is unique in the DB for the provided keys.'''

    submission_files = fetch_submission_files()
    for submission_file in submission_files:
        with open(submission_file, 'r') as f:
            file_data = json.load(f)
            for key in keys:
                if data[key] == file_data[key]:
                    return {'status': 409, 'error': "{} already in use!".format(key)}

    return {'status': 200}

def save_submission(submission_id, data):
    '''Save the given data for the submission with the provided id.'''
    
    submission_data = {k: data.get(k, None) for k in FIELDS}
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(submission_id))
    try:
        with open(new_file_path, 'w') as write_file:
            json.dump(submission_data, write_file)
    except EnvironmentError:
        return {'status': 500, 'error': "Internal Server Error while saving."}

def fetch_queued_submissions():
    '''Return all the submissions that are on queue to be processed by the grader'''

    try:
        with open(os.path.join(DATA_DIR, "grading.queue"), "r") as f:
            queue = json.load(f)
    except EnvironmentError as e:
        queue = {'queue': {}}
    except ValueError:
        return {'status': 500, 'error': 'Internal Server Error'}

    return queue

def queue_submission(submission_id, timestamp):
    '''Queue the submission to be processed by the grader.'''

    queue = fetch_queued_submissions()
    if 'error' in queue:
        return queue
    queue['queue'][submission_id] = timestamp

    try:
        with open(os.path.join(DATA_DIR, 'grading.queue'), 'w') as f:
            json.dump(queue, f)
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal Server Error while adding.'}

    return {'status': 200}

##############################################################################
# Workers
##############################################################################
def fetch_submissions(queried_info=PUBLIC):
    '''Return a map of all submissions with their data enlisted.'''
    
    submission_files = fetch_submission_files()
    submissions = []
    try:
        for submission_file in submission_files:
            with open(submission_file, 'r') as f:
                data = json.load(f)
                submissions.append({k: data.get(k, None) for k in queried_info})
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal server error reading data.'}
    
    return {'submissions': submissions}

def fetch_submission(submission_id):
    submission_file = os.path.join(DATA_DIR, '{}.txt'.format(submission_id))
    try:
        with open(submission_file, 'r') as f:
            submission_data = json.load(f)
            submission_data = {k: submission_data[k] for k in submission_data if k not in HIDDEN}
    except EnvironmentError:
        return {'status': 404, 'error': "Submission doesn't exist."}

    return {'submission': submission_data}

def add_submission(submission_data):
    # Fetch the next possible id for our new submission.
    max_id = fetch_max_submission_id()
    submission_id = "{0:08d}".format(max_id + 1)
    submission_data['id'] = submission_id
    
    # Check for presence of required fields.
    essentials_present = check_presence(data=submission_data)
    if 'error' in essentials_present:
        return {'status': essentials_present['status'], 'error': essentials_present['error']}
    
    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=submission_data)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}

    # Add a timestamp.
    submission_data['timestamp'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S Z")

    # Queue the submission to be graded.
    submit_to_queue = queue_submission(submission_id, submission_data['timestamp'])
    if 'error' in submit_to_queue:
        return {'status': submit_to_queue['status'], 'error': submit_to_queue['error']}
    submission_data['status'] = 'Queued'

    # Store the information if no errors encountered.
    save_submission(submission_id, submission_data)

    submission_data = {k: submission_data[k] for k in submission_data if k not in HIDDEN}
    
    return {'submission': submission_data}


###############################################################################
# Service API endpoints
###############################################################################
@app.route('/pics-service/api/v1.0/submissions', methods=['GET'])
def get_submissions():
    submissions = fetch_submissions()
    if 'error' in submissions:
        abort(submissions['status'], submissions['error'])
    return jsonify(submissions)

@app.route('/pics-service/api/v1.0/submissions/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    submission = fetch_submission(submission_id)
    if 'error' in submission:
        abort(submission['status'], submission['error'])
    return jsonify(submission)

@app.route('/pics-service/api/v1.0/submissions', methods=['POST'])
def create_submission():
    submission_creation = add_submission(submission_data=request.json)
    if 'error' in submission_creation:
        abort(submission_creation['status'], submission_creation['error'])
    return jsonify(submission_creation), 201

@app.route('/pics-service/api/v1.0/submissions-queue', methods=['GET'])
def get_queued_submissions():
    submissions_queue = fetch_queued_submissions()
    if 'error' in submissions_queue:
        abort(submissions_queue['status'], submissions_queue['error'])
    return jsonify(submissions_queue)
