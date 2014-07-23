#! /usr/bin/env python

import yaml
import logging

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

class AccountId(BasicColumn):
    name = 'AccountId'
    export_type = 'text'
    @classmethod
    def get_search_op(cls):
        op = {}
        op['name'] = cls.name
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
        column['name'] = cls.name
        column['type'] = cls.export_type
        return column
    @classmethod
    def get_value_by_column(cls, column):
        return column['value'].strip()
    @classmethod
    def get_name(cls):
        return cls.name
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value

class EMail(BasicColumn):
    name = 'EMail'
    export_type = 'text'
    @classmethod
    def get_search_op(cls):
        op = {}
        op['name'] = cls.name
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
        column['name'] = cls.name
        column['type'] = cls.export_type
        return column
    @classmethod
    def get_value_by_column(cls, column):
        return column['value'].strip()
    @classmethod
    def get_name(cls):
        return cls.name
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value


class CustomerName(BasicColumn):
    name = 'CustomerName'
    export_type = 'text'
    @classmethod
    def get_search_op(cls):
        op = {}
        op['name'] = cls.name
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
        column['name'] = cls.name
        column['type'] = cls.export_type
        return column
    @classmethod
    def get_value_by_column(cls, column):
        return column['value'].strip()
    @classmethod
    def get_name(cls):
        return cls.name
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value

g_class_dict = {}
g_class_dict['AccountId'] = AccountId
g_class_dict['EMail'] = EMail
g_class_dict['CustomerName'] = CustomerName

g_all_classes = ['AccountId', 'EMail', 'CustomerName']
g_searchable_classes = g_all_classes
g_primary_column_name = 'EMail'
