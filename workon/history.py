import os
import json
from workon import config

HISTORY_FILE='.history.json'

#
# History Storage
#
def read_history():
    cfg = config.read_config()
    histfile = os.path.join(cfg['context_dir'], HISTORY_FILE)
    try:
        with open(histfile, 'r') as fp:
            hist = json.load(fp)
    except:
        hist = {}
    return hist

def write_history(hist):
    cfg = config.read_config()
    histfile = os.path.join(cfg['context_dir'], HISTORY_FILE)
    with open(histfile, 'w') as fp:
        json.dump(hist, fp)

def extended_history(hist, context):
    extended_hist = []
    for ctx in context:
        if ctx in hist:
            extended_hist.append(hist[ctx])
        else:
            extended_hist.append(0)

    return extended_hist


