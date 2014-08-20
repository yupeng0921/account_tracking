#! /usr/bin/env python

import yaml
import json
import logging
import os
import time
import csv
from uuid import uuid4
from tempfile import TemporaryFile
from subprocess import Popen, PIPE, STDOUT
from pymongo import MongoClient, DESCENDING
# from column_op import g_class_dict, g_all_classes, g_searchable_classes, g_primary_column_name, generate_columns_profile
# import column_op
from column_op import get_class_dict, get_all_classes, get_searchable_classes, get_primary_column_name, generate_columns_profile

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
accounts_collection_name = conf['accounts_collection_name']
default_csv_string = conf['default_csv_string']
default_csv_delimiter = conf['default_csv_delimiter']
scripts_collection_name = conf['scripts_collection_name']
awk_timeout = conf['awk_timeout']
graph_name_key = conf['graph_name_key']
graph_type_key = conf['graph_type_key']
graph_members_key = conf['graph_members_key']
profile_collection_name = conf['profile_collection_name']
profile_key = conf['profile_key']
user_collection_name = conf['user_collection_name']
timezone = conf['timezone']
timezone_seconds = timezone * 3600

client = MongoClient(mongodb_addr, mongodb_port)
db = client[db_name]
accounts_collection = db[accounts_collection_name]
scripts_collection = db[scripts_collection_name]
profile_collection = db[profile_collection_name]
user_collection = db[user_collection_name]

def make_timestamp(input_time):
    time_fmt = '%Y-%m-%dT%H:%M:%S'
    if timezone >= 0:
        suffix = 'GMT+%02d00' % timezone
    else:
        suffix = 'GTM+%02d00' % (-timezone)
    time_fmt = '%s%s' % (time_fmt, suffix)
    return time.strftime(time_fmt, time.gmtime(input_time+timezone_seconds))

def write_log(primary_key, timestamp, username, action, body):
    version_collection = db[primary_key]
    version_document = {'_id': timestamp,
                        'username': username,
                        'action': action,
                        'body': body}
    version_collection.insert(version_document)

search_op = []
reload_time = 0
def reload_profile():
    global search_op
    global reload_time
    item = profile_collection.find_one({'_id': profile_key})
    reload_time = item['timestamp']
    body = item['body']
    generate_columns_profile(body)
    searchable_class = get_searchable_classes()
    class_dict = get_class_dict()
    for class_name in searchable_class:
        class_type = class_dict[class_name]
        op = class_type.get_search_op()
        search_op.append(op)

def check_and_reload_profile():
    item = profile_collection.find_one({'_id': profile_key}, {'timestamp': 1})
    if item and item['timestamp'] > reload_time:
        reload_profile()

def check_profile(func):
    def _check_profile(*args, **kwargs):
        check_and_reload_profile()
        ret = func(*args, **kwargs)
        return ret
    return _check_profile

class AccountLines():
    @check_profile
    def __init__(self, titles, timestamp, username):
        self.class_dict = get_class_dict()
        self.primary_column_name = get_primary_column_name()
        for title in titles:
            if title not in self.class_dict:
                raise Exception('invalid column name: %s, %s' % (title, self.class_dict))
        if self.primary_column_name not in titles:
            raise Exception('no primary column: %s' % self.primary_column_name)
        self.titles = titles
        self.lines = []
        self.timestamp = timestamp
        self.username = username
    def add_line(self, values):
        column_objs = []
        for title in self.titles:
            value = values.pop(0)
            column_class = self.class_dict[title]
            if not value and column_class.get_name() == self.primary_column_name:
                raise Exception('primary key %s should not be empty' % self.primary_column_name)
            else:
                column_obj = column_class(value)
                column_objs.append(column_obj)
        self.lines.append(column_objs)
    def _insert(self, keypairs):
        logging.debug('insert: %s' % keypairs)
        write_log(keypairs['_id'], self.timestamp, self.username, 'insert', keypairs)
        ret = accounts_collection.insert(keypairs)
    def create_account(self):
        for column_objs in self.lines:
            keypairs = {}
            for column_obj in column_objs:
                value = column_obj.get_value()
                name = column_obj.get_name()
                if name == self.primary_column_name:
                    name = '_id'
                keypairs.update({name: value})
            self._insert(keypairs)
    def _update(self, primary, keypairs):
        logging.debug('update: %s %s' % (primary, keypairs))
        write_log(primary['_id'], self.timestamp, self.username, 'update', keypairs)
        ret = accounts_collection.update(primary, {'$set': keypairs})
    def update_account(self):
        for column_objs in self.lines:
            keypairs = {}
            primary = None
            for column_obj in column_objs:
                name = column_obj.get_name()
                value = column_obj.get_value()
                if name == self.primary_column_name:
                    primary = {'_id': value}
                else:
                    keypairs.update({name: value})
            assert primary
            self._update(primary, keypairs)
    def _delete(self, primary):
        logging.debug('delete: %s' % primary)
        write_log(primary['_id'], self.timestamp, self.username, 'delete', primary)
        ret = accounts_collection.remove(primary)
    def delete_account(self):
        primary = None
        for column_objs in self.lines:
            for column_obj in column_objs:
                name = column_obj.get_name()
                if name == self.primary_column_name:
                    value = column_obj.get_value()
                    primary = {'_id': value}
                    break
            assert primary
            self._delete(primary)

@check_profile
def do_search(params):
    all_classes = get_all_classes()
    class_dict = get_class_dict()
    primary_column_name = get_primary_column_name()
    result = {}
    result['titles'] = all_classes
    keypairs = {}
    for param in params:
        name = param['name']
        class_type = class_dict[name]
        value = class_type.get_search_value(param)
        if name == primary_column_name:
            name = '_id'
        if value:
            keypairs.update({name: value})
    items = accounts_collection.find(keypairs)
    lines = []
    for item in items:
        columns = []
        primary_key = item['_id']
        for name in all_classes:
            class_type = class_dict[name]
            if name == primary_column_name:
                name = '_id'
            if name in item:
                html_string = class_type.get_html_string(\
                    item[name])
            else:
                html_string = ''
            columns.append({'html_string': html_string})
        line = {'primary_key': primary_key, 'columns': columns}
        lines.append(line)
    result['lines'] = lines
    return result

@check_profile
def generate_csv(params):
    class_dict = get_class_dict()
    primary_column_name = get_primary_column_name()
    all_classes = get_all_classes()
    keypairs = {}
    for param in params:
        name = param['name']
        class_type = class_dict[name]
        value = class_type.get_search_value(param)
        if name == primary_column_name:
            name = '_id'
        if value:
            keypairs.update({name: value})
    items = accounts_collection.find(keypairs)
    with TemporaryFile() as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(all_classes)
        for item in items:
            csv_columns =[]
            primary_key = item['_id']
            for name in all_classes:
                class_type = class_dict[name]
                if name == primary_column_name:
                    name = '_id'
                if name in item:
                    csv_string = class_type.get_csv_string(item[name])
                else:
                    csv_string = default_csv_string
                csv_columns.append(csv_string)
            csv_writer.writerow(csv_columns)
        f.seek(0)
        lines = f.read()
    return lines

@check_profile
def do_search_and_run_script(params, script_name):
    class_dict = get_class_dict()
    primary_column_name = get_primary_column_name()
    all_classes = get_all_classes()
    keypairs = {}
    for param in params:
        name = param['name']
        class_type = class_dict[name]
        value = class_type.get_search_value(param)
        if name == primary_column_name:
            name = '_id'
        if value:
            keypairs.update({name: value})
    items = accounts_collection.find(keypairs)
    f = TemporaryFile()
    for item in items:
        primary_key = item['_id']
        csv_columns = []
        for name in all_classes:
            class_type = class_dict[name]
            if name == primary_column_name:
                name = '_id'
            if name in item:
                csv_string = class_type.get_csv_string(item[name], escape=True)
            else:
                csv_string = default_csv_string
            csv_columns.append(csv_string)
            line = default_csv_delimiter.join(csv_columns)
            line = '%s\n' % line
        f.write(line)
    f.seek(0)
    body = get_script_body_by_name(script_name)
    awk_filename = '/tmp/account_tracking_%s' % uuid4()
    with open(awk_filename, 'w') as f_awk:
        f_awk.write(body)
    args = "awk -F '%s' -v _empty=%s -f %s" % \
        (default_csv_delimiter, default_csv_string, awk_filename)
    index = 1
    for name in all_classes:
        v = '-v %s=%d' % (name, index)
        args = "%s %s" % (args, v)
        index += 1
    p = Popen(args, stdin=f, stdout=PIPE, stderr=STDOUT, shell=True)
    stdout = p.communicate(timeout=awk_timeout)[0]
    os.remove(awk_filename)
    graphs = []
    graph = None
    output_lines = stdout.split('\n')
    for output_line in output_lines:
        output_line = output_line.strip()
        if not output_line:
            continue
        k, v = output_line.split(':')
        k = k.strip()
        v = v.strip()
        if k == graph_name_key:
            if graph:
                assert graph_type_key in graph
                graphs.append(graph)
            graph = {}
            graph[graph_name_key] = v
            graph[graph_members_key] = []
        elif k == graph_type_key:
            graph[graph_type_key] = v
        else:
            member = {'name': k, 'value': v}
            graph[graph_members_key].append(member)
    if graph:
        assert graph_type_key in graph
        graphs.append(graph)
    return graphs

def get_columns(primary_key=None):
    if not primary_key:
        return get_columns_skeleton()
    else:
        return get_columns_by_key(primary_key)

@check_profile
def get_columns_by_key(primary_key):
    all_classes = get_all_classes()
    primary_column_name = get_primary_column_name()
    class_dict = get_class_dict()
    columns = []
    item = accounts_collection.find_one({'_id': primary_key})
    for name in all_classes:
        class_type = class_dict[name]
        if name == primary_column_name:
            value = item['_id']
        elif name in item:
            value = item[name]
        else:
            value = None
        column = class_type.get_column_by_value(value)
        columns.append(column)
    return columns

@check_profile
def get_columns_skeleton():
    all_classes = get_all_classes()
    class_dict = get_class_dict()
    columns = []
    for name in all_classes:
        class_type = class_dict[name]
        column = class_type.get_column_skeleton()
        columns.append(column)
    return columns

@check_profile
def set_columns(columns, username, timestamp):
    class_dict = get_class_dict()
    primary_column_name = get_primary_column_name()
    keypairs = {}
    condition = None
    for column in columns:
        name = column['name']
        class_type = class_dict[name]
        value = class_type.get_value_by_column(column)
        if name == primary_column_name:
            condition = {'_id': value}
        else:
            keypairs.update({name: value})
    assert condition
    write_log(condition['_id'], timestamp, username, 'edit', keypairs)
    accounts_collection.update(condition, keypairs)

def get_scripts():
    items = scripts_collection.find()
    scripts = []
    for item in items:
        scripts.append(item['_id'])
    return scripts

def upload_script(script_filename, script_name):
    with open(script_filename, 'r') as f:
        body = f.read()
    ret = scripts_collection.insert({'_id': script_name, 'body': body})
    logging.info('upload script: %s %s %s' % (script_filename, script_name, unicode(ret)))

def delete_script(script_name):
    ret = scripts_collection.remove({'_id': script_name})
    logging.info('delete script: %s %s' % (script_name, unicode(ret)))

def get_script_body_by_name(script_name):
    ret = scripts_collection.find_one({'_id': script_name})
    return ret['body']

@check_profile
def get_primary_name():
    return get_primary_column_name()

def get_versions(primary_key, limit, skip):
    version_collection = db[primary_key]
    items = version_collection.find().sort('_id', DESCENDING).skip(skip).limit(limit)
    versions = []
    for item in items:
        version = {}
        version['raw_date'] = item['_id']
        version['date'] = make_timestamp(item['_id'])
        version['username'] = item['username']
        version['action'] = item['action']
        version['summary'] = json.dumps(item['body'], indent=2).replace('\n', '&#10;').replace('"','')
        versions.append(version)
    return versions

def get_version(primary_key, raw_date):
    version_collection = db[primary_key]
    version = version_collection.find_one({'_id': int(raw_date)})
    if version:
        return json.dumps(version['body'], indent=2).replace('"','')
    else:
        return ''

def get_raw_user(username):
    return user_collection.find_one({'_id': username})

def set_raw_user(username, password_md5):
    user_collection.insert({'_id': username, 'password_md5': password_md5})

def delete_raw_user(username):
    user_collection.remove({'_id': username})

def get_all_usernames():
    items = user_collection.find()
    usernames = []
    for item in items:
        usernames.append(item['_id'])
    return usernames

@check_profile
def get_search_op():
    return search_op

def update_profile(profile_filename):
    with open(profile_filename, 'r') as f:
        file_content = f.read()
    try:
        timestamp = int(time.time())
        profile_collection.insert({'_id': profile_key, 'timestamp': timestamp, 'body': file_content})
    except Exception, e:
        profile_collection.update({'_id': profile_key}, {'timestamp': timestamp, 'body': file_content})

def get_profile():
    item = profile_collection.find_one({'_id': profile_key})
    if item:
        return item['body']
    else:
        return ''
