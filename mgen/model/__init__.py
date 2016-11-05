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

from sqlalchemy.ext.mutable import Mutable

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import validates
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr

from validate_email import validate_email

log = logging.getLogger(__name__)


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
        return value.hex

    def process_result_value(self, value, dialect):
        return uuid.UUID(value)


class JSONObject(TypeDecorator):
    '''Opaque JSON string column type'''
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value == None:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
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


@as_declarative()
class BaseModel(object):
    '''Base class for SQLAlchemy powered models '''
    
    @declared_attr
    def __tablename__(cls):
        '''Table name is class name converted to lower'''
        return cls.__name__.lower()


project_membership = Table("project_membership",
                           BaseModel.metadata,
                           Column('project_id', IDType, ForeignKey("project.id")),
                           Column('profile_id', EscapedString(255), ForeignKey("profile.id")),
                           Column('permissions', Integer))


class Profile(GenericModelMixin, BaseModel):
    '''Base class represending local profile for security principals'''
    
    id = Column(EscapedString(255), primary_key=True)
    name = Column(EscapedString(255))
    picture = Column(EscapedString(1024))
    projects = relationship("Project", 
                            secondary=project_membership,
                            back_populates="members")
                            
    @validates('id')
    def validate_id(self, key, val):
        '''Make sure profile id is well formed email'''
        assert validate_email(val, check_mx=True)
                            
    def to_json(self):
        return {
            "email": self.id,
            "name": self.name,
            "picture": self.picture,
            "projects": [p.id for p in self.projects]
        }


class Project(GenericModelMixin, BaseModel):
    '''The project to build a static website'''
    
    id = Column(IDType, primary_key=True)
    title = Column(EscapedString(255))
    public_base_uri = Column(EscapedString(1024))
    options = Column(MutationDict.as_mutable(JSONObject))
    members = relationship("Profile", 
                           secondary=project_membership,
                           back_populates="projects")

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'public_base_uri': self.public_base_uri,
            'members': [m.id for m in self.members]
        }


class Slug(GenericModelMixin, BaseModel):
    '''The tarball with generated static content of some project'''
    
    id = Column(IDType, primary_key=True)
    project_id = Column(IDType, ForeignKey('slug.id'))
    project = relationship(Profile, backref=backref('slugs', lazy='dynamic'))
    created = Column(DateTime)
    created_by = Column(EscapedString(255), ForeignKey('profile.id'))
    size = Column(Integer)
    
    def to_json(self):
        return {
            'id': self.id,
            'project': self.project_id,
            'created': self.created,
            'created_by': self.created_by,
            'size': self.size
        }
    
    @property
    def filename(self):
        return self.id + ".slug"
    
    @property
    def filepath(self):
        return os.path.join(mgen.options(mgen.SLUGS_LOCAL_PATH), self.filename)

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