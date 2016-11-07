"""
MGEN Generic utilities
"""

import json
import decimal
import uuid
import datetime
import enum


class JSONEncoder(json.JSONEncoder):
    '''Encode JSON special types'''

    def default(self, o):
        # handler decimals
        if isinstance(o, decimal.Decimal):
            return float(o)
            
        # handle uuid
        if isinstance(o, uuid.UUID):
            return o.hex
            
        # handle dates
        if isinstance(o, datetime.date):
            return o.isoformat()
            
        # handle sqlalchemy models
        if hasattr(o, "to_json"):
            return getattr(o, "to_json")()
            
        # fallback 
        return super(JSONEncoder, self).default(o)


class EnumMask(object):
    '''Enum bitmask with and/or operators'''
    def __init__(self, enum, value):
        self._enum = enum
        self._value = value
 
    def __and__(self, other):
        # print ("EnumMask::__and__(%s, %s): %s & %s = %s" % (
        #     self, other,
        #     self._value, other.value, 
        #     self._value & other.value))
        assert isinstance(other, self._enum)
        return self._value & other.value
 
    def __or__(self, other):
        # print ("EnumMask::__or__(%s, %s): %s | %s = %s" % (
        #     self, other,
        #     self._value, other.value, 
        #     self._value | other.value))
        assert isinstance(other, self._enum)
        return EnumMask(self._enum, self._value | other.value)
 
    def __repr__(self):
        return "<{} for {}: {}>".format(
            self.__class__.__name__,
            self._enum,
            self._value
        )


class Enum(enum.Enum):
    '''Enum based on oldschool bitmask'''
    
    @classmethod
    def enum(cls, val):
        '''Returns an instances of this enum corresponding to the given value'''
        for e in cls:
            if e.value == val:
                return e
        raise ValueError('Enum "%s" has no member with value "%s"' %(
            cls.__name__, val))
 
    def __or__(self, other):
        # print ("Enum::__or__(%s, %s)" % (self, other))
        return EnumMask(self.__class__, self.value | other.value)
 
    def __and__(self, other):
        # print ("Enum::__and__(%s, %s)" % (self, other))
        if isinstance(other, self.__class__):
            return self.value & other.value
        elif isinstance(other, EnumMask):
            return other & self
        else: raise ValueError("Unsupported value: %s (%s)" % (other, other.__class__.__name__))