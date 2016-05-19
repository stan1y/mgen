"""
Web intefaces for MGEN.

It exposes module level make_app function for mgen.app module
"""
import os
import functools
import logging

import tornado
import tornado.web
import tornado.auth

import mako.template
import mako.lookup
import mako.exceptions

import mgen.web.api
import mgen.web.ui

import logging

MGEN_DEFINES = os.environ.get("MGEN_DEFINES") or "mgen.defines"
MGEN_LOG_LEVEL = logging.DEBUG
MGEN_ADDR = os.environ.get("MGEN_ADDR") or '0.0.0.0'
MGEN_PORT = int(os.environ.get("MGEN_PORT") or 8888)
MGEN_PUBLIC_URL = 'http://www.endlessinsomnia.com/projects/mgen'
MGEN_LOGIN_REDIRECT_URL = 'http://mgen-web.herokuapp.com/auth/google'
MGEN_GOOGLE_OAUTH_CREDS = {
	"key": "664409134549-6eotcrte0qqhu4l9anaq57k5ua4a5a4n.apps.googleusercontent.com",
	"secret": "idwzGRRJjuGlv5W4G2tpicl4"
}


log = logging.getLogger(__name__)

class MgenBaseHandler(tornado.web.RequestHandler):

	@property
	def auth_principal(self):
		return self.get_secure_cookie('mgen-auth-principal')

	@property
	def auth_token(self):
		return self.get_secure_cookie('mgen-auth-token')
	

def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            log.warn('not authorized request on [%s]' % self.request)
            if self.request.method in ("GET", "HEAD") and not self.request.path.startswith('/+api'):
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
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


class GoogleOAuth2LoginHandler(MgenBaseHandler,
                               tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
    	log.debug("login to google oauth vith client_id: {0}".format(
    		self.settings['google_oauth']['key']))
        redirect_uri = self.settings.get('login_url') or self.settings.get('public_url')
        if self.get_argument('code', False):
            user = yield self.get_authenticated_user(
                redirect_uri=redirect_uri,
                code=self.get_argument('code'))
            log.info( repr(user) )

            userinfo = yield self.oauth2_request(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                access_token=user["access_token"])
            log.info( repr(userinfo) )
            
            self.set_secure_cookie('mgen-auth-principal', user)
            self.set_secure_cookie('mgen-auth-profile', userinfo)
        else:
            yield self.authorize_redirect(
                redirect_uri=redirect_uri,
                client_id=self.settings['google_oauth']['key'],
                scope=['email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


def make_app():
	'''Create tornado app instance'''
	return tornado.web.Application(
    	[
    		(r"/auth/google", GoogleOAuth2LoginHandler)
    	],
    	google_oauth=MGEN_GOOGLE_OAUTH_CREDS,
	    public_url=MGEN_PUBLIC_URL,
	    login_url=MGEN_LOGIN_REDIRECT_URL
	    )

__all__ = [
	GoogleOAuth2LoginHandler,
	make_app
]