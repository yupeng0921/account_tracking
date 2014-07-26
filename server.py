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

from account_op import search_op, do_search, get_columns, set_columns, get_scripts, \
    upload_script, delete_script, do_search_and_run_script, get_script_body_by_name, AccountLines

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
server_log_file = conf['server_log_file']

upload_folder = 'upload'

format = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
datefmt='%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename=server_log_file, level=logging.DEBUG, format=format, datefmt=datefmt)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def do_upload(action, fullpath):
    f = open(fullpath, 'r')
    titles = f.next().split(',')
    titles = [title.strip() for title in titles]
    try:
        account_lines = AccountLines(titles)
    except Exception, e:
        msg = '%s failed\n%s' % (action, unicode(e))
        raise Exception(msg)
    varify_errors = []
    line_number = 1
    for eachline in f:
        line_number += 1
        values = eachline.split(',')
        values = [value.strip() for value in values]
        try:
            account_lines.add_line(values)
        except Exception, e:
            logging.error(unicode(e))
            varify_errors.append(line_number)
    if varify_errors:
        msg = 'varify failed: %s' % varify_errors
        raise Exception(msg)
    action_error = None
    if action == 'create':
        account_lines.create_account()
    elif action == 'update':
        account_lines.update_account()
    elif action == 'delete':
        account_lines.delete_account()

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
            do_upload(action, upload_filename)
        except Exception, e:
            os.remove(upload_filename)
            return unicode(e)
        os.remove(upload_filename)
        return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        params = []
        for item in search_op:
            name = item['name']
            param = {}
            param['name'] = name
            if item['type'] == 'text':
                option = request.form['%s_option' % name]
                if option == 'match all':
                    continue
                param['option'] = option
                param['text'] = request.form['%s_text' % name]
            else:
                raise Exception('unsupport type: %s' % item)
            params.append(param)
        params=json.dumps(params)
        script = request.form['script_radio']
        if script == 'no_script':
            return redirect(url_for('search_result', params=params))
        else:
            return redirect(url_for('run_script', params=params, script=script))
    scripts = get_scripts()
    return render_template('search.html', items=search_op, scripts=scripts)

@app.route('/search/<params>')
def search_result(params):
    params = json.loads(params)
    result = do_search(params)
    return render_template('search_result.html', result=result)

@app.route('/search/<params>/<script>')
def run_script(params, script):
    params = json.loads(params)
    result = do_search_and_run_script(params, script)
    return render_template('statistic.html', result=result)

@app.route('/edit')
@app.route('/edit/<primary_key>', methods=['GET', 'POST'])
def edit_item(primary_key):
    if request.method == 'POST':
        columns = get_columns()
        for column in columns:
            name = column['name']
            if column['type'] == 'text':
                value = request.form['%s_text' % name]
                column['value'] = value
            elif column['type'] == 'boolean':
                value = request.form['%s_boolean' % name]
                if value == 'not set':
                    continue
                column['value'] = value
            elif column['type'] == 'time':
                value = request.form['%s_time' % name]
                if not value:
                    continue
                column['value'] = value
            elif column['type'] == 'time_event':
                option = request.form['%s_time_event_option' % name]
                if option == 'not set':
                    continue
                checked = option
                timestr = request.form['%s_time_event_date' % name]
                column['value'] = '%s/%s' % (timestr, checked)
            elif column['type'] == 'textarea':
                value = request.form['%s_textarea' % name]
                column['value'] = value
            else:
                logging.error('invalid column: %s' % unicode(column))
                abort(500)
        set_columns(columns)
        return redirect(url_for('edit_item', primary_key=primary_key))
    columns = get_columns(primary_key)
    return render_template('edit.html', columns=columns)

@app.route('/script', methods=['GET', 'POST'])
def script():
    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'upload':
            script_file = request.files['script_file']
            filename = secure_filename(script_file.filename)
            script_filename = os.path.join(current_file_full_path, upload_folder, filename)
            script_file.save(script_filename)
            try:
                upload_script(script_filename, filename)
            except Exception, e:
                os.remove(script_filename)
                return unicode(e)
            os.remove(script_filename)
            return redirect(url_for('script'))
        elif action == 'delete':
            script_name = request.args.get('name')
            print('delete: %s' % script_name)
            try:
                delete_script(script_name)
            except Exception, e:
                return unicode(e)
            return redirect(url_for('script'))
    scripts = get_scripts()
    return render_template('script.html', scripts=scripts)

@app.route('/script/<script_name>')
def get_script_body(script_name):
    body = get_script_body_by_name(script_name)
    return render_template('script_body.html', body=body)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
