#! /usr/bin/env python

import os
import time
import yaml
import json
import logging
from pymongo import MongoClient
from flask import Flask, request, redirect, url_for, render_template, abort, Response
from werkzeug import secure_filename
from flask.ext.login import LoginManager , login_required , UserMixin , login_user, logout_user

from account_op import search_op, do_search, get_item

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

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        results = []
        for item in search_op:
            name = item['name']
            result = {}
            result['name'] = name
            if item['type'] == 'text':
                result['option'] = request.form['%s_option' % name]
                result['text'] = request.form['%s_text' % name]
            elif item['type'] == 'multichoice':
                result['choices'] = request.form.getlist('%s_choices' % name)
            results.append(result)
        params=json.dumps(results)
        return redirect(url_for('search_result', params=params))
    return render_template('search.html', items=search_op)

@app.route('/search/<params>')
def search_result(params):
    params = json.loads(params)
    result = do_search(params)
    return render_template('search_result.html', result=result)

@app.route('/edit')
@app.route('/edit/<primary_key>')
def edit_item(primary_key):
    item = get_item(primary_key)
    return render_template('edit.html', item=item)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
