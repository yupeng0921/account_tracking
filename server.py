#! /usr/bin/env python
#coding=utf-8

import os
import time
import yaml
import json
import zipfile
import logging
import traceback
import csv
import hashlib
from uuid import uuid4
from flask import Flask, request, redirect, url_for, render_template, abort, Response, make_response
from werkzeug import secure_filename
from flask.ext.login import LoginManager , login_required , UserMixin , login_user, logout_user, current_user

from account_op import get_search_op, do_search, get_columns, set_columns, get_scripts, generate_csv, update_profile, \
    get_profile, upload_script, delete_script, do_search_and_run_script, get_script_body_by_name, AccountLines, \
    get_primary_name, get_versions, get_version, get_raw_user, set_raw_user, get_all_usernames, delete_raw_user, update_raw_user

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
    def __init__(self, username, password_md5, userid, active=True):
        self.userid = userid
        self.username = username
        self.password_md5 = password_md5
        self.active = active
    def get_id(self):
        return self.userid
    def is_active(self):
        return self.active

class UsersRepository():
    def get_user_by_name(self, username):
        return self.get_user_from_db(username)
    def get_user_by_id(self, userid):
        return self.get_user_from_db(userid)
    # assume username and userid are the same value
    def get_user_from_db(self, name_or_id):
        raw_user = get_raw_user(name_or_id)
        if not raw_user:
            return None
        password_md5 = raw_user['password_md5']
        return User(name_or_id, password_md5, name_or_id)

with open(login_file) as f:
    login_profile = yaml.safe_load(f)

admin_username = login_profile['admin_username']
admin_password = unicode(login_profile['admin_password'])
admin_password_md5 = hashlib.md5(admin_password).hexdigest()
try:
    set_raw_user(admin_username, admin_password_md5)
except Exception, e:
    print(str(e))
    pass
users_repository = UsersRepository()

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
        if registeredUser != None and unicode(registeredUser.password_md5) == unicode(hashlib.md5(unicode(password)).hexdigest()):
            login_user(registeredUser)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            logging.warning('invalide username or password for user %s' % username)
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
    return redirect(url_for('login'))

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
        # yield line.decode('utf-8')

import codecs
def do_upload(action, fullpath):
    f = codecs.open(fullpath, 'r', 'utf-8')
    # f = open(fullpath, 'r')
    # csv_reader = csv.reader(f)
    csv_reader = unicode_csv_reader(f)
    titles = csv_reader.next()
    titles = [title.strip() for title in titles]
    try:
        account_lines = AccountLines(titles, int(time.time()), current_user.username)
    except Exception, e:
        msg = '%s failed\n%s' % (action, unicode(e))
        raise Exception(msg)
    varify_errors = []
    line_number = 1
    for values in csv_reader:
        line_number += 1
        values = [value.strip() for value in values]
        if action == 'delete' and len(values) != 1:
            logging.error('%d has more than one columns: %s' % (line_number, values))
            varify_errors.append(line_number)
        try:
            account_lines.add_line(values)
        except Exception, e:
            msg = traceback.format_exc()
            logging.error(unicode(e))
            logging.error(msg)
            varify_errors.append(line_number)
    if varify_errors:
        msg = 'varify failed: %s' % varify_errors
        raise Exception(msg)
    if action == 'create':
        account_lines.create_account()
    elif action == 'update':
        account_lines.update_account()
    elif action == 'delete':
        account_lines.delete_account()
    else:
        raise Exception('unsupport action %s' % action)

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
    search_op = get_search_op()
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
    sort_by = request.args.get('sort')
    j_params = json.loads(params)
    result = do_search(j_params, sort_by)
    return render_template('search_result.html', result=result, params=params, user=current_user, prev_search=params, sort_by=sort_by)

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
                    value = ''
                column['value'] = value
            elif column['type'] == 'time':
                value = request.form['%s_time' % name]
                column['value'] = value
            elif column['type'] == 'time_event':
                checked = request.form['%s_time_event_option' % name]
                timestr = request.form['%s_time_event_date' % name]
                if checked and timestr:
                    column['value'] = '%s/%s' % (timestr, checked)
                else:
                    column['value'] = ''
            elif column['type'] == 'textarea':
                value = request.form['%s_textarea' % name]
                column['value'] = value
            else:
                logging.error('invalid column: %s' % unicode(column))
                abort(500)
        set_columns(columns, username=current_user.username, timestamp=int(time.time()))
        prev_search = request.args.get('prev_search')
        sort_by = request.args.get('sort')
        if prev_search:
            return redirect(url_for('search_result', params=prev_search, sort=sort_by))
        else:
            return redirect(url_for('edit_item', primary_key=primary_key))
    columns = get_columns(primary_key)
    return render_template('edit.html', columns=columns, user=current_user)

@app.route('/download')
@app.route('/download/<params>')
@login_required
def download(params):
    sort_by = request.args.get('sort')
    j_params = json.loads(params)
    result = generate_csv(j_params, sort_by)
    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=download.csv"
    return response

@app.route('/script', methods=['GET', 'POST'])
@login_required
def script():
    if current_user.username != 'admin':
        return abort(403)
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
    if current_user.username != 'admin':
        return abort(403)
    body = get_script_body_by_name(script_name)
    return render_template('script_body.html', body=body, user=current_user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.username != 'admin':
        return abort(403)
    if request.method == 'POST':
        profile_file = request.files['profile_file']
        filename = secure_filename(profile_file.filename)
        profile_filename = os.path.join(current_file_full_path, upload_folder, filename)
        profile_file.save(profile_filename)
        try:
            update_profile(profile_filename)
        except Exception, e:
            os.remove(profile_filename)
            return unicode(e)
        os.remove(profile_filename)
        return redirect(url_for('profile'))
    profile = get_profile()
    return render_template('profile.html', profile=profile, user=current_user)

@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    if current_user.username != 'admin':
        return abort(403)
    if request.method == 'POST':
        primary_key = request.form['primary_key_text']
        return redirect(url_for('one_history', primary_key=primary_key))
    return render_template('history.html', primary_key=get_primary_name(), user=current_user)

@app.route('/history/<primary_key>', methods=['GET', 'POST'])
@login_required
def one_history(primary_key=None):
    if current_user.username != 'admin':
        return abort(403)
    if request.method == 'POST':
        pass
    versions = get_versions(primary_key, limit=1000, skip=0)
    return render_template('one_history.html', primary_key=primary_key, versions=versions, user=current_user)

@app.route('/history/<primary_key>/<raw_date>')
@login_required
def show_version_body(primary_key=None, raw_date=None):
    if current_user.username != 'admin':
        return abort(403)
    version_body = get_version(primary_key, raw_date)
    return render_template('version_body.html', version_body=version_body, user=current_user)

@app.route('/users', methods=['GET', 'POST'])
@login_required
def users_management():
    if current_user.username != 'admin':
        return abort(403)
    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'create':
            username = request.form['username_text']
            if len(username) < 1:
                return 'username should at least 1 character: [%s]' % username
            password = request.form['password_text']
            if len(password) < 3:
                return 'password should has at least 3 characters'
            password_md5 = hashlib.md5(password).hexdigest()
            try:
                set_raw_user(username, password_md5)
            except Exception, e:
                return unicode(e)
        elif action == 'delete':
            username = request.args.get('username')
            delete_raw_user(username)
        else:
            return 'unknow action: %s' % action
        return redirect(url_for('users_management'))
    usernames = get_all_usernames()
    return render_template('users.html', usernames=usernames, user=current_user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        username = current_user.username
        password = request.form['password_text']
        verify_password = request.form['verify_password_text']
        if password != verify_password:
            return 'password inconsistent'
        password_md5 = hashlib.md5(password).hexdigest()
        update_raw_user(username, password_md5)
        return redirect(url_for('settings'))
    return render_template('settings.html', user=current_user)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
