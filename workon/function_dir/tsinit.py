import os
import shutil

def init_function(script_dir, context_dir, context_name):
    # Context treesheet storage
    treesheet_src = os.path.join(script_dir, 'template_dir', 'template.cts')
    support_dir = os.path.join(context_dir, context_name+'.files')
    treesheet_dst = os.path.join(support_dir, context_name+'.cts')
    try:
        os.mkdir(support_dir)
    except:
        pass
    shutil.copyfile(treesheet_src, treesheet_dst)

