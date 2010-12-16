#!/usr/bin/env python
# - * - coding: utf8 - * -

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from common import *
from data import User, Plan
from users import AddUserPage

class MainPage(webapp.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        template_data = { 'users': [] }
        for user in User.all().filter('owner =', current_user):
            plans = []
            for plan in Plan.all().filter('user =', user).order('-plan_time'):
                plans.append({
                        'key': plan.key().id(),
                        'status': plan.status,
                        'plan_time': plan.plan_time,
                        'exec_time': plan.exec_time,
                        'result': plan.result,
                        })
            template_data['users'].append({
                    'user_id': user.user_id,
                    'plans': plans,
                    })
        self.response.out.write(template.render(
            os.path.join(template_path, 'main.html'), template_data))

application = webapp.WSGIApplication([('/', MainPage)], debug=True)
run_wsgi_app(application)
