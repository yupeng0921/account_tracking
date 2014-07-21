#! /usr/bin/env python

import os
import time
import yaml
import logging
from pymongo import MongoClient
from flask import Flask, request, redirect, url_for, render_template, abort, Response
from werkzeug import secure_filename
from flask.ext.login import LoginManager , login_required , UserMixin , login_user, logout_user

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
message_collection = conf['message_collection']
message_magic_key = conf['message_magic_key']

upload_folder = 'upload'

def send_message(action, fullpath):
    '''
    action should be create, update or delete
    fullpath is the full path of the csv file
    '''
    if action not in ('create', 'update', 'delete'):
        raise Exception('invalid action: %s' % action)
    client = MongoClient(mongodb_addr, mongodb_port)
    db = client[db_name]
    collection = db[message_collection]
    message = {
        'action': action,
        'fullpath': fullpath,
        'status': 'doing'
        }
    condition = {'_id': message_magic_key, 'status': 'idle'}
    ret = collection.update(condition, message)
    if not ret['updatedExisting']:
        raise Exception('send message failed')

def get_information():
    '''
    return (status, info)
    status is doing or idle
    info is set by daemon
    '''
    client = MongoClient(mongodb_addr, mongodb_port)
    db = client[db_name]
    collection = db[message_collection]
    condition = {'_id': message_magic_key}
    ret = collection.find_one(condition, {'status':1,'info':1})
    print(ret)
    status = ret['status']
    if 'info' in ret:
        info = ret['info']
    else:
        info = ''
    return (status, info)
    
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'hello world'

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        upload_file = request.files['upload_file']
        filename = secure_filename(upload_file.filename)
        timestamp = '%f' % time.time()
        upload_filename = '%s.%s' % (timestamp, filename)
        upload_filename = os.path.join(current_file_full_path, upload_folder, upload_filename)
        upload_file.save(upload_filename)
        action = request.form['actionsRadios']
        try:
            send_message(action, upload_filename)
        except Exception, e:
            os.remove(upload_filename)
            return unicode(e)
        return redirect(url_for('upload'))
    (status, info) = get_information()
    status_and_info = '%s\n%s' % (status, info)
    return render_template('upload.html', status_and_info=status_and_info)

@app.route('/insert', methods=['GET', 'POST'])
def insert():
    if request.method == 'POST':
        insert_file = request.files['insert_file']
        if not insert_file:
            return 'no insert file'
        filename = secure_filename(insert_file.filename)
        timestamp = '%f' % time.time()
        insert_filename = '%s.%s' % (timestamp, filename)
        insert_filename = os.path.join(current_file_full_path, upload_folder, insert_filename)
        insert_file.save(insert_filename)
        value = request.form.getlist('update')
        if value:
            action = 'update'
        else:
            action = 'create'
        try:
            send_message(action, insert_filename)
        except Exception, e:
            os.remove(insert_filename)
            return unicode(e)
        os.remove(insert_filename)
        return redirect(url_for('insert'))
    (status, info) = get_information()
    status_and_info = '%s\n%s' % (status, info)
    return render_template('insert.html', status_and_info=status_and_info)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        delete_file = request.files['delete_file']
        if not delete_file:
            return 'no delete file'
        filename = secure_filename(delete_file.filename)
        timestamp = '%f' % time.time()
        delete_filename = '%s.%s' % (timestamp, filename)
        delete_filename = os.path.join(upload_folder, delete_filename)
        delete_file.save(delete_filename)
        try:
            send_message('delete', delete_filename)
        except Exception, e:
            os.remove(delete_filename)
            return unicode(e)
        os.remove(delete_filename)
        return redirect(url_for('delete'))
    return render_template('delete.html')

@app.route('/status', methods=['GET'])
def status():
    (status, info) = get_information()
    status_and_info = '%s\n%s' % (status, info)
    return status_and_info

@app.route('/search', methods=['GET', 'POST'])
def search():
    return 'search'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
