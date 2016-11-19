"""
MGEN: Data Models. Base classes and utilities
"""

import os
import re
import uuid
import json
import cgi
import logging

import mgen
import mgen.error
import mgen.util

import mgen.generator.template

import sqlalchemy.exc


from sqlalchemy import create_engine
from sqlalchemy import asc, desc
from sqlalchemy import ForeignKey

from sqlalchemy import Table, Column
from sqlalchemy.types import TypeDecorator
from sqlalchemy.types import Text
from sqlalchemy.types import String
from sqlalchemy.types import Integer
from sqlalchemy.types import DateTime
from sqlalchemy.types import Boolean

from sqlalchemy.inspection import inspect

from sqlalchemy.ext.mutable import Mutable

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import validates
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import mapper
from sqlalchemy.orm.session import object_session

from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr

from validate_email import validate_email

log = logging.getLogger(__name__)


#
# Permissions 
#
class Permission(mgen.util.Enum):
    Forbidden       = 0x000000
    Read            = 0x000001
    Edit            = 0x000010
    Create          = 0x000100
    Build           = 0x001000
    Deploy          = 0x010000
    GrantPermisson  = 0x100000
    
    @staticmethod
    def all():
        pp = 0
        for p in Permission:
            if p == Permission.Forbidden:
                continue
            pp |= p.value
        return pp

#
# Core Data Objects Access API
#

class SortModelMixin(object):
    '''Model mixin with "sort" classmethod'''
    
    @classmethod
    def sort(cls, query, sorting):
        try:
            for srt in json.loads(sorting):
                if not hasattr(cls, srt['property']):
                    log.debug('ignoring sort property [%s]' % srt['property'])
                    continue
                    
                pname = srt['property']
                if hasattr(cls, 'translate_property'):
                    pname = cls.translate_property(pname)
                prop = '%s.%s' % (cls.__tablename__, pname)
                
                direction = srt['direction']
                if not direction: continue
                direction = direction.lower()
                
                log.debug('sorting %s(%s)' % (direction, prop))
                if direction == 'asc': 
                    sort = asc
                elif direction == 'desc': 
                    sort = desc
                else:
                    raise mgen.error.BadRequest().describe('unsupported sort direction "%s"' % direction)
                
                query = query.order_by(sort(prop))
            return query
        except ValueError:
            raise mgen.error.BadRequest().describe('invalid sort arguments')
            

class FilterModelMixin(object):
    '''Model mixin with "filter" classmethod'''
    
    @classmethod
    def filter(cls, query, filtering):
        try:
            for flt in json.loads(filtering):
                if not hasattr(cls, str(flt['property'])):
                    log.debug('ignoring filter property [%s]' % flt['property'])
                    continue
                
                pname = flt['property']
                if hasattr(cls, 'translate_property'):
                    pname = cls.translate_property(pname)
                    
                prop = '%s.%s' % (cls.__tablename__, pname)
                value = flt['value']

                if isinstance(value, str):
                    if value.isdigit():
                        query = query.filter('%s = %s' % (prop, value.encode('utf-8')))
                    else:
                        if re.match('^[\w@.]+$', value):
                            query = query.filter('%s LIKE "%%%s%%"' % (prop, value))

                if isinstance(value, (int, float, bool)):
                    query = query.filter('%s = %d' % (prop, value))

                if value == None:
                    query = query.filter('%s IS NULL' % (prop))
            return query
        except ValueError:
            raise mgen.error.BadRequest().describe('invalid filter arguments')


class RangeModelMixin(object):
    '''Model mixin with "range" classmethod'''
    
    @classmethod
    def range(cls, query, ranging):
        try:
            for flt in json.loads(ranging):
                if not hasattr(cls, str(flt['property'])):
                    log.debug('ignoring ranging property [%s]' % flt['property'])
                    continue

                pname = flt['property']
                if hasattr(cls, 'translate_property'):
                    pname = cls.translate_property(pname)

                prop = '%s.%s' % (cls.__tablename__, pname)
                value_from = flt['value_from']
                value_to = flt['value_to']

                if isinstance(value_from, (int, float)) and isinstance(value_to, (int, float)):
                    query = query.filter('%s >= %d' % (prop, value_from))
                    query = query.filter('%s < %d' % (prop, value_to))

            return query
        except ValueError:
            raise mgen.error.BadRequest().describe('invalid range arguments')


class GenericModelMixin(SortModelMixin, FilterModelMixin, RangeModelMixin):
    '''Generalized mixin for general purpose models'''
    pass


class EscapedString(TypeDecorator):
    '''cgi.escape strings from user'''
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value == None:
            return value
        escaped = cgi.escape(value, quote=True)
        return escaped

    def process_result_value(self, value, dialect):
        return value


class IDType(TypeDecorator):
    '''Convert "uuid" instances to/from string'''
    impl = String
    
    def __init__(self):
        # 32 char hex string with UUID
        super().__init__(32)
    
    def process_bind_param(self, value, dialect):
        if value == None:
            return value
        if isinstance(value, uuid.UUID):
            return value.hex
        return value

    def process_result_value(self, value, dialect):
        if value == None:
            return None
        return uuid.UUID(value)


class JSONObject(TypeDecorator):
    '''Opaque JSON string column type'''
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value == None:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value == None:
            return None
        return json.loads(value.decode('utf-8') if isinstance(value, bytes) else value)


class MutationDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)
            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."
        dict.__delitem__(self, key)
        self.changed()


class MutationList(Mutable, list):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain lists to MutationList."
        if not isinstance(value, MutationList):
            if isinstance(value, list):
                return MutationList(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect list set events and emit change events."
        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect list del events and emit change events."
        list.__delitem__(self, key)
        self.changed()

    def __setslice__ (self, i, j, sequence):
        "Detect list slice events and emit change events."
        list.__setslice__(self, i, j, sequence)
        self.changed()

    def __delslice__ (self, i, j):
        "Detect list delete slice events and emit change events."
        list.__delslice__(self, i, j)
        self.changed()


#
# MGEN Core Objects
#
# Profile:   User details model linked with external auth principal by email
#
# Project:   Top level model with linked permissions per Profile
#
# Template:  A template represents a formatting used to render html with a list of
#            variables. These variables are available to formatting code and
#            must be specified by a caller.
#
# Page:      A basic rendering item with user defined input, resources and a Template producing html.
#            There are several types of pages with different sets of predefined inputs 
#            and possible locations/paths.
#
# Item:      A rendering item is an input parameters for metadata defined in Page
#


@as_declarative()
class BaseModel(object):
    '''Base class for SQLAlchemy powered models '''
    
    @declared_attr
    def __tablename__(cls):
        '''Table name is class name converted to lower'''
        return cls.__name__.lower()


def get_primary_key(cls, idx=0):
    '''Returns name of the primary key of this model by index. Returns first key by default'''
    return cls.__mapper__.primary_key[idx]


# Many-to-Many link of profiles to projects and permission in them
project2profile = Table("project2profile",
                        BaseModel.metadata,
                        Column('project', IDType, ForeignKey("project.project_id"), primary_key=True),
                        Column('profile', EscapedString(255), ForeignKey("profile.email"), primary_key=True),
                        Column('permission', Integer))


class ProjectPermission(object):
    '''Permission for a profile to do something with project'''
    
    @staticmethod
    def grant(p, project_id, profile_email):
        '''Grants a permission :p to a profile with :profile_email in project with :project_id'''
        val = p.value if isinstance(p, Permission) else p
        perm = ProjectPermission()
        perm.project = project_id
        perm.profile = profile_email
        perm.permission = val
        log.debug('granted permission "%d" to "%s" for project: %s' % (
            val, profile_email, project_id))
        return perm
    
# map model class to references table
mapper(ProjectPermission, project2profile)


class ProfileStore(dict):
  '''Proxy to access cached profile json'''
  
  #  @param name values name to fetch str
  #  raises ImportDataError if value missing for name
  def __getattr__ (self, name):
        try:
            return self[name]
        except KeyError:
            raise ValueError('Key "%s" was not found in ProfileStore' % name)


class Profile(GenericModelMixin, BaseModel):
    '''Base class represending local profile for security principals'''
    
    email = Column(EscapedString(255), primary_key=True)
    name = Column(EscapedString(255), unique=True)
    picture = Column(EscapedString(1024))
    projects = relationship("Project",
                            secondary=project2profile,
                            back_populates="members")
                            
    @validates('id')
    def validate_id(self, key, val):
        '''Make sure profile id is well formed email'''
        assert validate_email(val, check_mx=False)
                            
    def to_json(self):
        return {
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "projects": [p.project_id for p in self.projects]
        }
        
    @staticmethod
    def from_json(data):
        return ProfileStore(data)

class Project(GenericModelMixin, BaseModel):
    '''The project to build a static website'''
    
    project_id = Column(IDType, primary_key=True)
    title = Column(EscapedString(255), unique=True)
    public_base_uri = Column(EscapedString(1024))
    options = Column(MutationDict.as_mutable(JSONObject))
    members = relationship("Profile", 
                           secondary=project2profile,
                           back_populates="projects")

    def to_json(self):
        return {
            'id': self.project_id,
            'title': self.title,
            'public_base_uri': self.public_base_uri,
            'members': [m.email for m in self.members],
            'slugs': [s.slug_id for s in self.slugs],
            'templates': [t.template_id for t in self.templates],
            'items': [i.item_id for i in self.items],
            'pages': [p.page_id for p in self.pages]
        }

    def get_permission(self, email):
        '''Returns highest Permission available to given profile with :email in this project'''
        q = session().query(project2profile).filter(project2profile.c.profile==email)\
                                            .filter(project2profile.c.project==self.project_id)\
                                           .order_by(project2profile.c.permission)
        if q.count() == 0:
            return Permission.Forbidden

        return mgen.util.EnumMask(Permission, q.first().permission)
        
    def grant_permission(self, p, email):
        '''Grants specified Permission :p to profile with :email'''
        ProjectPermission.grant(p, self.project_id, email)
        


class Slug(GenericModelMixin, BaseModel):
    '''The tarball with generated static content of some project'''
    
    slug_id = Column(IDType, primary_key=True)
    created = Column(DateTime)
    created_by = Column(EscapedString(255), ForeignKey('profile.email'))
    size = Column(Integer)
    
    project_id = Column(IDType, ForeignKey('project.project_id'))
    project = relationship(Project, backref=backref('slugs', lazy='dynamic'))
    
    def to_json(self):
        return {
            'id': self.slug_id,
            'project': self.project_id,
            'created': self.created,
            'created_by': self.created_by,
            'size': self.size
        }
    
    @property
    def filename(self):
        return self.slug_id + ".slug"
    
    @property
    def filepath(self):
        return os.path.join(mgen.options(mgen.SLUGS_LOCAL_PATH), self.filename)


tag2item = Table("tag2item",
                BaseModel.metadata,
                Column('tag', EscapedString(255), ForeignKey("tag.tag")),
                Column('item', IDType, ForeignKey("item.item_id")))


class Tag(GenericModelMixin, BaseModel):
    '''Tag is a string attibute marker'''
    
    tag = Column(EscapedString(255), primary_key=True)
    items = relationship("Item", 
                         secondary=tag2item,
                         back_populates="tags")
                         
    def to_json(self):
        return {'tag': self.tag }


class Item(GenericModelMixin, BaseModel):
    '''Item is a generic container with user provided content'''
    
    item_id = Column(IDType, primary_key=True)
    name = Column(EscapedString(255), unique=True)
    uri_path = Column(EscapedString(255), unique=True)
    type = Column(EscapedString(255))
    body = Column(Text)
    published = Column(Boolean)
    publish_date = Column(DateTime)
    
    project_id = Column(IDType, ForeignKey('project.project_id'))
    project = relationship(Project, backref=backref('items', lazy='dynamic'))
    
    tags = relationship("Tag", 
                       secondary=tag2item,
                       back_populates="items")
                       
    def to_json(self):
        return {
            'id': self.item_id,
            'type': self.type,
            'name': self.name,
            'uri_path': self.uri_path,
            'body': self.body,
            'published': self.published,
            'publish_date': self.publish_date,
            'tags': [t.tag for t in self.tags]
        }
    

class Template(GenericModelMixin, BaseModel):
    '''Template is used to render Items into html for Slug'''
    
    template_id = Column(IDType, primary_key=True)
    name = Column(EscapedString(255), unique=True)
    type = Column(EscapedString(255))
    data = Column(EscapedString)
    params = Column(MutationList.as_mutable(JSONObject))
    
    project_id = Column(IDType, ForeignKey('project.project_id'))
    project = relationship(Project, backref=backref('templates', lazy='dynamic'))
    
    def to_json(self):
        return {
            'id': self.template_id,
            'name': self.name,
            'type': self.type,
            'data': self.data,
            'params': self.params
        }


class Page(GenericModelMixin, BaseModel):
    
    page_id = Column(IDType, primary_key=True)
    path    = Column(EscapedString(255), unique=True)
    input   = Column(MutationDict.as_mutable(JSONObject))
    
    template_id = Column(IDType, ForeignKey("template.template_id"))
    template    = relationship(Template, backref=backref('pages'))
    
    project_id = Column(IDType, ForeignKey("project.project_id"))
    project    = relationship(Project, backref=backref('pages'))

#
# MGEN Data Storage Sessions
#


__session_conn = None
__session_maker = None
__session = None


def connect():
    '''Connect SQLAlchemy to given database with DBN string'''
    global __session_maker
    if __session_maker is None:
        raise mgen.error.InternalError().describe("connection to database was not initialized")
    return __session_maker


def setup(conn_str, pool_recycle=300):
    '''Setup connection to db and create models'''
    global __session_conn
    global __session_maker
    
    if __session_maker is not None:
        raise Exception("models already initialized.")
    
    if conn_str and __session_conn is None:
        __session_conn = conn_str
    
    log.debug('initializing database session to %s pool_recycle=%d' % 
        (conn_str, pool_recycle))
    engine = create_engine(__session_conn, pool_recycle=pool_recycle)
    __session_maker = sessionmaker(bind=engine,
                                   expire_on_commit=False,
                                   autoflush=True)
    
    log.debug('initializing %d tables' % len(BaseModel.metadata.tables))
    BaseModel.metadata.create_all(engine, checkfirst=True)

def validate_session(session):
    '''Check if session is valid and recreate if needed'''
    maker = connect()
    if not session:
        log.debug('create new session')
        return maker()
    
    conn = None
    try:
        conn = session.connection()
    except sqlalchemy.exc.InvalidRequestError:
        log.warn('session connection lost, rolling back')
        session.rollback()
        conn = session.connection()
        
    if conn.invalidated:
        log.warn('session connection lost, recreating session')
        session.rollback()
        session.close()
        return maker()
        
    #session.expunge_all()
    return session


def session():
    '''Returns current session or setups new one'''
    global __session
    __session = validate_session(__session)
    return __session