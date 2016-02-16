# python

import lx
import os

from symbols import *

DEFAULTS = {
    'filetype': 'JPG',
    'frames': '1',
    'debug': True,
    'breakpoints': True,
    'destination': './frames/',
    'output_pattern': '[<pass>][<output>][<LR>]<FFFF>',
    'test_path': os.path.normpath(
        lx.eval("query platformservice alias ? {%s}" % "kit_mecco_renderMonkey:test/passGroups.lxo")
    ),
    'test_output_path': os.path.normpath(os.path.expanduser('~/Desktop/filename.xyz')),
    'test_passgroup': 'views',
    'test_passgroups': ['views', 'colors', 'shapes'],
    'test_framerange': '1-3,5,10-8',
    'test_camera': 'Camera',
    'test_render_channels': {'irrCache': False, 'globLimit': 5, 'aa': 's128'},
    'test_outputs': ['My Great Final Color Output'],
    'test_width': 128,
    'test_height': 128*(9/16),
    'test_single_frame': '1'
}


def get(key):
    if key in DEFAULTS:
        return DEFAULTS[key]
    else:
        return False

TASK_PARAMS = {
                FORMAT: DEFAULTS['filetype'],
                FRAMES: DEFAULTS['frames'],
                COMMANDS: [],
                DESTINATION: DEFAULTS['destination'],
                PATTERN: DEFAULTS['output_pattern'],
                GROUPS: [],
                WIDTH: None,
                HEIGHT: None,
                OUTPUTS: [],
                CAMERA: '',
                RENDER_CHANNELS: {}
            }