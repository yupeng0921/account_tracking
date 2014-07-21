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
        {'html_string': 'dany'}
        ]
    line = {'primary_key': 'cindy@def.com', 'columns': columns}
    lines.append(line)
    result['lines'] = lines
    return result

def get_item(primary_key):
    item = []
    column = {}
    column['name'] = 'AccountId'
    column['type'] = 'text'
    column['value'] = '1234'
    item.append(column)
    column = {}
    column['name'] = 'EMail'
    column['type'] = 'text'
    column['value'] = 'cindy@abc.com'
    item.append(column)
    column = {}
    column['name'] = 'CustomerName'
    column['type'] = 'text'
    column['value'] = 'abc company'
    item.append(column)
    column = {}
    column['name'] = 'Segment'
    column['type'] = 'text'
    column['value'] = 'segment fault'
    item.append(column)
    column = {}
    column['name'] = 'AccountManager'
    column['type'] = 'text'
    column['value'] = 'dany'
    item.append(column)
    column = {}
    column['name'] = 'KickoffMeeting'
    column['type'] = 'text'
    column['value'] = '2014/03/19'
    item.append(column)
    column = {}
    column['name'] = 'InternettraficRequired'
    column['type'] = 'multichoice'
    choices = []
    choice = {'name': 'require', 'checked': 'true'}
    choices.append(choice)
    column['choices'] = choices
    item.append(column)
    return item
