#python

DEFAULTS = {
    'filetype':'JPG',
    'frames':'1',
    'debug':True,
    'annoy':False,
    'destination':'./frames/',
    'output_pattern':'[<pass>][<output>][<LR>]<FFFF>'
}

def get(key):
    if key in DEFAULTS:
        return DEFAULTS[key]
    else:
        return False