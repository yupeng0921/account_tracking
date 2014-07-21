#! /usr/bin/env python

import sys
import os
import time
import yaml
import logging
from pymongo import MongoClient
from daemon import runner

from account_op import AccountLines

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
message_collection = conf['message_collection']
message_magic_key = conf['message_magic_key']
daemon_log_file = conf['daemon_log_file']
daemon_interval = conf[u'daemon_interval']
daemon_stdin_path = conf[u'daemon_stdin_path']
daemon_stdout_path = conf[u'daemon_stdout_path']
daemon_stderr_path = conf[u'daemon_stderr_path']
daemon_pidfile_path = conf[u'daemon_pidfile_path']
daemon_pidfile_timeout = conf[u'daemon_pidfile_timeout']

def update_information(collection, info):
    condition = {'_id': message_magic_key}
    collection.update(condition, {'$set': {'info': info}})

def set_status(collection, status):
    condition = {'_id': message_magic_key}
    collection.update(condition, {'$set': {'status': status}})

def do_job(action, fullpath, collection):
    if action not in ('create', 'update', 'delete'):
        raise Exception('invlaid action: %s' % action)
    f = open(fullpath, 'r')
    titles = f.next().split(',')
    titles = [title.strip() for title in titles]
    account_lines = AccountLines(titles)
    varify_errors = []
    line_number = 2
    for eachline in f:
        columns = eachline.split(',')
        columns = [column.strip() for column in columns]
        try:
            account_lines.add_line(columns)
        except Exception, e:
            varify_errors.append(line_number)
        line_number += 1
    info = 'verified: %d failed: %s' % (line_number, unicode(varify_errors))
    update_information(collection, info)
    if varify_errors:
        set_status(collection, 'idle')
        return
    if action == 'create':
        account_lines.create_account()
    elif action == 'update':
        account_lines.update_account()
    elif action == 'delete':
        account_lines.delete_account()
    info = '%s complete' % action
    update_information(collection, info)

class RunTask():
    def __init__(self, stdin_path, stdout_path, stderr_path, pidfile_path, pidfile_timeout):
        self.stdin_path = stdin_path
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.pidfile_path = pidfile_path
        self.pidfile_timeout = pidfile_timeout
    def run(self):
        format = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
        datefmt='%Y-%m-%d %H:%M:%S'
        level = logging.INFO
        logging.basicConfig(filename=daemon_log_file, level=level, format=format, datefmt=datefmt)
        client = MongoClient(mongodb_addr, mongodb_port)
        db = client[db_name]
        collection = db[message_collection]
        try:
            collection.insert({'_id': message_magic_key, 'status': 'idle'})
        except Exception, e:
            pass
        logging.info('come into loop')
        while True:
            job = collection.find_one({'_id': message_magic_key})
            if 'status' not in job:
                logging.error('invalid job: %s' % unicode(job))
                time.sleep(daemon_interval)
                continue
            if job['status'] == 'idle':
                time.sleep(daemon_interval)
                continue
            logging.info('job: %s' % unicode(job))
            if 'action' not in job or 'fullpath' not in job:
                logging.error('invalid job: %s' % unicode(job))
                time.sleep(daemon_interval)
                continue
            action = job['action']
            fullpath = job['fullpath']
            try:
                do_job(action, fullpath, collection)
            except Exception, e:
                logging.error('job failed: %s' % unicode(e))
            try:
                os.remove(fullpath)
            except Exception, e:
                pass
            set_status(collection, 'idle')

task = RunTask(daemon_stdin_path, daemon_stdout_path, daemon_stderr_path, daemon_pidfile_path, daemon_pidfile_timeout)
daemon_runner = runner.DaemonRunner(task)
daemon_runner.do_action()
