from flask import abort, request, render_template

from .. import app
from ..services import question_service
from ..services import result_service

@app.route('/results')
def render_results():
    admin = request.args.get('admin', None)
    results = result_service.fetch_results()['results']
    if admin and session['user_id'] in app.config['ADMINS']:
        return render_template('admin-results.djhtml', results=results)
    results = [result for result in results if result['user-id'] == session['user_id']]
    return render_template('results.djhtml', results=results)

@app.route('/results/<result_id>', methods=['GET'])
def render_result(result_id):
    result = result_service.fetch_result(result_id=result_id)
    if 'error' in result:
        abort(result['status'], result['error'])

    result = result['result']

    return render_template('result.djhtml', result=result)
