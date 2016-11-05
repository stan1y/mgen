"""
MGEN Rest API Inteface classes
"""

import zlib
import uuid
import json
import functools
import logging
import traceback

import tornado
import tornado.web
import tornado.template

import sqlalchemy
import sqlalchemy.exc

import mgen.util
import mgen.error
import mgen.model

from mgen.model import session

from mgen.web import BaseRequestHandler
from mgen.web.auth import authenticated


log = logging.getLogger(__name__)


def jsonify(method):
    """Decorate methods with this to output valid JSON data."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        answer = method(self, *args, **kwargs)
        if answer:
            if self._finished:
                log.warn('trying to write JSON on finished request.')
            else:
                self.set_header('Content-Type', 'application/json')
                self.write(json.dumps(answer, cls=mgen.util.JSONEncoder))
    return wrapper


class BaseAPIRequestHandler(BaseRequestHandler):
    """Base class for API requests processing"""
    
    def write_error(self, status_code, **kwargs):
        '''Override default error rendering to report JSON for API calls'''
        ex_type, ex, ex_trsbk = kwargs['exc_info']
        if not ex or not isinstance(ex, mgen.error.MGENException):
            return super().write_error(status_code, **kwargs)
                
        ex.append('traceback', traceback.format_exception(ex_type, ex, ex_trsbk))
        self.set_header('Content-Type', 'application/json')
        self.write(ex.format())
    
    @property
    def request_params(self):
        '''Read and validate client JSON data for current request'''

        if hasattr(self, '__cached_request_params'):
            return self.__cached_request_params

        content_type = self.request.headers.get('Content-Type')
        body = self.request.body
        if content_type == 'application/lzg+json':
            log.debug('decompressing request params')
            try:
                body = zlib.decompress(body)
            except zlib.error as ex:
                raise mgen.error.BadRequest().describe("can't decompress body. %s" % ex)
                
        try:
            self.__cached_request_params = json.loads(body.decode('utf-8'))
            return self.__cached_request_params
        except ValueError:
            raise mgen.error.BadRequest().describe('invalid json received')


def collection_name(model):
    return model.__tablename__ + "s"


class GenericModelHandler(BaseAPIRequestHandler):
    """Generic REST API handler for models access with paging, sorting, filtering, etc"""
    
    @property
    def page_arguments(self):
        """Returns tuple of pageing arguments of sent by client"""
            
        #check that all three fields are present
        if 'page' in self.request.arguments:
            page = int(self.get_argument('page'))
        else:
            return False, 0, 0, 0
        if 'limit' in self.request.arguments:
            limit = int(self.get_argument('limit'))
        else:
            return False, 0, 0, 0
        if 'start' in self.request.arguments:
            start = int(self.get_argument('start'))
        else:
            return False, 0, 0, 0    
        
        return True, page, start, limit
        
    def sort(self, model, query):
        '''Server-side sorting support'''
        if not 'sort' in self.request.arguments:
            log.debug('no sort arguments')
            return query
        if not issubclass(model, mgen.model.SortModelMixin):
            log.debug('not a sorted instance')
            return query
        
        log.debug('sorting query for %s' % repr(model))
        return model.sort(query, self.get_argument('sort'))
    
    def filter(self, model, query):
        '''Server side filtering support'''
        if not 'filter' in self.request.arguments:
            log.debug('no filter arguments')
            return query
        if not issubclass(model, mgen.model.FilterModelMixin):
            log.debug('not a sorted instance')
            return query

        log.debug('filtering query for %s' % repr(model))
        return model.filter(query, self.get_argument('filter'))

    def range(self, model, query):
        '''Server side range query support'''
        if not 'range' in self.request.arguments:
            log.debug('no range arguments')
            return query
        if not issubclass(model, mgen.model.RangeModelMixin):
            log.debug('not a sorted instance')
            return query

        log.debug('range query for %s' % repr(model))
        return model.range(query, self.get_argument('range'))

    def fetch(self, query, page_args, obj_id=None, collection="objects", **kwargs):
        """Generic get method for models with paging support and conversion to json"""
        if obj_id != None:
            # get object by id
            obj = query.filter_by(id=obj_id).first()
            if obj == None:
                raise mgen.error.NotFound().describe('object with id "{0}" was not found in "{1}"'.format(
                    obj_id, collection))
            return {
                "total": 1,
                collection: [obj]
            }
        else:
            # get list of arguments
            should_page, page_no, start, limit = page_args
            if should_page:
                query = query.offset(start).limit(limit)
            # perform query and convert results to json
            objects = [obj.to_json() for obj in query]
            return {
                "page": page_no,
                "limit": limit,
                "start": start,
                "total": len(objects),
                collection: objects
            }
            
    def restfull_get(self, model, oid=None):
        """RESTfull GET object or list of objects"""
        log.debug('REST GET {0}{1}'.format(model, 
                                           ", oid: %s" % oid if oid else ""))
        return self.fetch(session().query(model), 
                          self.page_arguments,
                          obj_id=oid,
                          collection=collection_name(model)
                          )
                          
    def restfull_post(self, model):
        """RESTfull POST to create a new object"""
        params = self.request_params
        log.debug('REST POST {0}, {1} properties'.format(model, len(params)))
        new_inst = model(id = uuid.uuid4())
        for key in params:
            if not hasattr(new_inst, key):
                raise mgen.error.BadRequest().describe('no such property: ' + key)
            val = params[key]
            log.debug("- %s=%s" % (key, val))
            setattr(new_inst, key, val)
        return new_inst
    
    def commit_changes(self, s = None):
        cls_name = self.__class__.__name__
        try:
            # use default session if param was omitted
            if s is None: s = session()
            s.commit()
            log.debug("commited changes to session %s" % s)
        
        except sqlalchemy.exc.IntegrityError as ie:
            raise mgen.error.Conflict().duplicate_object(
                'Failed to create new object in "{0}". Error: {1}'.format(
                cls_name, ie)
            )
            
        except Exception as ex:
            raise mgen.error.BadRequest().describe(
                'Failed to create new object in "{0}". Error: {1}'.format(
                cls_name, ex)
            )

class Profiles(GenericModelHandler):
    """Profiles restfull interface"""
    
    @authenticated
    @jsonify
    def get(self, oid=None):
        """GET list or single profile"""
        return self.restfull_get(mgen.model.Profile, oid)

                          
class Projects(GenericModelHandler):
    """"Projects restfull interface"""
    
    @authenticated
    @jsonify
    def get(self, oid=None):
        """GET list or single project"""
        return self.restfull_get(mgen.model.Project, oid)
        
    @authenticated
    @jsonify
    def post(self, oid=None):
        """POST to create a new project"""
        s = session()
        project = self.restfull_post(mgen.model.Project)
        s.add(project)
        project.members.append(self.current_profile)
        self.commit_changes(s)
        self.set_status(201)
        return self.restfull_get(mgen.model.Project, oid=project.id)
        