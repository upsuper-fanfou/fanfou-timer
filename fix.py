#!/usr/bin/env python
# - * - coding: utf8 - * -

import base64

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.api import urlfetch

from data import User, Plan

print 'Content-Type: text/plain;charset=UTF-8'
print
plans = Plan.all().filter('user =', db.Key.from_path('User', 69006))
db.delete([plan for plan in plans])
