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
from datetime import datetime
import zipfile

CONTEXT_DIR='.context'
CURRENT_CONTEXT_FILE='.current_context.json'
HISTORY_FILE='.history.json'

def read_history():
    histfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, HISTORY_FILE)
    try:
        with open(histfile, 'r') as fp:
            history = json.load(fp)
    except:
        history = {}
    return history

def write_history(history):
    histfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, HISTORY_FILE)
    with open(histfile, 'w') as fp:
        json.dump(history, fp)

def get_contexts():
    context_list = []

    ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
    for f in os.listdir(ctxdir):
        if f != CURRENT_CONTEXT_FILE and f != HISTORY_FILE and os.path.splitext(f)[1] == '.json':
            context_list.append(os.path.splitext(f)[0])

    return context_list

def extend_history(history, context):
    extended_hist = []
    for ctx in context:
        if ctx in history:
            extended_hist.append(history[ctx])
        else:
            extended_hist.append(0)

    return extended_hist

def get_script_path():
    return os.path.realpath(os.path.dirname(os.readlink(__file__)))

#
# Parse command line arguments
#
parser = argparse.ArgumentParser(description='Establish/switch project environments.')
parser.add_argument('-l', '--list', dest='list', action='store_true', default=False,
                    help='List the available contexts')
parser.add_argument('-c', '--create', dest='create', action='store_true', default=False,
                    help='Create a new context')
parser.add_argument('-a', '--add', dest='addtocontext', action='store_true', default=False,
                    help='Add to the current context')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                    help='Verbose output')
parser.add_argument('context', nargs='?', default='error', help='Name of the context to load/create')
args = parser.parse_args()

#
# Create context directory if it does not exist
#
try:
    # Create context directory
    ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
    os.mkdir(ctxdir)
    # Create "none" context
    template_path = os.path.join(get_script_path(), 'template_dir', 'none.json.tmpl')
    t = Template(file=template_path)
    nonefile = os.path.join(os.environ['HOME'], CONTEXT_DIR, 'none.json')
    with open(nonefile, 'w') as fp:
        fp.write(str(t))
except:
    pass

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

elif args.create == True:
    #
    # Create new context
    #
    if args.context == 'error':
        parser.print_help()
    else:
        kanbansrc = os.path.join(get_script_path(), 'kanban_dir.zip')
        kanbandst = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context+'.kanban')

        # Session config file
        nmspc = {
            'commands': [('Kanban_{}'.format(args.context), '/usr/bin/firefox', '{}/index.html'.format(kanbandst))],
        }
        template_path = os.path.join(get_script_path(), 'template_dir', 'context.json.tmpl')
        t = Template(file=template_path, searchList=nmspc)
        cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
        with open(cfgfile, 'w') as fp:
            fp.write(str(t))

        # Session kanban files
        with zipfile.ZipFile(kanbansrc, 'r') as zip_ref:
            zip_ref.extractall(kanbandst)

elif args.context == 'error':
        parser.print_help()

else:
    #
    # End previous context (unless 'addtocontext' requested)
    #
    current_context = {}
    try:
        ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, CURRENT_CONTEXT_FILE)
        with open(ctxfile) as fp:
            current_context = json.load(fp)
        
        if args.addtocontext == False:
            for ctx,apps in current_context.items():
                for app,pid in apps.items():
                    print("Stopping {}".format(app))
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except:
                        pass

            try:
                os.unlink(ctxfile)
            except:
                pass

            current_context = {}
    
    except Exception as e:
        pass
    
    #
    # Start new context
    #
    cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
    with open(cfgfile) as fp:
        config = json.load(fp)
    
    app = {}
    for key,actions in config.items():
        command = actions['command']
        try:
            arguments = actions['args'].split()
        except:
            arguments = []
        spawnargs = tuple([command] + arguments)
        pid = os.spawnv(os.P_NOWAIT, command, spawnargs)
        app[key] = pid

    current_context[args.context] = app
    
    #
    # Save current context info
    # 
    with open(ctxfile, 'w') as fp:
        json.dump(current_context, fp)
    
    history = read_history()
    history[args.context] = str(time.time())
    write_history(history)
    
