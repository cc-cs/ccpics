''''Utilities and API backend for user_service that serves user data'''

# TODO: Capitalize or Title case the error message???

import os

from flask import abort, json, jsonify, request

from .. import app

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'user')
ESSENTIALS = set(['id', 'username', 'password', 'email'])
UNIQUES = set(['username', 'email'])
PUBLIC = set(['id', 'username']) # TODO : Better names!!!
HIDDEN = set(['password']) # TODO: Is this better than having an accessible set of keys when a?
FIELDS = ESSENTIALS | UNIQUES | PUBLIC | set([])


##############################################################################
# Helpers
##############################################################################
def fetch_user_ids():
    '''Return all the user ids we have so far.'''
    
    return os.listdir(DATA_DIR)

def fetch_max_user_id():
    '''Return the largest user id created so far AS AN INT.'''

    user_ids = fetch_user_ids()
    
    return int(max(user_ids)[:-4]) if user_ids else -1

def fetch_user_files():
    '''Return all valid user data files.'''
    
    user_ids = fetch_user_ids()
    data_files = [os.path.join(DATA_DIR, id_) for id_ in user_ids]
    user_files = [f for f in data_files if os.path.isfile(f)]

    return user_files

def check_presence(keys=ESSENTIALS, data=None):
    '''Check if the given data contains information for the required set of keys.'''

    if not data or keys - set(data):
        return {'status': 400, 'error': "Required fields not present."}
    
    for key in keys:
        if not data[key]:
            return {'status': 400, 'error': "{} is required.".format(key)}

    return {'status': 200}

def check_uniqueness(keys=UNIQUES, data=None, *, ignore_self=False):
    '''Check if the given data is unique in the DB for the provided keys.'''
    user_files = fetch_user_files()
    if ignore_self:
        user_files.remove('{}.txt'.format(data['id']))    

    for user_file in user_files:
        with open(user_file, 'r') as f:
            file_data = json.load(f)
            for key in keys:
                if data[key] == file_data[key]:
                    return {'status': 409, 'error': "{} already in use!".format(key)}

    return {'status': 200}

def save_user(user_id, data):
    '''Save the given data for the user with the provided id.'''
    
    user_data = {k: data.get(k, None) for k in FIELDS}
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(user_id))
    try:
        with open(new_file_path, 'w') as write_file:
            json.dump(user_data, write_file)
    except EnvironmentError:
        return {'status': 500, 'error': "Internal Server Error while saving."}

    return {'status': 200}

##############################################################################
# Workers
##############################################################################
def fetch_users(queried_info=PUBLIC):
    '''Return a map of all users with their data enlisted.'''
    
    user_files = fetch_user_files()
    users = []
    try:
        for user_file in user_files:
            with open(user_file, 'r') as f:
                data = json.load(f)
                users.append({k: data.get(k, None) for k in queried_info})
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal server error reading data.'}
    
    return {'users': users}

def fetch_user(user_id):
    user_file = os.path.join(DATA_DIR, '{}.txt'.format(user_id))
    try:
        with open(user_file, 'r') as f:
            user_data = json.load(f)
            user_data = {k: user_data[k] for k in user_data if k not in HIDDEN}
    except EnvironmentError:
        return {'status': 404, 'error': "User doesn't exist."}

    return {'user': user_data}

def add_user(user_data):
    # Fetch the next possible id for our new user.
    max_id = fetch_max_user_id()
    user_id = "{0:08d}".format(max_id + 1)
    user_data['id'] = user_id
    
    # Check for presence of required fields.
    essentials_present = check_presence(data=user_data)
    if 'error' in essentials_present:
        return {'status': essentials_present['status'], 'error': essentials_present['error']}
    
    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=user_data)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}
    
    # Store the information if no errors encountered.
    save_user(user_id, user_data)

    user_data = {k: user_data[k] for k in user_data if k not in HIDDEN}
    
    return {'user': user_data}

def update_user(user_id, data):
    user_data = fetch_user(user_id)
    for k, v in data.items():
        try:
            user_data[k] = v
        except KeyError:
            return {'status': 400, 'error': "Invalid field: {}".format(k)}

    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=user_data, ignore_self=True)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}
    
    # Store the information if no errors encountered.
    save_user(user_id, user_data)

    user_data = {k: user_data[k] for k in user_data if k not in HIDDEN}
    
    return {'user': user_data}

###############################################################################
# Service API endpoints
###############################################################################
@app.route('/pics-service/api/v1.0/users', methods=['GET'])
def get_users():
    users = fetch_users()
    if 'error' in users:
        abort(users['status'], users['error'])
    return jsonify(users)

@app.route('/pics-service/api/v1.0/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = fetch_user(user_id)
    if 'error' in user:
        abort(user['status'], user['error'])
    return jsonify(user)

@app.route('/pics-service/api/v1.0/users', methods=['POST'])
def create_user():
    user_creation = add_user(user_data=request.json)
    if 'error' in user_creation:
        abort(user_creation['status'], user_creation['error'])
    return jsonify(user_creation), 201
