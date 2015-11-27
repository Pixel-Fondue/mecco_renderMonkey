#python

DEFAULTS = {
    'filetype':'JPG',
    'frames':'1',
    'debug':True,
    'destination':'./frames/'
}

def get(key):
    if key in DEFAULTS:
        return DEFAULTS[key]
    else:
        return False