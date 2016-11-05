"""
MGEN Rest API Inteface classes
"""

import zlib
import uuid
import json
import functools
import logging
import traceback
import datetime

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
        ex_msg = ex.format()
        log.error('Exception: %s' % ex_msg)
        self.write(ex_msg)
    
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

    def fetch(self, query, page_args, single=None, collection="objects", **kwargs):
        """Generic get method for models with paging support and conversion to json"""
        if single != None:
            # get object by id
            k, v = single
            filter = {k: v}
            obj = query.filter_by(**filter).first()
            if obj == None:
                raise mgen.error.NotFound().describe('object with %s=%s was not found in "%s"' % (
                    k, v, collection)
                )
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
            
    def restfull_get(self, model, single=None):
        """RESTfull GET object or list of objects"""
        log.debug('REST GET {0}{1}'.format(model, 
                                           ", %s=%s" % single if single else ""))
        return self.fetch(session().query(model), 
                          self.page_arguments,
                          single=single,
                          collection=collection_name(model)
                          )
                          
    def restfull_post(self, model):
        """RESTfull POST to create a new object"""
        params = self.request_params
        log.debug('REST POST {0}, {1} properties'.format(model, len(params)))
        new_inst = model()
        for c in model.__table__.columns:
            val = params.get(c.name, None)
            if val != None:
                log.debug("- %s=%s" % (c.name, val))
                setattr(new_inst, c.name, val)
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
        return self.restfull_get(mgen.model.Profile,
                                 single=None if oid is None else ('email', oid))

                          
class Projects(GenericModelHandler):
    """"Projects restfull interface"""
    
    @authenticated
    @jsonify
    def get(self, oid=None):
        """GET list or single project"""
        return self.restfull_get(mgen.model.Project,
                                 single=None if oid is None else ('project_id', oid))
        
    @authenticated
    @jsonify
    def post(self):
        """POST to create a new project"""
        s = session()
        project = self.restfull_post(mgen.model.Project)
        project.project_id = uuid.uuid4()
        s.add(project)
        project.members.append(self.current_profile)
        self.commit_changes(s)
        self.set_status(201)
        
        log.debug('created new project: %s' % project.project_id)
        return self.restfull_get(mgen.model.Project,
                                 single=('project_id', project.project_id))
                                 
                                 
class Templates(GenericModelHandler):
    """"Templates restfull interface"""
    
    @authenticated
    @jsonify
    def get(self, oid=None):
        """GET list or single project"""
        return self.restfull_get(mgen.model.Template,
                                 single=None if oid is None else ('template_id', oid))
        
    @authenticated
    @jsonify
    def post(self):
        """POST to create a new project"""
        s = session()
        t = self.restfull_post(mgen.model.Project)
        t.template_id = uuid.uuid4()
        s.add(t)
        self.commit_changes(s)
        self.set_status(201)
        
        log.debug('created new template: %s' % t.template_id)
        return self.restfull_get(mgen.model.Template,
                                 single=('template_id', t.template_id))


class Items(GenericModelHandler):
    """Items restfull interface"""
    
    @authenticated
    @jsonify
    def get(self, oid=None):
        """GET list or single project"""
        return self.restfull_get(mgen.model.Item,
                                 single=None if oid is None else ('item_id', oid))
        
    @authenticated
    @jsonify
    def post(self):
        """POST to create a new item"""
        s = session()
        i = self.restfull_post(mgen.model.Item)
        i.item_id = uuid.uuid4()
        if not i.uri_path:
            i.uri_path = i.name.lower().replace(' ', '-').replace('/', '-').replace('\\', '-')
        # publish_on -> publish_date
        if i.published:
            i.publish_date = datetime.datetime.now()
        else:
            i.publish_date = datetime.datetime.strptime('%d-%M-%Y',
                                                        self.request_params["publish_on"])
            if i.publish_date < datetime.datetime.now():
                raise mgen.error.BadRequest().describe("publish_on can not be in past if you want to schedule")

        s.add(i)
        self.commit_changes(s)
        self.set_status(201)
        
        log.debug('created new item: %s' % i.item_id)
        return self.restfull_get(mgen.model.Item,
                                 single=('item_id', i.item_id))
        