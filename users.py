#!/usr/bin/env python
# - * - coding: utf8 - * -

import os
import base64

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from common import *
from data import User, Plan

class AddUserPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(
            os.path.join(template_path, 'user_add.html'), {}))

    def post(self):
        user_id = self.request.get('user_id')
        password = base64.b64encode(self.request.get('password'))
        query = User.all().filter('owner =', current_user)
        count = query.filter('user_id =', user_id).count()
        if count:
            self.response.out.write('用户已存在！')
            return
        User(user_id=user_id, password=password, owner=current_user).put()
        self.redirect('/')

class DeleteUser(webapp.RequestHandler):
    def get(self, user_id):
        query = User.all().filter('owner =', current_user)
        query = query.filter('user_id =', user_id)
        if not query.count():
            self.error(404)
            return
        query.fetch(1)[0].delete()
        self.redirect('/')

current_user = users.get_current_user()
application = webapp.WSGIApplication([('/users/add', AddUserPage),
                                      ('/users/delete/(.*)', DeleteUser),
                                      ], debug=True)
run_wsgi_app(application)
