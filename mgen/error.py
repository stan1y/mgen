"""
MGEN: Exception definitions
"""

import json
import logging
import tornado.web

import mgen.util

log = logging.getLogger(__name__)

class MGENException(tornado.web.HTTPError):
    '''Base exception class for MGEN errors'''
    
    def __init__(self, status_code=None, log_message=None, report=False, *args):
        if status_code == None:
            self.status_code = self.http_status()
        else:
            self.status_code = status_code
        self.log_message = log_message
        self.report = report
        self.args = args
        self.reason = None
        self.data_map = {
            'exception': self.__class__.__name__
        }
        
    def http_status(self):
        '''Get this exception HTTP status code'''
        return 0
        
    def data(self):
        return self.data_map

    def format(self):
        return json.dumps(self.data(), cls=mgen.util.JSONEncoder)

    def append(self, key, value):
        self.data_map[key] = value

    def __str__(self):
        return '%d: %s' % (self.http_status(), self.json())
    
    def describe(self, msg):
        self.append('reason', msg)
        self.reason = msg
        return self
        
class InternalError(MGENException):
    def http_status(self):
        '''500: Internal Error'''
        return 500
        
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
        
class Forbidden(MGENException):
    def http_status(self):
        '''403 Forbidden'''
        return 403
        
class NotFound(MGENException):
    def http_status(self):
        '''404 Not Found'''
        return 404
        
class Conflict(MGENException):
    def http_status(self):
        '''409 Conflict'''
    
    def duplicate_object(self, col_name):
        '''Indicates that a conflict was in duplicated object in a collection'''
        self.describe('duplicate object in collection %s' % col_name)
        return self