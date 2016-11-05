"""
MGEN Web Authentication handlers
"""

import json
import logging
import functools

import mgen.util
import mgen.error
import mgen.model

import tornado
import tornado.auth

from urllib.parse import urlparse, urlencode, urlsplit
from mgen.web import BaseRequestHandler
from mgen.model import session


log = logging.getLogger(__name__)


def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
    
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or not self.current_profile:
            log.warn('not authorized request on [%s]' % self.request)
            if self.request.method in ("GET", "HEAD") and not self.request.path.startswith('/api'):
                # redirect UI requests
                login_url = urlsplit(self.get_login_url())
                if not login_url.query:
                    if login_url.scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    login_url = login_url._replace(query=urlencode(dict(next=next_url)))
                return self.redirect(login_url.geturl())
                
            # throw error for non-UI calls
            raise mgen.error.Unauthorized().describe("not a user")
        return method(self, *args, **kwargs)
    return wrapper


class Login(BaseRequestHandler):
    '''Allows to select external OAuth provider'''
    
    def get(self):
        return self.render("login.html")


class Logout(BaseRequestHandler):
    '''Delete auth cookies'''
    
    def get(self):
        self.clear_cookie('mgen-auth-principal')
        self.clear_cookie('mgen-auth-profile')


class GoogleOAuth2Login(BaseRequestHandler,
                        tornado.auth.GoogleOAuth2Mixin):
    '''Implement login handler with Google's OAuth endpoint'''
                                   
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            # read google auth info
            user = yield self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth']['redirect_uri'],
                code=self.get_argument('code'))

            userinfo = yield self.oauth2_request(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                access_token=user["access_token"])
            
            s = session()
            profile = s.query(mgen.model.Profile).filter_by(id=userinfo["email"]).first()
            if not profile:
                profile = mgen.model.Profile(
                    id=userinfo["email"],
                    name=userinfo["name"],
                    picture=userinfo["picture"])
                s.add(profile)
                s.commit()
                log.debug('created new locale profile %s' % profile.id)
            
            self.set_secure_cookie('mgen-auth-principal', json.dumps(user, 
                                                                     cls=mgen.util.JSONEncoder))
            self.set_secure_cookie('mgen-auth-profile', json.dumps(profile.to_json(),
                                                                   cls=mgen.util.JSONEncoder))
            
            self.redirect('/')
            
        else:
            # redirect to google login form
            yield self.authorize_redirect(
                redirect_uri=self.settings['google_oauth']['redirect_uri'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})