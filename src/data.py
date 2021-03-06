# - * - coding: utf8 - * -

from google.appengine.ext import db

class User(db.Model):
    user_id = db.StringProperty()
    name = db.StringProperty()
    password = db.StringProperty()
    owner = db.UserProperty()

class Plan(db.Model):
    user = db.ReferenceProperty(User)
    status = db.StringProperty(indexed=False, multiline=True)
    plan_time = db.DateTimeProperty()
    exec_time = db.DateTimeProperty(default=None)
    result = db.IntegerProperty(default=None)
    interval = db.IntegerProperty(default=None) # 以分钟记
