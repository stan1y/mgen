import os
import sys
import re
import urllib

import mgen.error
import tornado.template

template_types = {
    'builtin': 'Built-in'
}


class Template(object):
    '''Generic templte class delegating rendering to specific implementations'''
    
    def __init__(self, ttype, body):
        self.type = ttype
        self.body = body
        
    def render(self, params = {}):
        if self.type == 'builtin':
            return tornado.template.Template(self.body).generate(*params)
            
        raise mgen.error.InternalError().describe('Unknown template type: %s' % self.type)