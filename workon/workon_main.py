#!/usr/bin/python3

import json
import os
import sys
import time
import signal
import argparse
import shutil
from Cheetah.Template import Template
import numpy as np
from datetime import datetime,date
import zipfile
import importlib
import sqlite3
from workon import config

ARCHIVE_DIR='archive'
CURRENT_CONTEXT_FILE='.current_context.json'
HISTORY_FILE='.history.json'
TIME_TRACK_DB='.time_track.db'
TIMERS_FILE='.timers.json'

#
# Path Helpers
#
def get_script_path():
    return os.path.realpath(os.path.dirname(os.readlink(__file__)))

def find_command(command):
    cmdpath = ''
    for path in os.environ['PATH'].split(':'):
        if os.path.exists(os.path.join(path, command)):
            cmdpath = os.path.join(path,command)
            break

    return cmdpath

#
# History Storage
#
def read_history():
    cfg = config.read_config()
    histfile = os.path.join(cfg['context_dir'], HISTORY_FILE)
    try:
        with open(histfile, 'r') as fp:
            history = json.load(fp)
    except:
        history = {}
    return history

def write_history(history):
    cfg = config.read_config()
    histfile = os.path.join(cfg['context_dir'], HISTORY_FILE)
    with open(histfile, 'w') as fp:
        json.dump(history, fp)

def extend_history(history, context):
    extended_hist = []
    for ctx in context:
        if ctx in history:
            extended_hist.append(history[ctx])
        else:
            extended_hist.append(0)

    return extended_hist

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

#
# Timer Storage
#
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

#
# Context storage
#
def get_contexts():
    context_list = []

    cfg = config.read_config()
    for f in os.listdir(cfg['context_dir']):
        if f[0] != '.' and os.path.splitext(f)[1] == '.json':
            context_list.append(os.path.splitext(f)[0])

    return context_list

def read_context(context_name):
    cfg = config.read_config()
    ctxfile = os.path.join(cfg['context_dir'], context_name + '.json')
    with open(ctxfile) as fp:
        context = json.load(fp)

    return context

def write_context(filename, context):
    with open(filename, 'w') as fp:
        json.dump(context, fp, indent=2)
        
def read_current_context():
    cfg = config.read_config()
    ctxfile = os.path.join(cfg['context_dir'], CURRENT_CONTEXT_FILE)
    with open(ctxfile) as fp:
        current_context = json.load(fp)

    return current_context
        
def write_current_context(current_context):
    cfg = config.read_config()
    ctxfile = os.path.join(cfg['context_dir'], CURRENT_CONTEXT_FILE)
    write_context(ctxfile, current_context)

def close_context(context=''):
    current_context = {}
    try:
        current_context = read_current_context()

        for ctx,apps in current_context.items():
            if len(context) == 0 or ctx == context:
                stop_timer(ctx)

                for app,info in apps.items():
                    pid = info[0]
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except:
                        pass

                if len(context) > 0:
                    del current_context[ctx]

        if len(context) == 0:
            current_context = {}

    except Exception as e:
        pass
    
    #
    # Save current context info
    # 
    write_current_context(current_context)
    
    return current_context

#
# Function storage
#
def get_functions():
    function_list = []

    funcdir = os.path.join(get_script_path(), 'function_dir')
    for f in os.listdir(funcdir):
        extension = os.path.splitext(f)[1]
        if extension == ".func":
            function_list.append(os.path.splitext(f)[0])

    return function_list

def read_function(func):
    funcfile = os.path.join(get_script_path(), 'function_dir', '{}.func'.format(func))
    with open(funcfile) as fp:
        function = json.load(fp)

    return function

#
# Archive storage
#
def get_archive():
    context_list = []

    cfg = config.read_config()
    arcdir = os.path.join(cfg['context_dir'], ARCHIVE_DIR)
    for f in os.listdir(arcdir):
        if f[0] != '.' and os.path.splitext(f)[1] == '.json':
            context_list.append(os.path.splitext(f)[0])

    return context_list


#
# Enhance module search path
#
funcdir = os.path.join(get_script_path(), 'function_dir')
sys.path.append(funcdir)

#
# Parse command line arguments
#
parser = argparse.ArgumentParser(description='Establish/switch project contexts.')

listing_group = parser.add_argument_group('List available contexts/pre-defined functions')
listing_group.add_argument('-l', '--list', dest='list', action='store_true', default=False,
                    help='List the available contexts')
listing_group.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                    help='Verbose output for listing (shows pre-defined functions)')

modify_group = parser.add_argument_group('Change/show running context')
modify_group.add_argument('-c', '--close', dest='close', action='store_true', default=False,
                    help='Close a running context')
modify_group.add_argument('-a', '--add', dest='addtocontext', action='store_true', default=False,
                    help='Add to the current running context')
modify_group.add_argument('-s', '--show', dest='show', action='store_true', default=False,
                    help='Show the current running context')

edit_group = parser.add_argument_group('Edit context definition')
edit_group.add_argument('-n', '--new', dest='create', action='store_true', default=False,
                    help='Create a new context')
edit_group.add_argument('-e', '--edit', dest='edit', action='store_true', default=False,
                    help='Edit a context definition')
edit_group.add_argument('-f', '--function', dest='function', 
                    help='Add/list pre-defined function to a context definition')

archive_group = parser.add_argument_group('Archive')
archive_group.add_argument('--archive', dest='archive', action='store_true', default=False,
                    help='Archive a context. Can be restored later.')
archive_group.add_argument('--restore', dest='restore', action='store_true', default=False,
                    help='Restore a context from the archive.')
archive_group.add_argument('--list-archive', dest='list_archive', action='store_true', default=False,
                    help='List the contexts in the archive.')

time_group = parser.add_argument_group('Time Tracking')
time_group.add_argument('--time-spent', dest='time_spent', action='store_true', default=False,
                    help='Display the amount of time spent in a context.')
time_group.add_argument('--date-begin', dest='date_begin', 
                    type=str, default=date.today().strftime('%Y%m%d'),
                    help='Beginning date for time spent. Format: YYYYMMDD')
time_group.add_argument('--date-end', dest='date_end', 
                    type=str, default=date.today().strftime('%Y%m%d'),
                    help='End date for time spent. Format: YYYYMMDD')
time_group.add_argument('--add-time', dest='additional_time',
                    type=str, default='',
                    help='Elapsed time to add. Format: HH:MM:SS')

parser.add_argument('context', nargs='?', default='', help='Name of the context to create/open/close')

args = parser.parse_args()

#
# Create context directory if it does not exist
#
try:
    # Create context directory
    cfg = config.read_config()
    os.mkdir(cfg['context_dir'])
except:
    pass

try:
    # Create time tracking database
    create_time_spent_db()
except:
    pass


#
# Execute User Instruction
#
if args.list == True:
    #
    # List available contexts
    #
    context_list = get_contexts()
    history = read_history()
    extended_hist = extend_history(history, context_list)

    # Display list of contexts in reverse order by last access time
    indices = np.argsort(extended_hist)
    for index in reversed(indices):
        if args.verbose and context_list[index] in history:
            datecode = datetime.fromtimestamp(float(extended_hist[index]))
            datestr = datecode.strftime("%d/%m/%Y %H:%M:%S")
            print('{:.<16} (Last access: {})'.format(context_list[index], datestr))
        else:
            print('{}'.format(context_list[index]))

    if args.verbose:
        print('=== Available Functions ===')
        function_list = get_functions()
        for func in function_list:
            print('{}'.format(func))

elif args.list_archive == True:
    #
    # List available contexts
    #
    archive_list = get_archive()

    # Display list of contexts in reverse order by last access time
    for arc in archive_list:
        print('{}'.format(arc))


elif args.archive == True:
    # Create archive directory, if it doesn't exist
    cfg = config.read_config()
    arcdir = os.path.join(cfg['context_dir'], ARCHIVE_DIR)
    try:
        os.mkdir(arcdir)
    except:
        pass

    cfgfile = os.path.join(cfg['context_dir'], args.context + '.json')
    support_dir = os.path.join(cfg['context_dir'], args.context+'.files')
    try:
        shutil.move(cfgfile, arcdir)
        shutil.move(support_dir, arcdir)
    except:
        print("Error archiving context: {}".format(args.context))

elif args.restore == True:
    # Create archive directory, if it doesn't exist
    cfg = config.read_config()
    arcfile = os.path.join(cfg['context_dir'], ARCHIVE_DIR, args.context + '.json')
    support_dir = os.path.join(cfg['context_dir'], ARCHIVE_DIR, args.context+'.files')

    try:
        shutil.move(arcfile, cfg['context_dir'])
        shutil.move(support_dir, cfg['context_dir'])
    except:
        print("Error restoring context: {}".format(args.context))
    

elif args.show == True:
    current_context = read_current_context()
    print(json.dumps(current_context, indent=2))

elif args.edit == True:
    cfg = config.read_config()
    cfgfile = os.path.join(cfg['context_dir'], args.context + '.json')
    editor = find_command(os.environ['EDITOR'])
    if len(editor) > 0:
        spawnargs = tuple([editor] + [cfgfile])
        os.spawnv(os.P_NOWAIT, editor, spawnargs)
    else:
        print("Cannot find editor: {}".format(os.environ['EDITOR']))

elif args.create == True:
    #
    # Create new context
    #
    if len(args.context) == 0:
        parser.print_help()
    else:
        # Context context file
        cfg = config.read_config()
        ctxfile = os.path.join(cfg['context_dir'], args.context + '.json')
        write_context(ctxfile, dict())
        # Create directory for context
        ctxfiles = os.path.join(cfg['context_dir'], args.context + '.files')
        os.mkdir(ctxfiles)

elif args.function != None:
    #
    # Create new context
    #
    if len(args.context) == 0:
        parser.print_help()
    else:

        context = read_context(args.context)
        function = read_function(args.function)

        # Replace "<name>" with context name
        newfunc = {}
        module_name = ''
        for toolname,params in function.items():
            for key,val in params.items():
                try:
                    if key == "command":
                        newfunc[key] = val.replace("<name>", args.context)
                    elif key == "args":
                        newfunc[key] = val.replace("<name>", args.context)
                    elif key == "env":
                        env = {}
                        for var,string in val.items():
                            try:
                                env[var] = string.replace("<name>", args.context)
                            except:
                                pass
                        newfunc[key] = env
                    elif key == "module":
                        module_name = val
                except:
                    pass

            try:
                toolname = toolname.replace("<name>", args.context)
            except:
                pass
            context[toolname] = newfunc

        # Initialize the function is an initialization module provided
        cfg = config.read_config()
        if len(module_name) > 0:
            toolmod = importlib.import_module(module_name)
            toolmod.init_function(get_script_path(), cfg['context_dir'], args.context)

        ctxfile = os.path.join(os.environ['HOME'], cfg['context_dir'], args.context + '.json')
        write_context(ctxfile, context)

elif args.time_spent == True:
    context_list = get_contexts()
    total = 0
    for ctx in context_list:
        spent = get_time_spent(ctx, args.date_begin, args.date_end)
        if spent != None:
            print('{:.<16} (Time spent: {})'.format(ctx, pretty_time_spent(spent)))
            total = total + spent
    print('{:.<16} (Time spent: {})'.format('TOTAL', pretty_time_spent(total)))

elif len(args.additional_time) > 0:
    t0 = datetime.strptime('0','%S')
    t1 = datetime.strptime(args.additional_time, '%H:%M:%S')
    elapsed = (t1-t0).total_seconds()
    print('Adding {} seconds to {} context'.format(elapsed, args.context))
    add_time_spent(args.context, elapsed)

elif args.close == True:
    close_context(args.context)

else:
    if len(args.context) == 0:
        parser.print_help()
    else:
        #
        # End previous context (unless 'addtocontext' requested)
        #
        if args.addtocontext == False:
            current_context = close_context()
        else:
            current_context = read_current_context()

        #
        # Start new context
        #
        ctx = read_context(args.context)
        
        app = {}

        cfg = config.read_config()
        try:
            support_dir = os.path.join(cfg['context_dir'], args.context+'.files')
            os.chdir(support_dir)
        except:
            os.chdir(cfg['context_dir'])

        for key,actions in ctx.items():
            command = actions['command']
            if command[0] != '/':
                command = find_command(command)

            if len(command) > 0:
                try:
                    arguments = actions['args'].split()
                except:
                    arguments = []

                try:
                    envars = actions['env']
                except:
                    envars = {}

                spawnenv = os.environ
                for var,val in envars.items():
                    spawnenv[key] = val

                spawnargs = tuple([command] + arguments)
                pid = os.spawnve(os.P_NOWAIT, command, spawnargs, spawnenv)
                app[key] = (pid,time.time())
            else:
                print('Error finding command: {}'.format(actions['command']))

        current_context[args.context] = app
        start_timer(args.context)
        
        #
        # Save current context info
        # 
        write_current_context(current_context)
        
        history = read_history()
        history[args.context] = str(time.time())
        write_history(history)
    
