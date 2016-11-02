"""
MGEN Web Authentication handlers
"""

import json
import urllib
import urlparse
import logging
import functools

import mgen.ex
import tornado
import tornado.auth

from mgen.web import BaseRequestHandler


log = logging.getLogger(__name__)


def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
    
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            log.warn('not authorized request on [%s]' % self.request)
            if self.request.method in ("GET", "HEAD") and not self.request.path.startswith('/+api'):
                # redirect UI requests
                url = self.get_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            # throw error for non-UI calls
            raise mgen.ex.Unauthorized().msg("not a user")
        return method(self, *args, **kwargs)
    return wrapper
    

class GoogleOAuth2LoginHandler(BaseRequestHandler,
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
            
            self.set_secure_cookie('mgen-auth-principal', json.dumps(user))
            self.set_secure_cookie('mgen-auth-profile', json.dumps(userinfo))
            
            self.redirect('/')
            
        else:
            # redirect to google login form
            yield self.authorize_redirect(
                redirect_uri=self.settings['google_oauth']['redirect_uri'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})