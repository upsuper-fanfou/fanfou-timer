#!/usr/bin/env python
# - * - coding: utf8 - * -

import os
import urllib
import base64

from datetime import datetime, timedelta
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from data import User, Plan
from common import next_time

def get_users_list():
    return [user for user in User.all().filter('owner =', current_user)]

def convert_users_list(users):
    return [{
        'user_id': user.user_id,
        'name': user.name,
        } for user in users]

def get_user_plans(user):
    return [{
        'plan_id': plan.key().id(),
        'status': plan.status,
        'plan_time':
            (plan.plan_time + utc_fix).strftime('%Y-%m-%d %H:%M'),
        'exec_time':
            (plan.exec_time + utc_fix).strftime('%Y-%m-%d %H:%M')
                        if plan.exec_time else None,
        'interval': plan.interval,
        'result': plan.result,
        } for plan in
              Plan.all().filter('user =', user).order('-plan_time')]

class MainPage(webapp.RequestHandler):
    def get(self):
        users = get_users_list()
        data = (convert_users_list(users),
                get_user_plans(users[0]) if users else [])
        json.dump(data, self.response.out)

class UserAdd(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('user_id')
        password = self.request.get('password')

        # 验证是否重复添加
        users = User.all().filter('owner =', current_user)
        count = users.filter('user_id =', user_id).count()
        if count:
            json.dump({ 'error': True, 'reason': u'用户已存在' },
                    self.response.out)
            return

        # 验证用户名密码是否正确
        headers = {
                'Authorization': 'Basic ' +
                    base64.b64encode('%s:%s' %
                        (user_id.encode('utf8'), password.encode('utf8'))),
                }
        try:
            resp = urlfetch.fetch(
                    'http://api.fanfou.com/account/verify_credentials.json',
                    headers=headers, deadline=10)
        except Exception, e:
            json.dump({ 'error': True, 'reason': u'错误 ' + repr(e) },
                    self.response.out)
        else:
            if resp.status_code == 200:
                user_data = json.loads(resp.content)
                user_id = user_data['id']
                name = user_data['name']
                # 添加到数据库
                user = User(user_id=user_id,
                            password=base64.b64encode(password),
                            name=name,
                            owner=current_user)
                user.put()
                # 输出到浏览器
                json.dump({
                    'error': False,
                    'user_id': user_id,
                    'users': convert_users_list(get_users_list()),
                    'plans': get_user_plans(user),
                    }, self.response.out)
            elif resp.status_code == 401:
                json.dump({ 'error': True, 'reason': u'用户名或密码错误' },
                        self.response.out)
            else:
                json.dump({
                    'error': True,
                    'reason': u'HTTP Error %d' % (resp.status_code, )
                    }, self.response.out)

class UserEdit(webapp.RequestHandler):
    def post(self):
        old_user_id = self.request.get('old_user_id')
        user_id = self.request.get('user_id')
        password = self.request.get('password')

        users = User.all().filter('owner =', current_user)
        # 获取原帐号信息
        the_user = users.filter('user_id =', old_user_id)
        if not the_user.count():
            return
        the_user = the_user.fetch(1)[0]
        if not password:
            password = base64.b64decode(the_user.password)

        # 验证是否重复添加
        if old_user_id != user_id:
            count = users.filter('user_id =', user_id).count()
            if count:
                json.dump({ 'error': True, 'reason': u'用户已存在' },
                        self.response.out)
                return

        # 验证用户名密码是否正确
        headers = {
                'Authorization': 'Basic ' +
                    base64.b64encode('%s:%s' %
                        (user_id.encode('utf8'), password.encode('utf8'))),
                }
        try:
            resp = urlfetch.fetch(
                    'http://api.fanfou.com/account/verify_credentials.json',
                    headers=headers, deadline=10)
        except Exception, e:
            json.dump({ 'error': True, 'reason': u'错误 ' + repr(e) },
                    self.response.out)
        else:
            if resp.status_code == 200:
                user_data = json.loads(resp.content)
                user_id = user_data['id']
                name = user_data['name']
                # 修改到数据库
                the_user.user_id = user_id
                the_user.password = base64.b64encode(password)
                the_user.name = name
                the_user.put()
                # 输出到浏览器
                json.dump({
                    'error': False,
                    'user_id': user_id,
                    'users': convert_users_list(get_users_list()),
                    'plans': get_user_plans(the_user),
                    }, self.response.out)
            elif resp.status_code == 401:
                json.dump({ 'error': True, 'reason': u'用户名或密码错误' },
                        self.response.out)
            else:
                json.dump({
                    'error': True,
                    'reason': u'HTTP Error %d' % (resp.status_code, )
                    }, self.response.out)

class UserDelete(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('user_id')
        users = User.all().filter('owner =', current_user)
        the_user = users.filter('user_id =', user_id)
        if not the_user.count():
            return
        the_user = the_user.fetch(1)[0]
        plans = Plan.all().filter('user =', the_user)
        db.delete([plan for plan in plans])
        the_user.delete()

        # 获取新的数据
        users = get_users_list()
        data = {
                'users': convert_users_list(users),
                'plans': get_user_plans(users[0]) if users else [],
                }
        json.dump(data, self.response.out)

class PlansList(webapp.RequestHandler):
    def get(self, user_id):
        user_id = urllib.unquote(user_id).decode('utf8')
        user = User.all().filter('owner =', current_user)
        user = user.filter('user_id =', user_id).fetch(1)[0]
        json.dump(get_user_plans(user), self.response.out)

class PlanAdd(webapp.RequestHandler):
    def post(self):
        status = self.request.get('status')
        user_id = self.request.get('user_id')
        user = User.all().filter('owner =', current_user)
        user = user.filter('user_id =', user_id).fetch(1)[0]
        if status:
            plan_time = datetime.strptime(self.request.get('plan_time'), 
                                          '%Y-%m-%d %H:%M') - utc_fix
            interval = int(self.request.get('interval'))
            if interval and plan_time <= datetime.now():
                plan_time = next_time(plan_time, interval)
            Plan(user=user,
                 status=status,
                 plan_time=plan_time,
                 interval=interval
                 ).put()
        json.dump(get_user_plans(user), self.response.out)

class PlanEdit(webapp.RequestHandler):
    def post(self):
        plan_id = int(self.request.get('plan_id'))
        plan = Plan.get_by_id(plan_id)
        if not plan:
            return
        user = plan.user
        if user.owner != current_user:
            return
        status = self.request.get('status')
        if status:
            plan_time = datetime.strptime(self.request.get('plan_time'), 
                                          '%Y-%m-%d %H:%M') - utc_fix
            interval = int(self.request.get('interval'))
            if interval and plan_time <= datetime.now():
                plan_time = next_time(plan_time, interval)
            plan.status = status
            plan.plan_time = plan_time
            plan.interval = interval
            plan.put()
        json.dump(get_user_plans(user), self.response.out)

class PlanDelete(webapp.RequestHandler):
    def post(self):
        plan_id = int(self.request.get('plan_id'))
        plan = Plan.get_by_id(plan_id)
        user = plan.user
        if user.owner != current_user:
            return
        plan.delete()
        json.dump(get_user_plans(user), self.response.out)

current_user = users.get_current_user()
utc_fix = timedelta(hours=8)
application = webapp.WSGIApplication([('/main', MainPage),
                                      ('/user/add', UserAdd),
                                      ('/user/edit', UserEdit),
                                      ('/user/delete', UserDelete),
                                      ('/plans/(.*)', PlansList),
                                      ('/plan/add', PlanAdd),
                                      ('/plan/edit', PlanEdit),
                                      ('/plan/delete', PlanDelete),
                                      ], debug=False)
run_wsgi_app(application)
