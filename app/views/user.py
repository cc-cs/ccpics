from flask import flash, json, redirect, request, render_template, url_for

from .. import app
from ..services import user_service

@app.route('/users')
def render_users():
    users = user_service.fetch_users()['users']
    return render_template('users.html', users=users)

@app.route('/users/<user_id>', methods=['GET'])
def render_user(user_id):
    user = user_service.fetch_user(user_id=user_id)['user']
    return render_template('user.html', user=user)
    
