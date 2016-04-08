from flask import flash, json, redirect, request, render_template, url_for, session

from .. import app
from ..services import question_service
from ..services import result_service

@app.route('/results')
def render_results():
    admin = request.args.get('admin', None)
    results = result_service.fetch_results()['results']
    if admin and session['user_id'] in app.config['ADMINS']:
        return render_template('admin-results.html', results=results)
    results = [result for result in results if result['user-id'] == session['user_id']]
    return render_template('results.html', results=results)

@app.route('/results/<result_id>', methods=['GET'])
def render_result(result_id):
    result = result_service.fetch_result(result_id=result_id)['result']
    return render_template('result.html', result=result)