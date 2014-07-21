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
    line = [
        {'html_string': '111'},
        {'html_string':'alice@abc.com'},
        {'html_string': 'alice'},
        {'html_string': '', },
        {'html_string': 'bob'}
        ]
    lines.append(line)
    line = [
        {'html_string': '222'},
        {'html_string':'cindy@abc.com'},
        {'html_string': 'cindy'},
        {'html_string': '', },
        {'html_string': 'dany'}
        ]
    lines.append(line)
    result['lines'] = lines
    return result
