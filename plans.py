#!/usr/bin/env python
# - * - coding: utf8 - * -

import os
import base64

from datetime import datetime, timedelta
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from common import *
from data import User, Plan

class AddPlanPage(webapp.RequestHandler):
    def get(self, user_id):
        self.response.out.write(template.render(
            os.path.join(template_path, 'plan_add.html'), {
                'next_day': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
                }))

    def post(self, user_id):
        # 验证权限
        query = User.all().filter('owner =', current_user)
        query = query.filter('user_id =', user_id)
        if not query.count():
            self.error(403)
            return
        
        # 获取用户
        user = query.fetch(1)[0]
        Plan(user=user, status=self.request.get('status'),
             plan_time=datetime.strptime(self.request.get('plan_time'),
                                         '%Y-%m-%d %H:%M')).put()
        self.redirect('/')

class DeletePlan(webapp.RequestHandler):
    def get(self, plan_id):
        plan = Plan.get_by_id(int(plan_id))
        if not plan:
            self.error(404)
            return
        if plan.user.owner != current_user:
            self.error(403)
            return
        plan.delete()
        self.redirect('/')

current_user = users.get_current_user()
application = webapp.WSGIApplication([('/plans/add/(.*)', AddPlanPage),
                                      ('/plans/delete/(.*)', DeletePlan),
                                      ], debug=True)
run_wsgi_app(application)
