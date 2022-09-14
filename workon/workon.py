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
ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
try:
    os.mkdir(ctxdir)
except:
    pass

if args.list == True:
    #
    # List available contexts
    #
    context_list = []
    for f in os.listdir(ctxdir):
        if f != CURRENT_CONTEXT_FILE and f != HISTORY_FILE and os.path.splitext(f)[1] == '.json':
            context_list.append(os.path.splitext(f)[0])

    history = read_history()

    history_list = []
    for ctx in context_list:
        if ctx in history:
            history_list.append(history[ctx])
        else:
            history_list.append(0)

    indices = np.argsort(history_list)

    for index in reversed(indices):
        if args.verbose and context_list[index] in history:
            datecode = datetime.fromtimestamp(float(history_list[index]))
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
        kanbansrc = os.path.join(os.environ['HOME'], CONTEXT_DIR, '.kanban')
        kanbandst = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context+'.kanban')

        # Session config file
        nmspc = {
            'commands': [('Kanban_{}'.format(args.context), '/usr/bin/firefox', '{}/index.html'.format(kanbandst))],
        }
        template_path = os.path.join(os.environ['HOME'], CONTEXT_DIR, '.template', 'context.json.tmpl')
        t = Template(file=template_path, searchList=nmspc)
        cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
        with open(cfgfile, 'w') as fp:
            fp.write(str(t))

        # Session kanban files
        shutil.copytree(kanbansrc, kanbandst)

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
            for key,pid in current_context.items():
                print("Stopping {}".format(key))
                try:
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass

            current_context = {}
            try:
                os.unlink(ctxfile)
            except:
                pass
    
    except:
        pass
    
    #
    # Start new context
    #
    cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
    with open(cfgfile) as fp:
        config = json.load(fp)
    
    for key,actions in config.items():
        command = actions['command']
        try:
            arguments = actions['args'].split()
        except:
            arguments = []
        spawnargs = tuple([command] + arguments)
        pid = os.spawnv(os.P_NOWAIT, command, spawnargs)
        current_context[key] = pid
    
    #
    # Save current context info
    # 
    with open(ctxfile, 'w') as fp:
        json.dump(current_context, fp)
    
    history = read_history()
    history[args.context] = str(time.time())
    write_history(history)
    
