import os

from flask import abort, json, jsonify, request

from .. import app

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'user')

@app.route('/pics-service/api/v1.0/users', methods=['GET'])
def get_users():
    data_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)]
    user_files = [f for f in data_files if os.path.isfile(f)]

    # list of things to return when requested all users, keep it small
    essentials = set(['id', 'username']) 
    users = []
    for user_file in user_files:
        with open(user_file, 'r') as f:
            data = json.load(f)
            users.append({k: data.get(k, None) for k in essentials})
    return jsonify({'users': users})

@app.route('/pics-service/api/v1.0/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user_file = os.path.join(DATA_DIR, '{}.txt'.format(user_id))
    try:
        with open(user_file, 'r') as f:
            data = json.load(f)
            data.pop('password')
    except EnvironmentError:
        abort(404)
        
    return jsonify({'user': data})

@app.route('/pics-service/api/v1.0/users', methods=['POST'])
def create_user():
    print("json", request.json)
    essentials = set(['username', 'password', 'email'])
    if not request.json or essentials - set(request.json):
        abort(400)

    for essential in essentials:
        if not request.json[essential]:
            abort(400)
        
    # TODO: Perhaps switch to making a request for users???
    # Fetch existing user files and get the largest existing user ID
    user_files = os.listdir(DATA_DIR)
    max_id = int(max(user_files)[:8])
    user_files = [os.path.join(DATA_DIR, f) for f in user_files]
    user_files = [f for f in user_files if os.path.isfile(f)]
    
    # Read the files to check if the user exists.
    # Uniqueness checked for username and email.
    for user_file in user_files:
        with open(user_file, 'r') as f:
            data = json.load(f)
            if request.json["email"] == data["email"]:
                abort(409, "Error: Email already in use!")
            elif request.json["username"] == data["username"]:
                abort(409, "Error: Username already in use!")

    # Store the information if no errors encountered
    user_id = "{0:08d}".format(max_id + 1)
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(user_id))
    with open(new_file_path, 'w') as write_file:
        user_data = {}
        user_data["id"] = user_id
        user_data["username"] = request.json["username"]
        user_data["password"] = request.json["password"]
        user_data["email"] = request.json["email"]
        json.dump(user_data, write_file)

    return jsonify({'user': user_data}), 201

