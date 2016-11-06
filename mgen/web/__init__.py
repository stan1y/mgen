"""
Web intefaces for MGEN.

It exposes module level make_app function for mgen.app module
"""
import os
import json
import logging

import tornado.web
import mgen.model
import mgen.error
import mgen.util
import sqlalchemy.orm.exc


log = logging.getLogger(__name__)


class BaseRequestHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        '''
        Returns current auth principal (token) json 
        received from external auth provider and stored in
        a secure cookie on client
        '''
        prn = self.get_secure_cookie("mgen-auth-principal")
        if prn:
            return json.loads(prn.decode('utf-8'))
        return None
        
    def get_profile(self):
        '''Returns profile id (email) stored in secure cookie'''
        profile = self.get_secure_cookie("mgen-auth-profile")
        if profile:
            return profile.decode('utf-8')
        return None
    
    @property
    def current_profile(self):
        '''Returns a Profile model of the current user'''
        if hasattr(self, '__cached_profile'):
            return getattr(self, '__cached_profile')
        
        profile_email = self.get_profile()
        log.debug('loading profile: %s' % profile_email)
        self.__cached_profile = mgen.model.session().query(
            mgen.model.Profile).filter_by(email=profile_email).first()
            
        return self.__cached_profile