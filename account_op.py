#! /usr/bin/env python

import yaml
import logging
import os
from pymongo import MongoClient
from column_op import g_class_dict, g_all_classes, g_searchable_classes, g_primary_column_name

current_file_full_path = os.path.split(os.path.realpath(__file__))[0]
with open(os.path.join(current_file_full_path, 'conf.yaml'), 'r') as f:
    conf = yaml.safe_load(f)

mongodb_addr = conf['mongodb_addr']
mongodb_port = conf['mongodb_port']
db_name = conf['db_name']
account_collection = conf['account_collection']

client = MongoClient(mongodb_addr, mongodb_port)
db = client[db_name]
g_collection = db[account_collection]

class AccountLines():
    class_dict = g_class_dict
    primary_column_name = g_primary_column_name
    collection = g_collection
    def __init__(self, titles):
        for title in titles:
            if title not in self.class_dict:
                raise Exception('invalid column name: %s' % title)
        if self.primary_column_name not in titles:
            raise Exception('no primary column: %s' % self.primary_column_name)
        self.titles = titles
        self.lines = []
    def add_line(self, values):
        column_objs = []
        for title in self.titles:
            value = values.pop(0)
            column_class = self.class_dict[title]
            column_obj = column_class(value)
            column_objs.append(column_obj)
        self.lines.append(column_objs)
    def _insert(self, keypairs):
        logging.debug('insert: %s' % keypairs)
        self.collection.insert(keypairs)
    def create_account(self):
        for column_objs in self.lines:
            keypairs = {}
            for column_obj in column_objs:
                value = column_obj.get_value()
                name = column_obj.get_name()
                if name == g_primary_column_name:
                    name = '_id'
                keypairs.update({name: value})
            self._insert(keypairs)
    def _update(self, primary, keypairs):
        logging.debug('update: %s %s' % (primary, keypairs))
        self.collection.update(primary, {'$set': keypairs})
    def update_account(self):
        for column_objs in self.lines:
            keypairs = {}
            primary = None
            for column_obj in column_objs:
                name = column_obj.get_name()
                value = column_obj.get_value()
                if name == g_primary_column_name:
                    primary = {'_id': value}
                else:
                    keypairs.update({name: value})
            assert primary
            self._update(primary, keykpairs)
    def _delete(self, primary):
        logging.debug('delete: %s' % primary)
        self.collection.remove(primary)
    def delete_account(self):
        primary = None
        for column_objs in self.lines:
            for column_obj in column_objs:
                name = column_obj.get_name()
                if name == g_primary_column_name:
                    value = column_obj.get_value()
                    primary = {'_id': value}
                    break
            assert primary
            self._delete(primary)

search_op = []
for class_name in g_searchable_classes:
    class_type = g_class_dict[class_name]
    op = class_type.get_search_op()
    search_op.append(op)

def do_search(params):
    result = {}
    result['titles'] = g_all_classes
    keypairs = {}
    for param in params:
        name = param['name']
        class_type = g_class_dict[name]
        value = class_type.get_search_value(param)
        if name == g_primary_column_name:
            name = '_id'
        if value:
            keypairs.update({name: value})
    items = g_collection.find(keypairs)
    lines = []
    for item in items:
        columns = []
        primary_key = item['_id']
        for name in g_all_classes:
            class_type = g_class_dict[name]
            if name == g_primary_column_name:
                name = '_id'
            if name in item:
                html_string = class_type.get_html_string(item[name])
            else:
                html_string = ''
            columns.append({'html_string': html_string})
        line = {'primary_key': primary_key, 'columns': columns}
        lines.append(line)
    result['lines'] = lines
    return result

def get_columns(primary_key=None):
    if not primary_key:
        return get_columns_skeleton()
    else:
        return get_columns_by_key(primary_key)

def get_columns_by_key(primary_key):
    columns = []
    item = g_collection.find_one({'_id': primary_key})
    for name in g_all_classes:
        class_type = g_class_dict[name]
        if name == g_primary_column_name:
            value = item['_id']
        elif name in item:
            value = item[name]
        else:
            value = ''
        column = class_type.get_column_by_value(value)
        columns.append(column)
    return columns

def get_columns_skeleton():
    columns = []
    for name in g_all_classes:
        class_type = g_class_dict[name]
        column = class_type.get_column_skeleton()
        columns.append(column)
    return columns

def set_columns(columns):
    keypairs = {}
    condition = None
    for column in columns:
        name = column['name']
        class_type = g_class_dict[name]
        value = class_type.get_value_by_column(column)
        if name == g_primary_column_name:
            condition = {'_id': value}
        else:
            keypairs.update({name:value})
    assert condition
    g_collection.update(condition, {'$set': keypairs})
