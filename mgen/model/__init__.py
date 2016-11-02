"""
MGEN: Data Models. Base classes and utilities
"""

import re
import json
import logging
import sqlalchemy

import mgen.ex

from sqlalchemy import asc, desc
from sqlalchemy.ext.mutable import Mutable


log = logging.getLogger(__name__)


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

                if isinstance(value, basestring):
                    if value.isdigit():
                        query = query.filter('%s = %s' % (prop, value))
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
            
