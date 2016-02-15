# python

from os.path import join

KIT_ALIAS = 'kit_mecco_renderMonkey'
QUICK_BATCH_PATH = join('tmp', 'quick_batch.yaml')

CMD_OpenBatchFile = "monkey.OpenBatchFile"
CMD_CloseBatchFile = "monkey.CloseBatchFile"
CMD_AddBatchTask = "monkey.AddBatchTask"
CMD_RemoveBatchSel = "monkey.RemoveBatchSel"
CMD_RunCurrentBatch = "monkey.RunCurrentBatch"
CMD_ExampleBatch = "monkey.ExampleBatch"
CMD_OpenBatchInFilesystem = "monkey.OpenBatchInFilesystem"
CMD_echoSelected = "monkey.echoSelected"
CMD_batchTemplate = 'monkey.batchTemplate'
CMD_RevealBatchInFilesystem = 'monkey.RevealBatchInFilesystem'
CMD_NewBatchFile = 'monkey.NewBatchFile'
CMD_SaveBatchAs = 'monkey.SaveBatchAs'

BATCHFILE = "batch_file"
PARAMETERS = "parameters"
SCENE_PATH = "scene"
FORMAT = "format"
FRAMES = "frames"
DESTINATION = "destination"
PATTERN = "suffix"
GROUPS = "passgroups"
WIDTH = "frame_width"
HEIGHT = "frame_height"
OUTPUTS = "outputs"
CAMERA = "camera"
RENDER_CHANNELS = "render_channels"
STATUS = "status"
STATUS_COMPLETE = "(Complete)"
STATUS_IN_PROGRESS = "(In progress...)"
STATUS_FAILED = "(Failed)"
STATUS_AVAILABLE = "(Available)"
STATUS_FILE_SUFFIX = "status"

COL_NAME = "Name"
COL_VALUE = "Value"
SERVERNAME = 'RenderMonkeyBatch'
EMPTY_PROMPT = 'no batch file'
EMPTY_TASKS = 'no tasks'
ADD_GENERIC = '(add...)'
SELECT_BATCH_FILE_PROMPT = '(select batch file)'
NO_FILE_SELECTED = "(no batch file)"
TREE_ROOT_TITLE = 'Tasks'
TASK = 'Task'
SCENE = 'Scene'
ITEM = 'item'
LIST = '(list)'
DICT = '(dict)'
EMPTY = ''
ADD_TASK = '(add task...)'
ADD_PARAM = '(add control...)'
UPDATE_FROM_FILE = '(update)'
REPLACE_BATCH_FILE = '(open batch file...)'
IDENT = 'RMTV'
sSRV_USERNAME = "rendermonkeybatch"
NICE_NAME = "RenderMonkey_Batch"
OPEN_FILE_DIALOG_TITLE = 'Open File(s)'
LXO_FILE = '$LXOB'
VPTYPE = 'vpapplication'
SP = " "

NODETYPE_BATCHFILE = 'batchFile'
NODETYPE_BATCHTASK = 'batchTask'
NODETYPE_TASKPARAM = 'taskParam'
NODETYPE_TASKPARAM_MULTI = 'taskParamMulti'
NODETYPE_TASKPARAM_SUB = 'taskParamSub'
NODETYPE_ADDNODE = 'addNode'
NODETYPE_NULL = 'null'
