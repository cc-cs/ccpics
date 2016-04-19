from flask import flash, json, redirect, request, render_template, url_for, session

from .. import app
from ..services import user_service
from ..services import result_service

@app.route('/users')
def render_users():
    users = user_service.fetch_users()['users']
    return render_template('users.djhtml', users=users)

@app.route('/users/<user_id>', methods=['GET'])
def render_user(user_id):
    user = user_service.fetch_user(user_id=user_id)['user']

    # Possible stat categories: 
    # pass, fail, Compilation failure, Timed out, 

    results = result_service.fetch_results()['results']
    results = [result for result in results if result['user-id'] == user_id]

    num_pass = 0
    num_fail = 0
    num_compfail = 0
    num_timedout = 0
    num_results = len(results)
    pass_percent = 0.0
    fail_percent = 0.0
    compfail_percent = 0.0
    timedout_percent = 0.0

    if len(results) > 0:
	    num_pass = len([result for result in results if result['verdict'] == 
	    	"pass"])
	    num_fail = len([result for result in results if result['verdict'] == 
	    	"fail"])
	    num_compfail = len([result for result in results if result['verdict'] == 
	    	"Compilation failure"])
	    num_timedout = len([result for result in results if result['verdict'] == 
	    	"Timed out"])

	    pass_percent = num_pass / float(num_results) * 100
	    fail_percent = num_fail / float(num_results) * 100
	    compfail_percent = num_compfail / float(num_results) * 100
	    timedout_percent = num_timedout / float(num_results) * 100

    return render_template('user.djhtml', user=user, num_pass=num_pass,
    	num_fail=num_fail, num_compfail=num_compfail,
    	num_timedout=num_timedout, num_results=num_results, 
    	pass_percent=pass_percent, fail_percent=fail_percent,
    	compfail_percent=compfail_percent, timedout_percent=timedout_percent)
    
