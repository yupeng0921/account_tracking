#! /usr/bin/env python

import yaml
import json
import logging
from new import classobj

class BasicColumn():
    @classmethod
    def get_search_op(cls):
        """
        :return the options dict
        op['name'] = ColumnName
        op['type'] = text
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_search_value(cls, inp):
        """
        :type inp: dict
        :param inp: search value, input by user

        :rtype: string or dict
        :return: parten can be used for mongodb find command
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_html_string(cls, inp):
        """
        :type inp: string or dict or list
        :param inp: value stored in mongodb

        :rtype: string
        :return: can be suitable shown in format html
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_csv_string(cls, inp):
        """
        :type inp: string or dict or list
        :param inp: data stored in mongodb

        :rtype: string
        :return: can be suitable shown in csv file
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_column_by_value(cls, value):
        """
        :type value: string or dict or list
        :param value: data stored in mongodb

        :rtype: dict
        :return: a dict include name, type and value
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_column_skeleton(cls):
        """
        :rtype: dict
        :return: a dict include name and type
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_value_by_column(cls, column):
        """
        :type column: dict
        :param column: user input

        :rtype: string or dict or list
        :return: data could be stored to mongodb
        """
        raise Exception('child should overwrite it')
    @classmethod
    def get_name(cls):
        """
        :rtype: string
        :return: column name
        """
        raise Exception('child should overwrite it')
    def __init__(self, value):
        """
        :type value: string
        :param value: user input value from batch mode
        """
        raise Exception('child should overwrite it')
    def get_value(self):
        """
        :rtype: string or dict or list
        :return: data could be stored to mongodb
        """
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
    def get_csv_string(cls, inp):
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
        return cls.__name__
    @classmethod
    def _varify_value(cls, value):
        for param, method in cls.varify_methods:
            ret = method(value, param)
            if not ret:
                raise Exception('invalid value: %s %s %s' % \
                                    (value, param, method))
    def __init__(self, value):
        self._varify_value(value)
        self.value = value
    def get_value(self):
        return self.value

class BooleanColumn(BasicColumn):
    export_type = 'text'
    true_values = ('True', 'Yes', 'yes', 'Y', 'y')
    false_values = ('False', 'No', 'no', 'N', 'n')
    true_in_db = 'True'
    false_in_db = 'False'
    @classmethod
    def get_search_op(cls):
        raise Exception('not support')
    @classmethod
    def get_search_value(cls, inp):
        raise Exception('not support')
    @classmethod
    def get_html_string(cls, inp):
        return inp
    @classmethod
    def get_csv_string(cls, inp):
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
        value = cls._get_value_from_input(value)
        return value
    @classmethod
    def get_name(cls):
        return cls.name
    @classmethod
    def _get_value_from_input(cls, value):
        if not value:
            return value
        elif value in cls.true_values:
            return cls.true_in_db
        elif value in cls.false_values:
            return cls.false_in_db
        else:
            raise Exception('invalid value for %s: %s' % \
                                (cls.__name__, value))
    def __init__(self, value):
        self.get_value_by_column(value)
        self.value = value
    def get_value(self):
        return self.value

class TimeColumn(BasicColumn):
    export_type = 'text'
    @classmethod
    def get_search_op(cls):
        raise Exception('not support')
    @classmethod
    def get_search_value(cls, inp):
        raise Exception('not support')
    @classmethod
    def get_html_string(cls, inp):
        return inp
    @classmethod
    def get_csv_string(cls, inp):
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
        return cls.__name__
    @classmethod
    def _varify_value(cls, value):
        pass
    def __init__(self, value):
        self._varify_value(value)
        self.value = value
    def get_value(self):
        return self.value

class TimeEventColumn(BasicColumn):
    export_type = 'time_event'
    @classmethod
    def get_search_op(cls):
        raise Exception('not support')
    @classmethod
    def get_search_value(cls, inp):
        raise Exception('not support')

class MultiLineStringColumn(BasicColumn):
    export_type = 'textarea'
    @classmethod
    def get_search_op(cls):
        raise Exception('not support')
    @classmethod
    def get_search_vaue(cls, inp):
        raise Exception('not support')
    @classmethod
    def get_html_string(cls, inp):
        lines = inp.split('\n')
        html = ''
        for line in lines:
            html = '%s<p>%s</p>' % (html, line)
        return html
    @classmethod
    def get_csv_string(cls, inp):
        lines = inp.split('\n')
        csv_string = ' '.join(lines)
        return csv_string
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
        value = column['value']
        return value
    def __init(self, value):
        self.value = value

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

def get_boolean_class(name, p):
    cls = classobj(str(name), (BooleanColumn,), {})
    return cls

def get_time_class(name, p):
    cls = classobj(str(name), (TimeColumn,), {})
    return cls

def get_time_event_class(name, p):
    cls = classobj(str(name), (TimeEventColumn,), {})
    return cls

def get_multilinestring_class(name, p):
    cls = classobj(str(name), (MultiLineStringColumn,), {})
    return cls

g_class_dict = {}
g_primary_column_name = None

with open('profile.json') as f:
    profile = json.load(f)

for name in profile:
    p = profile[name]
    t = p['Type']
    if t == 'String':
        cls = get_string_class(name, p)
    elif t == 'Time':
        cls = get_time_class(name, p)
    elif t == 'TimeEvent':
        cls = get_time_event_class(name, p)
    elif t == 'Boolean':
        cls = get_boolean_class(name, p)
    elif t == 'MultiLineString':
        cls = get_multilinestring_class(name, p)
    else:
        raise Exception('unsupport type: %s %s' % (name, t))
    g_class_dict[name] = cls
    if 'IsPrimary' in p:
        assert not g_primary_column_name
        g_primary_column_name = name

assert g_primary_column_name

with open('sequence.json') as f:
    g_all_classes = json.load(f)

with open('searchable.json') as f:
    g_searchable_classes = json.load(f)
