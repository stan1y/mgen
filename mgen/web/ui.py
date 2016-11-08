"""
MGEN UI callbacks
"""

import json
import logging
import pprint

import mgen.error
import mgen.model

from mgen.model import Permission, session

from mgen.web import BaseRequestHandler
from mgen.web.auth import authenticated

import tornado.template

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
        proj = s.query(mgen.model.Project).filter_by(project_id=oid).one()
        p = proj.get_permission(self.current_profile.email)
        if Permission.Forbidden & p:
            raise mgen.error.Forbidden().describe('access denied to project id "%s"' % oid)
        
        log.debug('displaying project %s' % proj.project_id)
        return self.render("project.html", 
                           user=self.current_user,
                           profile=self.current_profile,
                           project=proj,
                           item_types=mgen.generator.item_types,
                           template_types=mgen.generator.template.template_types,
                           # permissions
                           allow_edit=(Permission.Edit & p),
                           allow_create=(Permission.Create & p),
                           allow_build=(Permission.Build & p),
                           allow_deploy=(Permission.Deploy & p),
                           is_owner=(Permission.GrantPermisson & p))
                           
class Template(BaseRequestHandler):
    pass

class Item(BaseRequestHandler):
    pass

class Page(BaseRequestHandler):
    pass

class TemplatePreview(BaseRequestHandler):
    '''Read template from body and render it with provided parameters'''
    
    @authenticated
    def post(self):
        tmpl_type = self.get_query_argument('type', 'builtin')
        params = json.loads(self.get_query_argument('params', '{}'))
        
        if tmpl_type not in mgen.generator.template.template_types:
            raise mgen.error.BadRequest().describe("unsupported template type: %s" % tmpl_type)
        
        tmpl_body = self.request.body.decode('utf-8')
        generator = mgen.generator.template.Template(tmpl_type, tmpl_body)
        self.write(generator.render(params))
        
        
        