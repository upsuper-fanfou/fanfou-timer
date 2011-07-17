# - * - coding: utf8 - * -

from datetime import datetime, timedelta

def next_time(start_time, interval):
    '''获取下一次执行的时间'''
    delta = datetime.now() - start_time
    delta = delta.days * 1440 + (delta.seconds + 59) / 60
    delta = (delta + interval - 1) / interval * interval
    if not delta:
        delta = interval
    start_time += timedelta(minutes=delta)
    return start_time
