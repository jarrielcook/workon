import os
import sys
import json
import importlib
from workon import config,context,function

#
# Enhance module search path
#
cfg = config.read_config()
funcdir = os.path.join(cfg['context_dir'], 'function_dir')
sys.path.append(funcdir)

#
# Function storage
#
def get_functions():
    function_list = []

    cfg = config.read_config()
    funcdir = os.path.join(cfg['context_dir'], 'function_dir')
    for f in os.listdir(funcdir):
        extension = os.path.splitext(f)[1]
        if extension == ".func":
            function_list.append(os.path.splitext(f)[0])

    return function_list

def read_function(func):
    cfg = config.read_config()
    funcfile = os.path.join(cfg['context_dir'], 'function_dir', '{}.func'.format(func))
    with open(funcfile) as fp:
        function = json.load(fp)

    return function

def add_function_to_context(ctx_name, func):
    cfg = config.read_config()
    ctx = context.read_context(ctx_name)
    function = read_function(func)

    # Replace "<name>" with context name
    newfunc = {}
    module_name = ''
    for toolname,params in function.items():
        for key,val in params.items():
            try:
                if key == "command":
                    newfunc[key] = val.replace("<name>", ctx_name)
                    newfunc[key] = newfunc[key].replace("<context_dir>", cfg['context_dir'])
                elif key == "args":
                    newfunc[key] = val.replace("<name>", ctx_name)
                    newfunc[key] = newfunc[key].replace("<context_dir>", cfg['context_dir'])
                elif key == "env":
                    env = {}
                    for var,string in val.items():
                        try:
                            env[var] = string.replace("<name>", ctx_name)
                            env[var] = env[var].replace("<context_dir>", cfg['context_dir'])
                        except:
                            pass
                    newfunc[key] = env
                elif key == "module":
                    module_name = val
            except:
                pass

        try:
            toolname = toolname.replace("<name>", ctx_name)
            toolname = toolname.replace("<context_dir>", cfg['context_dir'])
        except:
            pass
        ctx[toolname] = newfunc

    # Initialize the function is an initialization module provided
    cfg = config.read_config()
    if len(module_name) > 0:
        toolmod = importlib.import_module(module_name)
        toolmod.init_function(cfg['context_dir'], ctx_name)

    ctxfile = os.path.join(os.environ['HOME'], cfg['context_dir'], ctx_name + '.json')
    context.write_context(ctxfile, ctx)
