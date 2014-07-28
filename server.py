#! /usr/bin/env python

import os
import yaml
import json
import zipfile
import logging
import traceback
from uuid import uuid4
from flask import Flask, request, redirect, url_for, render_template, abort, Response, make_response
from werkzeug import secure_filename
from flask.ext.login import LoginManager , login_required , UserMixin , login_user, logout_user, current_user

from account_op import search_op, do_search, get_columns, set_columns, get_scripts, generate_csv, update_columns_format, \
    get_columns_format, upload_script, delete_script, do_search_and_run_script, get_script_body_by_name, AccountLines

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
server_log_file = conf['server_log_file']
login_file = conf['login_file']

upload_folder = 'upload'

format = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
datefmt='%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename=server_log_file, level=logging.DEBUG, format=format, datefmt=datefmt)

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, password, userid, active=True):
        self.userid = userid
        self.username = username
        self.password = password
        self.active = active
    def get_id(self):
        return self.userid
    def is_active(self):
        return self.active

class UsersRepository():
    def __init__(self):
        self.users_id = dict()
        self.users_name = dict()
        self.identifier = 0
    def save_user(self, user):
        self.users_id[user.userid] = user
        self.users_name[user.username] = user
    def get_user_by_name(self, username):
        return self.users_name.get(username)
    def get_user_by_id(self, userid):
        return self.users_id.get(userid)
    def next_index(self):
        self.identifier += 1
        return self.identifier

users_repository = UsersRepository()

with open(login_file) as f:
    login_profile = yaml.safe_load(f)
for user in login_profile['users']:
    username = user['username']
    password = user['password']
    new_user = User(username, password, users_repository.next_index())
    users_repository.save_user(new_user)

@login_manager.user_loader
def load_user(userid):
    return users_repository.get_user_by_id(userid)

app.config['SECRET_KEY'] = unicode(login_profile['secret_key'])
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        registeredUser = users_repository.get_user_by_name(username)
        logging.info(registeredUser)
        if registeredUser:
            logging.info(registeredUser.password)
        if registeredUser != None and unicode(registeredUser.password) == unicode(password):
            login_user(registeredUser)
            return redirect(url_for('index'))
        else:
            logging.warning('invalide username or password: %s %s' % (username, password))
            return abort(401)
    else:
        return Response('''
<form actoin="" method="post">
<p><input type=text id=username name=username>
<p><input type=password id=password name=password>
<p><input type=submit id=login_submit name=login_submit value=Login>
</form>
''')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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
@login_required
def upload():
    if request.method == 'POST':
        upload_file = request.files['upload_file']
        filename = secure_filename(upload_file.filename)
        upload_filename = '%s.%s' % (uuid4(), filename)
        upload_filename = os.path.join(current_file_full_path, upload_folder, upload_filename)
        upload_file.save(upload_filename)
        action = request.form['actionsRadios']
        try:
            do_upload(action, upload_filename)
        except Exception, e:
            os.remove(upload_filename)
            msg = traceback.format_exc()
            return unicode(msg)
        os.remove(upload_filename)
        return redirect(url_for('upload'))
    return render_template('upload.html', user=current_user)

@app.route('/search', methods=['GET', 'POST'])
@login_required
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
    return render_template('search.html', items=search_op, scripts=scripts, user=current_user)

@app.route('/search/<params>')
@login_required
def search_result(params):
    j_params = json.loads(params)
    result = do_search(j_params)
    return render_template('search_result.html', result=result, params=params, user=current_user)

@app.route('/search/<params>/<script>')
@login_required
def run_script(params, script):
    params = json.loads(params)
    graphs = do_search_and_run_script(params, script)
    return render_template('statistic.html', graphs=graphs, user=current_user)

@app.route('/edit')
@app.route('/edit/<primary_key>', methods=['GET', 'POST'])
@login_required
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
    return render_template('edit.html', columns=columns, user=current_user)

@app.route('/download')
@app.route('/download/<params>')
@login_required
def download(params):
    j_params = json.loads(params)
    result = generate_csv(j_params)
    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=download.csv"
    return response

@app.route('/script', methods=['GET', 'POST'])
@login_required
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
            try:
                delete_script(script_name)
            except Exception, e:
                return unicode(e)
            return redirect(url_for('script'))
    scripts = get_scripts()
    return render_template('script.html', scripts=scripts, user=current_user)

@app.route('/script/<script_name>')
@login_required
def get_script_body(script_name):
    body = get_script_body_by_name(script_name)
    return render_template('script_body.html', body=body, user=current_user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        columns_format_file = request.files['columns_format_file']
        filename = secure_filename(columns_format_file.filename)
        columns_format_filename = os.path.join(current_file_full_path, upload_folder, filename)
        columns_format_file.save(columns_format_filename)
        try:
            update_columns_format(columns_format_filename)
        except Exception, e:
            os.remove(columns_format_filename)
            return unicode(e)
        os.remove(columns_format_filename)
        return redirect(url_for('profile'))
    profile = get_columns_format()
    return render_template('profile.html', profile=profile, user=current_user)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
