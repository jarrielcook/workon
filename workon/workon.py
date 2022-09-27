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
ARCHIVE_DIR='archive'
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

def get_functions():
    function_list = []

    funcdir = os.path.join(get_script_path(), 'function_dir')
    for f in os.listdir(funcdir):
        function_list.append(os.path.splitext(f)[0])

    return function_list

def get_archive():
    context_list = []

    ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR, ARCHIVE_DIR)
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

def find_command(command):
    cmdpath = ''
    for path in os.environ['PATH'].split(':'):
        if os.path.exists(os.path.join(path, command)):
            cmdpath = os.path.join(path,command)
            break

    return cmdpath

def close_context(context):
    current_context = {}
    try:
        ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, CURRENT_CONTEXT_FILE)
        with open(ctxfile) as fp:
            current_context = json.load(fp)
        
        for ctx,apps in current_context.items():
            if len(args.context) == 0 or ctx == args.context:
                for app,info in apps.items():
                    pid = info[0]
                    print("Stopping {} ({})".format(app, pid))
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except:
                        pass

                if len(args.context) > 0:
                    del current_context[ctx]

        if len(args.context) == 0:
            current_context = {}
    
    except Exception as e:
        pass
    
    #
    # Save current context info
    # 
    with open(ctxfile, 'w') as fp:
        json.dump(current_context, fp)
    
    return current_context

def read_context(context_name):
    ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, context_name + '.json')
    with open(ctxfile) as fp:
        context = json.load(fp)

    return context

def write_context(filename, context):
    with open(filename, 'w') as fp:
        json.dump(context, fp, indent=2)
        
def read_function(func):
    funcfile = os.path.join(get_script_path(), 'function_dir', '{}.func'.format(func))
    with open(funcfile) as fp:
        function = json.load(fp)

    return function

#
# Parse command line arguments
#
parser = argparse.ArgumentParser(description='Establish/switch project contexts.')

listing_group = parser.add_argument_group('List available contexts/pre-defined functions')
listing_group.add_argument('-l', '--list', dest='list', action='store_true', default=False,
                    help='List the available contexts')
listing_group.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                    help='Verbose output for listing')

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

parser.add_argument('context', nargs='?', default='', help='Name of the context to create/open/close')

args = parser.parse_args()

#
# Create context directory if it does not exist
#
try:
    # Create context directory
    ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
    os.mkdir(ctxdir)
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
    arcdir = os.path.join(os.environ['HOME'], CONTEXT_DIR, ARCHIVE_DIR)
    try:
        os.mkdir(arcdir)
    except:
        pass

    cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
    try:
        shutil.move(cfgfile, arcdir)
    except:
        print("Error archiving context: {}".format(args.context))

elif args.restore == True:
    # Create archive directory, if it doesn't exist
    arcfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, ARCHIVE_DIR, args.context + '.json')
    ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
    shutil.move(arcfile, ctxdir)
    

elif args.show == True:
    ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, CURRENT_CONTEXT_FILE)
    with open(ctxfile) as fp:
        current_context = json.load(fp)

    print(json.dumps(current_context, indent=2))

elif args.edit == True:
    cfgfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
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
        ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
        write_context(ctxfile, current_context)

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
                except:
                    pass

            try:
                toolname = toolname.replace("<name>", args.context)
            except:
                pass
            context[toolname] = newfunc

        if args.function == "treesheets":
            # Context treesheet storage
            treesheet_src = os.path.join(get_script_path(), 'template_dir', 'template.cts')
            support_dir = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context+'.files')
            treesheet_dst = os.path.join(support_dir, args.context+'.cts')
            try:
                os.mkdir(support_dir)
            except:
                pass
            shutil.copyfile(treesheet_src, treesheet_dst)

        ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context + '.json')
        write_context(ctxfile, context)

elif args.close == True:
    close_context(args.context)

else:
    if len(args.context) == 0:
        parser.print_help()
    else:
        #
        # End previous context (unless 'addtocontext' requested)
        #
        current_context = {}
        if args.addtocontext == False:
            current_context = close_context('')

        #
        # Start new context
        #
        config = read_context(args.context)
        
        app = {}

        try:
            support_dir = os.path.join(os.environ['HOME'], CONTEXT_DIR, args.context+'.files')
            os.chdir(support_dir)
        except:
            ctxdir = os.path.join(os.environ['HOME'], CONTEXT_DIR)
            os.chdir(ctxdir)

        for key,actions in config.items():
            command = actions['command']
            if command[0] != '/':
                command = find_command(command)

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

        current_context[args.context] = app
        
        #
        # Save current context info
        # 
        ctxfile = os.path.join(os.environ['HOME'], CONTEXT_DIR, CURRENT_CONTEXT_FILE)
        write_context(ctxfile, current_context)
        
        history = read_history()
        history[args.context] = str(time.time())
        write_history(history)
    
