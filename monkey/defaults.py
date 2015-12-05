#python

import os, lx

DEFAULTS = {
    'filetype':'JPG',
    'frames':'1',
    'debug':True,
    'annoy':True,
    'destination':'./frames/',
    'output_pattern':'[<pass>][<output>][<LR>]<FFFF>',
    'test_path': os.path.normpath(lx.eval("query platformservice alias ? {%s}" % "kit_mecco_renderMonkey:test/passGroups.lxo")),
    'test_output_path': os.path.normpath(os.path.expanduser('~/Desktop/filename.xyz')),
    'test_passgroup':'views',
    'test_passgroups':['views','colors','shapes'],
    'test_framerange':'1-3,5,10-8'
}

def get(key):
    if key in DEFAULTS:
        return DEFAULTS[key]
    else:
        return False