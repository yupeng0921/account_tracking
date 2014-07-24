#! /usr/bin/env python

import yaml
import json
import logging
from new import classobj

class BasicColumn():
    @classmethod
    def get_search_op(cls):
        raise Exception('child should overwrite it')
    @classmethod
    def get_search_value(cls, inp):
        raise Exception('child should overwrite it')
    @classmethod
    def get_html_string(cls, inp):
        raise Exception('child should overwrite it')
    @classmethod
    def get_column_by_value(cls, value):
        raise Exception('child should overwrite it')
    @classmethod
    def get_column_skeleton(cls):
        raise Exception('child should overwrite it')
    @classmethod
    def get_value_by_column(cls, column):
        raise Exception('child should overwrite it')
    @classmethod
    def get_name(cls):
        raise Exception('child should overwrite it')
    def __init__(self):
        raise Exception('child should overwrite it')
    def get_value(self):
        raise Exception('child should overwrite it')

class StringColumn(BasicColumn):
    export_type = 'text'
    varify_methods = []
    @classmethod
    def get_search_op(cls):
        op = {}
        op['name'] = cls.__name__
        op['type'] = cls.export_type
        op['options'] = ['equal']
        return op
    @classmethod
    def get_search_value(cls, inp):
        return inp['text'].strip()
    @classmethod
    def get_html_string(cls, inp):
        return inp
    @classmethod
    def get_column_by_value(cls, value):
        column = cls.get_column_skeleton()
        column['value'] = value
        return column
    @classmethod
    def get_column_skeleton(cls):
        column = {}
        column['name'] = cls.__name__
        column['type'] = cls.export_type
        return column
    @classmethod
    def get_value_by_column(cls, column):
        value = column['value'].strip()
        cls._varify_value(value)
        return value
    @classmethod
    def get_name(cls):
        return cls.name
    @classmethod
    def _varify_value(cls, value):
        for param, method in cls.varify_methods:
            ret = method(value, param)
            if not ret:
                raise Exception('invalid value: %s %s %s' % \
                                    (value, param, method))
    def __init__(selv, value):
        self._varify_value(value)
        self.value = value
    def get_value(self):
        return self.value

def varify_string_pattern(value, param):
    return True

def varify_string_max(value, param):
    return True

def varify_string_min(value, param):
    return True

def get_string_class(name, p):
    varify_methods = []
    if 'Pattern' in p:
        varify_methods.append((p['Pattern'], varify_string_pattern))
    if 'Max' in p:
        varify_methods.append((p['Max'], varify_string_max))
    if 'Min' in p:
        varify_methods.append((p['Min'], varify_string_min))
    cls = classobj(str(name), (StringColumn,), {'varify_methods': varify_methods})
    return cls

g_class_dict = {}
g_all_classes = []
g_searchable_classes = []
g_primary_column_name = None

with open('profile.json') as f:
    profile = json.load(f)

for name in profile:
    p = profile[name]
    t = p['Type']
    if t == 'String':
        cls = get_string_class(name, p)
    else:
        raise Exception('unsupport type: %s %s' % (name, t))
    g_class_dict[name] = cls
    if 'IsPrimary' in p:
        assert not g_primary_column_name
        g_primary_column_name = name

assert g_primary_column_name

with open('sequence.json') as f:
    g_all_classes = json.load(f)

g_searchable_classes = g_all_classes
