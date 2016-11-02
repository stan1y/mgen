"""
MGEN: Exception definitions
"""

import json
import logging
import tornado.web

log = logging.getLogger(__name__)

class MGENException(tornado.web.HTTPError):
    '''Base exception class for MGEN errors'''
    
    def __init__(self, status_code=None, msg=None, report=False, *arg):
        if code is None:
            self.status_code = self.http_status()
        else:
            self.status_code = code
        self.msg = msg
        self.report = report
        self.data = {
            'exception': self.__class__.__name__
        }
        
    def http_status(self):
        '''Get this exception HTTP status code'''
        return 500
        
    def append(self, key, val):
        '''Add error info pair to this exception. Return self.'''
        self.data[key] = val
        return self
        
    def msg(self, txt):
        return self.append('error', txt)
        
class ServiceUnavailable(MGENException):
    def http_status(self):
        '''503: Service Unavailable''' 
        return 503
        
class BadRequest(MGENException):
    def http_status(self):
        '''400 Bad Request'''
        return 400
        
class Unauthorized(MGENException):
    def http_status(self):
        '''401 Unauthorized'''
        return 401