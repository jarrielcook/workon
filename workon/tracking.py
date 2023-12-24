import os
import json
import time
import sqlite3
from datetime import datetime,date
from workon import config

TIME_TRACK_DB='.time_track.db'
TIMERS_FILE='.timers.json'

#
# Time Spent Database
#
def create_time_spent_db():
    cfg = config.read_config()
    timer_db = os.path.join(cfg['context_dir'], TIME_TRACK_DB)
    if os.path.exists(timer_db) == False:
        connection = sqlite3.connect(timer_db)
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE time_spent(context NOT NULL, date NOT NULL, spent, PRIMARY KEY(context,date))')
        connection.commit()
        connection.close()

    timers_file = os.path.join(cfg['context_dir'], TIMERS_FILE)
    if os.path.exists(timers_file) == False:
        with open(timers_file, 'w') as fp:
            json.dump(dict(), fp, indent=2)

def today_is_in_db(context):
    cfg = config.read_config()
    timer_db = os.path.join(cfg['context_dir'], TIME_TRACK_DB)

    try:
        connection = sqlite3.connect(timer_db)
        cursor = connection.cursor()
        res = cursor.execute('SELECT count(*) FROM time_spent where context="{}" and date={}'.format(
            context, date.today().strftime('%Y%m%d')))
        occurrences = int(res.fetchone()[0])
        connection.close()
    except Exception as e:
        print(e)

    in_db = False
    if occurrences > 0:
        in_db = True

    return in_db

def get_time_spent(context, begin=None, end=None):
    today = date.today().strftime('%Y%m%d')
    if begin == None:
        begin = today
    if end == None:
        end = today

    if begin > end:
        begin = end
    if end < begin:
        end = begin

    cfg = config.read_config()
    timer_db = os.path.join(cfg['context_dir'], TIME_TRACK_DB)
    connection = sqlite3.connect(timer_db)
    cursor = connection.cursor()
    command = 'SELECT SUM(spent) FROM time_spent where context="{}" and date>={} and date<={}'.format(
        context, begin, end)
    res = cursor.execute(command)
    time_spent = res.fetchone()[0]
    connection.close()

    return time_spent

def pretty_time_spent(seconds):
    seconds = int(seconds)
    #days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    return '{:3}h {:2}m {:2}s'.format(hours, minutes, seconds)
    '''
    if days > 0:
        return '%dd %dh %dm %ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh %dm %ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm %ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)
    '''

def read_timers():
    cfg = config.read_config()
    timers_file = os.path.join(cfg['context_dir'], TIMERS_FILE)
    with open(timers_file) as fp:
        timers = json.load(fp)
    return timers

def write_timers(timers):
    cfg = config.read_config()
    timers_file = os.path.join(cfg['context_dir'], TIMERS_FILE)
    with open(timers_file, 'w') as fp:
        json.dump(timers, fp, indent=2)

def start_timer(context):
    timers = read_timers()
    timers[context] = time.time()
    write_timers(timers)

def stop_timer(context):
    timers = read_timers()
    current_time = time.time()

    if context in timers.keys():
        elapsed = current_time - timers[context]
        del timers[context]
    else:
        elapsed = 0

    write_timers(timers)

    if today_is_in_db(context):
        command = 'UPDATE time_spent SET spent=spent+{} where context="{}" and date={}'.format(
            elapsed, context, date.today().strftime('%Y%m%d'))
    else:
        command = 'INSERT INTO time_spent VALUES("{}", {}, "{}")'.format(
            context, date.today().strftime('%Y%m%d'), elapsed)
        
    cfg = config.read_config()
    timer_db = os.path.join(cfg['context_dir'], TIME_TRACK_DB)

    try:
        connection = sqlite3.connect(timer_db)
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        connection.close()
    except Exception as e:
        print(e)

def add_time_spent(context, elapsed):
    if today_is_in_db(context):
        command = 'UPDATE time_spent SET spent=spent+{} where context="{}" and date={}'.format(
            elapsed, context, date.today().strftime('%Y%m%d'))
    else:
        command = 'INSERT INTO time_spent VALUES("{}", {}, "{}")'.format(
            context, date.today().strftime('%Y%m%d'), elapsed)
        
    cfg = config.read_config()
    timer_db = os.path.join(cfg['context_dir'], TIME_TRACK_DB)

    try:
        connection = sqlite3.connect(timer_db)
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        connection.close()
    except Exception as e:
        print(e)

