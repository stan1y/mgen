"""
MGEN UI callbacks
"""

import json
import logging
import tornado.template

import mgen.ex

from mgen.web import BaseRequestHandler
from mgen.web.auth import authenticated



log = logging.getLogger(__name__)


class Dashboard(BaseRequestHandler):
    @authenticated
    def get(self):
        return self.render("dashboard.html")
        
        
class LoginForm(BaseRequestHandler):
    
    def get(self):
        return self.render("login.html")
    
    def post(self):
        pass
        