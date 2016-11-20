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

class ProjectPermissionMixin(object):
    '''Providers easy access to project permissions'''
    
    def get_permissions(self, proj):
        p = proj.get_permission(self.current_profile.email)
        if Permission.Forbidden & p:
            raise mgen.error.Forbidden().describe('access denied to project id "%s"' % project_id)
        # permissions
        return {
            'forbidden': (Permission.Forbidden & p),
            'allow_edit' : (Permission.Edit & p),
            'allow_create' : (Permission.Create & p),
            'allow_build' : (Permission.Build & p),
            'allow_deploy' : (Permission.Deploy & p),
            'is_owner' : (Permission.GrantPermisson & p)
        }

class Overview(BaseRequestHandler):
    @authenticated
    def get(self):
        s = session()
        return self.render("overview.html", 
                           user=self.current_user,
                           profile=self.current_profile)

class Project(BaseRequestHandler, ProjectPermissionMixin):
    @authenticated
    def get(self, project_id):
        s = session()
        proj = s.query(mgen.model.Project).filter_by(project_id=project_id).one()
        p = self.get_permissions(proj)
        if p['forbidden']:
             raise mgen.error.Forbidden().describe('access denied to project id "%s"' % project_id)
        
        log.debug('displaying project %s' % proj.project_id)
        return self.render("project.html", 
                           user=self.current_user,
                           profile=self.current_profile,
                           item_types=mgen.generator.item_types,
                           template_types=mgen.generator.template.template_types,
                           project=proj,
                           **p
                          )
                           
class Template(BaseRequestHandler, ProjectPermissionMixin):
    @authenticated
    def get(self, template_id):
        s = session()
        tmpl = s.query(mgen.model.Template).filter_by(template_id=template_id).one()
        p = self.get_permissions(tmpl.project)
        if p['forbidden']:
             raise mgen.error.Forbidden().describe('access denied to project id "%s"' % tmpl.project_id)
        
        log.debug('displaying template %s' % tmpl.template_id)
        return self.render("template.html", 
                           user=self.current_user,
                           profile=self.current_profile,
                           item_types=mgen.generator.item_types,
                           template_types=mgen.generator.template.template_types,
                           template=tmpl,
                           **p)


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
        
        
        