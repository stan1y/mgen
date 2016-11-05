"""
MGEN UI callbacks
"""

import json
import logging
import tornado.template


import mgen.error
import mgen.model

from mgen.model import session

from mgen.web import BaseRequestHandler
from mgen.web.auth import authenticated


log = logging.getLogger(__name__)


class Overview(BaseRequestHandler):
    @authenticated
    def get(self):
        s = session()
        return self.render("overview.html", 
                           user=self.current_user,
                           profile=self.current_profile)


class Project(BaseRequestHandler):
    @authenticated
    def get(self, oid):
        s = session()
        return self.render("project.html", 
                           user=self.current_user,
                           profile=self.current_profile,
                           project=s.query(mgen.model.Project).filter_by(id=oid)).one()
