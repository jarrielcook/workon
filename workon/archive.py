import os
import shutil
from workon import config

ARCHIVE_DIR='archive'

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


def move_to_archive(context):
    # Create archive directory, if it doesn't exist
    cfg = config.read_config()
    arcdir = os.path.join(cfg['context_dir'], ARCHIVE_DIR)
    try:
        os.mkdir(arcdir)
    except:
        pass

    cfgfile = os.path.join(cfg['context_dir'], context + '.json')
    support_dir = os.path.join(cfg['context_dir'], context+'.files')
    try:
        shutil.move(cfgfile, arcdir)
        if os.path.exists(support_dir):
            shutil.move(support_dir, arcdir)
    except Exception as e:
        print("Error archiving context: {} ({})".format(context, e))

def restore_from_archive(context):
    # Create archive directory, if it doesn't exist
    cfg = config.read_config()
    arcfile = os.path.join(cfg['context_dir'], ARCHIVE_DIR, context + '.json')
    support_dir = os.path.join(cfg['context_dir'], ARCHIVE_DIR, context+'.files')

    try:
        shutil.move(arcfile, cfg['context_dir'])

        if os.path.exists(support_dir):
            shutil.move(support_dir, cfg['context_dir'])
    except Exception as e:
        print("Error restoring context: {} ({})".format(context, e))
    
