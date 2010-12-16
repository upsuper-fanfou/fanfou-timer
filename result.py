# - * - coding: utf8 - * -

from enum import Enum

class PlanResult(Enum):
    success = 0 # 无错误
    unauthorized = 1 # 用户名或密码错误
    failed = 2 # 执行失败，等待下一次
    other_errors = 99 # 其他错误
