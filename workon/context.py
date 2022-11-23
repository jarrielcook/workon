import os
import json
from workon import config,tracking

CURRENT_CONTEXT_FILE='.current_context.json'

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
                tracking.stop_timer(ctx)

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


