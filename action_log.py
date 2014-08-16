#!/usr/bin/env python

import os
import yaml
import json
import boto
from boto.s3.key import Key

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

log_region = conf['log_region']
log_bucket_name = conf['log_bucket_name']

# conn = boto.s3.connect_to_region(log_region)
# log_bucket = conn.get_bucket(log_bucket_name)

def write_log(username, date, action, file_or_string):
    print('%s %s %s' % (username, date, action))
    # valid_action = ('create', 'upload', 'delete', 'edit')
    # if action not in valid_action:
    #     msg = 'invalid action: %s, %s' % (action, valid_action)
    #     raise Exception(msg)
    # key_name = '%s_%s_%s' % (date, username, action)
    # k = Key(log_bucket)
    # if action == 'edit':
    #     k.set_contents_from_string(file_or_string)
    # else:
    #     k.set_contents_from_filename(file_or_string)
