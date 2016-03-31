from flask import make_response, jsonify

from app import app

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': error.description}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': error.description}), 404)

@app.errorhandler(409)
def conflict(error):
    return make_response(jsonify({'error': error.description}), 409)
