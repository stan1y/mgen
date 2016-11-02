"""
MGEN: Data Models. Base classes and utilities
"""

import re
import uuid
import json
import cgi
import logging

import mgen.ex

from sqlalchemy import create_engine
from sqlalchemy import asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.mutable import Mutable

from sqlalchemy.types import TypeDecorator
from sqlalchemy.types import Text
from sqlalchemy.types import String

from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy.exc import InvalidRequestError

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
                    
                prop = '%s.%s' % (cls.__tablename__, cls.translate_property(srt['property']))
                direction = srt['direction']
                if not direction: continue
                
                log.debug('sorting %s(%s)' % (direction, prop))
                if direction == 'ASC': 
                    sort = asc
                elif direction == 'DESC': 
                    sort = desc
                else:
                    raise mgen.ex.BadRequest().msg('unsupported sort direction [%s]' % direction)
                
                query = query.order_by(sort(prop))
            return query
        except ValueError:
            raise mgen.ex.BadRequest().msg('invalid sort arguments')
            

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

                if isinstance(value, unicode):
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
            raise mgen.ex.BadRequest().msg('invalid filter arguments')


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
            raise mgen.ex.BadRequest().msg('invalid range arguments')


class GenericModelMixin(SortModelMixin, FilterModelMixin, RangeModelMixin):
    '''Generalized mixin for general purpose models'''
    pass


class JSONType(TypeDecorator):
    '''Convert plain types to/from JSON strings'''
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


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
    
    def process_bind_param(self, value, dialect):
        if value == None:
            return value
        return value.hex

    def process_result_value(self, value, dialect):
        return uuid.UUID(value)

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


class DecimalEncoder(json.JSONEncoder):
    '''Encode decimals as long'''
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


#
# MGEN Core Data Objects Framework
#


__session_conn = None
__session_maker = None
__session = None


def connect(conn_str=None):
    '''Connect SQLAlchemy to given database with DBN string'''
    global __session_conn
    global __session_maker
    if conn_str and __session_conn is None:
        __session_conn = conn_str
        
    if __session_maker is None:
        eng = create_engine(__session_conn, pool_recycle=300)
        __session_maker = sessionmaker(bind=eng,
                                       expire_on_commit=False,
                                       autoflush=False)
    return __session_maker


def validate_session(session):
    '''Check if session is valid and recreate if needed'''
    maker = connect()
    if not session:
        return maker()
    
    conn = None
    try:
        conn = session.connection()
    except InvalidRequestError, ex:
        session.rollback()
        conn = session.connection()
        
    if conn.invalidated:
        session.rollback()
        session.close()
        return maker()
        
    #session.expunge_all()
    return session


def session():
    '''Returns current session or setups new one'''
    global __session
    return validate_session(__session)


@as_declarative
class BaseModel(object):
    '''Base class for SQLAlchemy powered models '''
    
    @declared_attr
    def __tablename__(cls):
        '''Table name is class name converted to lower'''
        return cls.__name__.lower()


class Profile(GenericModelMixin, BaseModel):
    