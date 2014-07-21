#! /usr/bin/env python

class BasicItem():
    def __init__(self, input_string):
        if not self._valid_input(input_string):
            raise Exception('invalid input string: %s' % input_string)
        self.value = self._set_value(input_string)
    def get_value(
    def _valid_input(input_string):
        pass
    def _set_value(input_string):
        pass
