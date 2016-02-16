# python

from os.path import join

# Globals
KIT_ALIAS = 'kit_mecco_renderMonkey'
QUICK_BATCH_PATH = join('tmp', 'quick_batch.yaml')

# Blessings
CMD_BatchOpen = "monkey.BatchOpen"
CMD_BatchClose = "monkey.BatchClose"
CMD_BatchAddTask = "monkey.BatchAddTask"
CMD_BatchDeleteSel = "monkey.BatchDeleteSel"
CMD_BatchReorderSel = "monkey.BatchReorderSel"
CMD_BatchRender = "monkey.BatchRender"
CMD_BatchExample = "monkey.BatchExample"
CMD_BatchOpenInFilesystem = "monkey.BatchOpenInFilesystem"
CMD_BatchExportTemplate = 'monkey.BatchExportTemplate'
CMD_BatchRevealInFilesystem = 'monkey.BatchRevealInFilesystem'
CMD_BatchNew = 'monkey.BatchNew'
CMD_BatchSaveAs = 'monkey.BatchSaveAs'

# Special Node Names
BATCHFILE = "batch_file"
ADD_GENERIC = '(add...)'
ADD_TASK = '(add task...)'
ADD_PARAM = '(add control...)'
NO_FILE_SELECTED = "(no batch file)"

# Special Node Values
LIST = '(list)'
DICT = '(dict)'

# Useful Strings
TASK = 'Task'
SP = " "
EMPTY = ''

# Task Parameters
SCENE_PATH = "scene"
FORMAT = "format"
FRAMES = "frames"
COMMANDS = "commands"
DESTINATION = "destination"
PATTERN = "suffix"
GROUPS = "passgroups"
WIDTH = "frame_width"
HEIGHT = "frame_height"
OUTPUTS = "outputs"
CAMERA = "camera"
RENDER_CHANNELS = "render_channels"

# Status Messages
STATUS = "status"
STATUS_COMPLETE = "(Complete)"
STATUS_IN_PROGRESS = "(In progress...)"
STATUS_FAILED = "(Failed)"
STATUS_AVAILABLE = "(Available)"
STATUS_FILE_SUFFIX = "status"

# Treeview Basics
COL_NAME = "Name"
COL_VALUE = "Value"
SERVERNAME = 'RenderMonkeyBatch'
EMPTY_PROMPT = 'no batch file'
EMPTY_TASKS = 'no tasks'

TREE_ROOT_TITLE = 'Tasks'
IDENT = 'RMTV'
sSRV_USERNAME = "rendermonkeybatch"
NICE_NAME = "RenderMonkey_Batch"
OPEN_FILE_DIALOG_TITLE = 'Open File(s)'
VPTYPE = 'vpapplication'


# Node Types
REGIONS = [
    'batchFile',
    'batchTask',
    'taskParam',
    'taskParamMulti',
    'taskParamSub',
    'addNode',
    'null'
]
# Misc
LXO_FILE = '$LXOB'

# BatchReorderSel Arguments
REORDER_ARGS = {
    'TOP': 'top',
    'BOTTOM': 'bottom',
    'UP': 'up',
    'DOWN': 'down'
}

# Flags
fTREE_VIEW_ITEM_ATTR             = 0x00000001
fTREE_VIEW_ITEM_EXPAND           = 0x00000002
fTREE_VIEW_ATTR_EXPAND           = 0x00000004

# More Flags
fTREE_VIEW_ISTREE                = 0x00000001        # Cell has a tree-style layout
fTREE_VIEW_HASSUB                = 0x00000002        # Item has sub-items, causing an expansion arrow to be shown for ISTREE columns
fTREE_VIEW_EXPSUB                = 0x00000004        # Sub-items are expanded and the children are visible for ISTREE columns
fTREE_VIEW_HASATTR               = 0x00000008        # Item has attribute children, causing a +/- arrow to be shown for ISTREE columns
fTREE_VIEW_EXPATTR               = 0x00000010        # Attribute children are expanded and visible for ISTREE columns
fTREE_VIEW_DESCENDANT_SELECTED   = 0x00000020        # Item itself isn't selected, but any of it's descendants are
fTREE_VIEW_SELECTED              = 0x00000040        # Item itself is selected
fTREE_VIEW_PRIMARY               = 0x00000080        # Item is the primary selection
fTREE_VIEW_NOSELECT              = 0x00000100        # Item is not selectable, and should not show roll-over hilighting
fTREE_VIEW_INS_ABOVE             = 0x00000200        # Insertion line above the item
fTREE_VIEW_INS_BELOW             = 0x00000400        # Insertion line below the item
fTREE_VIEW_INS_SUB               = 0x00000800        # Insertion line as a child of the item
fTREE_VIEW_INS_ON                = 0x00001000        # Insertion line on the item (drop onto the item)
fTREE_VIEW_HIDDEN                = 0x00002000        # Item is hidden and will note be drawn.
fTREE_VIEW_ISATTR                = 0x00004000        # Item is an attribute of it's parent, instead of a normal child for ISTREE columns
fTREE_VIEW_ANCHOR                = 0x00008000        # Item represents the anchor for keyboard navigation.  Usually the primary selected item, assuming that item can be selected in the first place

# Even More Flags
fTREE_VIEW_ROWCOLOR_NONE         = 0x00000000        # No color
fTREE_VIEW_ROWCOLOR_RED          = 0x00010000
fTREE_VIEW_ROWCOLOR_MAGENTA      = 0x00020000
fTREE_VIEW_ROWCOLOR_PINK         = 0x00030000
fTREE_VIEW_ROWCOLOR_BROWN        = 0x00040000
fTREE_VIEW_ROWCOLOR_ORANGE       = 0x00050000
fTREE_VIEW_ROWCOLOR_YELLOW       = 0x00060000
fTREE_VIEW_ROWCOLOR_GREEN        = 0x00070000
fTREE_VIEW_ROWCOLOR_LIGHT_GREEN  = 0x00080000
fTREE_VIEW_ROWCOLOR_CYAN         = 0x00090000
fTREE_VIEW_ROWCOLOR_BLUE         = 0x000A0000
fTREE_VIEW_ROWCOLOR_LIGHT_BLUE   = 0x000B0000
fTREE_VIEW_ROWCOLOR_ULTRAMARINE  = 0x000C0000
fTREE_VIEW_ROWCOLOR_PURPLE       = 0x000D0000
fTREE_VIEW_ROWCOLOR_LIGHT_PURPLE = 0x000E0000
fTREE_VIEW_ROWCOLOR_DARK_GREY    = 0x000F0000
fTREE_VIEW_ROWCOLOR_GREY         = 0x00100000
fTREE_VIEW_ROWCOLOR_WHITE        = 0x00110000
