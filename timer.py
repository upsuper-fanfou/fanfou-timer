#!/usr/bin/env python
# - * - coding: utf8 - * -

import base64
import urllib
import logging

from datetime import datetime
from django.utils import simplejson as json
from google.appengine.api import urlfetch

from data import User, Plan
from result import PlanResult

# 初始化
# 获取当前时间
now = datetime.now()
# 初始化异步发送列表
requests = []

def exec_plan(plan):
    '''发送消息'''

    # 读取计划信息
    user = plan.user
    user_id = user.user_id.encode('utf8')
    password = base64.b64decode(user.password)
    status = plan.status

    # 标记计划执行时间
    plan.exec_time = datetime.now()
    plan.put()

    # 准备发送的信息
    headers = {
            'Authorization': 'Basic ' +
                base64.b64encode('%s:%s' % (user_id, password)),
            'User-Agent': 'Fanfou-Timer',
            }
    body = urllib.urlencode({
            'status': status.encode('utf8'),
            'source': 'timer',
            })

    # 执行移步发送
    rpc = urlfetch.create_rpc(deadline=10)
    urlfetch.make_fetch_call(rpc,
            'http://api.fanfou.com/statuses/update.json',
            body, 'POST', headers)
    requests.append((plan, rpc))

# 打印标准头
print 'Content-Type: text/plain'
print

# 寻找需要被发送的消息
plans = Plan.all().filter('exec_time =', None)
plans = plans.filter('plan_time <=', now).order('plan_time')
for plan in plans:
    exec_plan(plan)

# 等待所有任务完成
for plan, rpc in requests:
    try:
        resp = rpc.get_result()
    except Exception, e:
        # 将错误保存以备查验
        logging.error('error %s occurred at %s' %
                (repr(e), plan.key().id()))
        # 标记为执行失败
        plan.exec_time = None
        plan.result = int(PlanResult.failed)
    else:
        # 检查执行结果
        if resp.status_code == 200:
            plan.result = int(PlanResult.success)
        elif resp.status_code == 401:
            plan.result = int(PlanResult.unauthorized)
        else:
            plan.result = int(PlanResult.other_errors)
    finally:
        plan.put()
