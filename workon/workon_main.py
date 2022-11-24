#!/usr/bin/python3

import json
import os
import sys
import time
import argparse
import shutil
import numpy as np
from datetime import datetime,date
from workon import config,context,history,tracking,archive,function

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
# Create directories if they do not exist
#
try:
    # Create context directory
    cfg = config.read_config()
    os.mkdir(cfg['context_dir'])
except:
    pass

try:
    # Create function directory
    cfg = config.read_config()
    func_dir = os.path.join(cfg['context_dir'], 'function_dir')
    src_dir = os.path.join(get_script_path(), 'function_dir')
    shutil.copytree(src_dir, func_dir)
except:
    pass

try:
    # Create template directory
    cfg = config.read_config()
    tmpl_dir = os.path.join(cfg['context_dir'], 'template_dir')
    src_dir = os.path.join(get_script_path(), 'template_dir')
    shutil.copytree(src_dir, tmpl_dir)
except:
    pass

try:
    # Create time tracking database
    tracking.create_time_spent_db()
except:
    pass


#
# Execute User Instruction
#
if args.list == True:
    #
    # List available contexts
    #
    context_list = context.get_contexts()
    hist = history.read_history()
    extended_hist = history.extended_history(hist, context_list)

    # Display list of contexts in reverse order by last access time
    indices = np.argsort(extended_hist)
    for index in reversed(indices):
        if args.verbose and context_list[index] in hist:
            datecode = datetime.fromtimestamp(float(extended_hist[index]))
            datestr = datecode.strftime("%d/%m/%Y %H:%M:%S")
            print('{:.<16} (Last access: {})'.format(context_list[index], datestr))
        else:
            print('{}'.format(context_list[index]))

    if args.verbose:
        print('=== Available Functions ===')
        function_list = function.get_functions()
        for func in function_list:
            print('{}'.format(func))

elif args.list_archive == True:
    #
    # List available contexts
    #
    archive_list = archive.get_archive()

    # Display list
    for arc in archive_list:
        print('{}'.format(arc))


elif args.archive == True:
    archive.move_to_archive(args.context)

elif args.restore == True:
    archive.restore_from_archive(args.context)

elif args.show == True:
    current_context = context.read_current_context()
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
        context.write_context(ctxfile, dict())
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
        function.add_function_to_context(args.context, args.function)

elif args.time_spent == True:
    context_list = context.get_contexts()
    total = 0
    for ctx in context_list:
        spent = tracking.get_time_spent(ctx, args.date_begin, args.date_end)
        if spent != None:
            print('{:.<16} (Time spent: {})'.format(ctx, tracking.pretty_time_spent(spent)))
            total = total + spent
    print('{:.<16} (Time spent: {})'.format('TOTAL', tracking.pretty_time_spent(total)))

elif len(args.additional_time) > 0:
    t0 = datetime.strptime('0','%S')
    t1 = datetime.strptime(args.additional_time, '%H:%M:%S')
    elapsed = (t1-t0).total_seconds()
    print('Adding {} seconds to {} context'.format(elapsed, args.context))
    tracking.add_time_spent(args.context, elapsed)

elif args.close == True:
    context.close_context(args.context)

else:
    if len(args.context) == 0:
        parser.print_help()
    else:
        #
        # End previous context (unless 'addtocontext' requested)
        #
        if args.addtocontext == False:
            current_context = context.close_context()
        else:
            current_context = context.read_current_context()

        #
        # Start new context
        #
        ctx = context.read_context(args.context)
        
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
        tracking.start_timer(args.context)
        
        #
        # Save current context info
        # 
        context.write_current_context(current_context)
        
        hist = history.read_history()
        hist[args.context] = str(time.time())
        history.write_history(hist)
    
