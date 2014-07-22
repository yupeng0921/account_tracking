#! /usr/bin/env python

class AccountLines():
    def __init__(self, titles):
        pass
    def add_line(self, columns):
        pass
    def create_account(self):
        pass
    def update_account(self):
        pass
    def delete_account(self):
        pass

search_op = [
    { 'name': 'AccountId',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] },
    { 'name': 'Email',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] },
    { 'name': 'CustomerName',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] },
    { 'name': 'Segment',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] },
    { 'name': 'AccountManager',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] },
    { 'name': 'KnownIssues',
      'type': 'multichoice',
      'choices': ['issue A', 'issue B', 'issue C']
      },
    { 'name': 'OpenIssues',
      'type': 'text',
      'options': ['equal', 'contain', 'equal ignore case', 'contain ignore case'] }
    ]

def do_search(params):
    result = {}
    result['titles'] = [
        'AccountId', 'EMail', 'CustomerName', 'Segment', 
        'AccountManager', 'KicooffMeeting', 'InternetTrafficRequired',
        'ExceptionApproved', 'IPRecord', 'ICPRecord1', 'ICPRecord2', 'ICPRecord3',
        'Usage', 'KnownIssues', 'OpenIssues'
        ]
    lines = []
    columns = [
        {'html_string': '111'},
        {'html_string':'alice@abc.com'},
        {'html_string': 'alice'},
        {'html_string': '', },
        {'html_string': 'bob'}
        ]
    line = {'primary_key': 'alice@abc.com', 'columns': columns}
    lines.append(line)
    columns = [
        {'html_string': '222'},
        {'html_string':'cindy@def.com'},
        {'html_string': 'cindy'},
        {'html_string': '', },
        {'html_string': 'dany'},
        {'html_string': '2014/09/11'},
        {'html_string': 'yes'},
        {'html_string': 'no'},
        {'html_string': '2014/10/20'},
        {'html_string': ''},
        {'html_string': ''},
        {'html_string': '2014/10/23'},
        {'html_string': '20'},
        {'html_string': '<p>Issue A</p><p>Issue B</p>'},
        {'html_string': '<p>abc</p><p>def</p><p>gh</p>'}
        ]
    line = {'primary_key': 'cindy@def.com', 'columns': columns}
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
    column = {}
    column['name'] = 'AccountId'
    column['type'] = 'text'
    column['value'] = '1234'
    columns.append(column)
    column = {}
    column['name'] = 'EMail'
    column['type'] = 'text'
    column['value'] = 'cindy@abc.com'
    columns.append(column)
    column = {}
    column['name'] = 'CustomerName'
    column['type'] = 'text'
    column['value'] = 'abc company'
    columns.append(column)
    column = {}
    column['name'] = 'Segment'
    column['type'] = 'text'
    column['value'] = 'segment fault'
    columns.append(column)
    column = {}
    column['name'] = 'AccountManager'
    column['type'] = 'text'
    column['value'] = 'dany'
    columns.append(column)
    column = {}
    column['name'] = 'KickoffMeeting'
    column['type'] = 'text'
    column['value'] = '2014/03/19'
    columns.append(column)
    column = {}
    column['name'] = 'InternettraficRequired'
    column['type'] = 'multichoice'
    choices = []
    choice = {'name': 'require', 'checked': 'true'}
    choices.append(choice)
    column['choices'] = choices
    columns.append(column)
    column = {}
    column['name'] = 'Exception'
    column['type'] = 'multichoice'
    choices = []
    choice = {'name': 'require', 'checked': 'true'}
    choices.append(choice)
    column['choices'] = choices
    columns.append(column)
    column = {}
    column['name'] = 'IPRecord'
    column['type'] = 'text'
    column['value'] = '2014/04/20'
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord1'
    column['type'] = 'text'
    column['value'] = ''
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord2'
    column['type'] = 'text'
    column['value'] = ''
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord3'
    column['type'] = 'text'
    column['value'] = ''
    columns.append(column)
    column = {}
    column['name'] = 'Usage'
    column['type'] = 'text'
    column['value'] = ''
    columns.append(column)
    column = {}
    column['name'] = 'KnownIssues'
    column['type'] = 'multichoice'
    choices = []
    choice = {'name': 'Issue A', 'checked': 'true'}
    choices.append(choice)
    choice = {'name': 'Issue B', 'checked': ''}
    choices.append(choice)
    choice = {'name': 'Issue C', 'checked': 'true'}
    choices.append(choice)
    column['choices'] = choices
    columns.append(column)
    column = {}
    column['name'] = 'OpenIssues'
    column['type'] = 'textarea'
    column['value'] = 'abc\ndef\nmn'
    columns.append(column)
    return columns

def get_columns_skeleton():
    columns = []
    column = {}
    column['name'] = 'AccountId'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'EMail'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'CustomerName'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'Segment'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'AccountManager'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'KickoffMeeting'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'InternettraficRequired'
    column['type'] = 'multichoice'
    columns.append(column)
    column = {}
    column['name'] = 'Exception'
    column['type'] = 'multichoice'
    columns.append(column)
    column = {}
    column['name'] = 'IPRecord'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord1'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord2'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'ICPRecord3'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'Usage'
    column['type'] = 'text'
    columns.append(column)
    column = {}
    column['name'] = 'KnownIssues'
    column['type'] = 'multichoice'
    columns.append(column)
    column = {}
    column['name'] = 'OpenIssues'
    column['type'] = 'textarea'
    columns.append(column)
    return columns

def set_columns(columns):
    print(columns)
