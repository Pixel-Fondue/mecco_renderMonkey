# python

import lx
import lxu
import lxifc
import modo
import monkey
import traceback
import os
import sys

try:
    import wingdbstub
except:
    pass
    
SERVERNAME = 'RenderMonkeyBatch'
EMPTY_PROMPT = '(no tasks)'
ADD_GENERIC = '(add...)'
SELECT_BATCH_FILE_PROMPT = '(select batch file)'
TREE_ROOT_TITLE = 'Tasks'
TASK = 'Task'
LIST = '(list)'
DICT = '(dict)'
EMPTY = ''
ADD_TASK = '(add task...)'
ADD_PARAM = '(add parameter...)'
UPDATE_FROM_FILE = '(update)'
REPLACE_BATCH_FILE = '(open batch file...)'
ADD_PARAMETER = '(add parameter...)'
IDENT = 'RMTV'
sSRV_USERNAME = "rendermonkeybatch"
NICE_NAME = "RenderMonkey_Batch"
OPEN_FILE_DIALOG_TITLE = 'Open File(s)'
LXO_FILE = '$LXOB'
VPTYPE = 'vpapplication'

CMD_requestBatchFile = "monkey.requestBatchFile"
CMD_addBatchTask = "monkey.addBatchTask"
CMD_runCurrentBatch = "monkey.runCurrentBatch"
CMD_exampleBatch = "monkey.exampleBatch"
CMD_openBatchInFilesystem = "monkey.openBatchInFilesystem"
CMD_echoSelected = "monkey.echoSelected"

PATH = monkey.symbols.SCENE_PATH
FORMAT = monkey.symbols.FORMAT
FRAMES = monkey.symbols.FRAMES
DESTINATION = monkey.symbols.DESTINATION
PATTERN = monkey.symbols.PATTERN
GROUPS = monkey.symbols.GROUPS
WIDTH = monkey.symbols.WIDTH
HEIGHT = monkey.symbols.HEIGHT
OUTPUTS = monkey.symbols.OUTPUTS
CAMERA = monkey.symbols.CAMERA
RENDER_CHANNELS = monkey.symbols.RENDER_CHANNELS

# -------------------------------------------------------------------------
# Node styles
# -------------------------------------------------------------------------

# Icons added via markup in the string itself.
# "\x03(i:uiicon_bm_overlay) Some text" < Adds icon resource "bm_overlay" to cell

fTREE_VIEW_ITEM_ATTR = 0x00000001
fTREE_VIEW_ITEM_EXPAND = 0x00000002
fTREE_VIEW_ATTR_EXPAND = 0x00000004

# -------------------------------------------------------------------------
# Generic layer node object that represents each entry in the tree
# -------------------------------------------------------------------------


class rm_TreeNode(object):

    _Primary = None

    def __init__(self, name, value=None, parent=None):
        self.name = name
        self.value = value
        self.parent = parent
        self.children = []
        self.state = 0
        self.selected = False

        # For column sizes you can use proportions via negative values.
        # So -1 and -2 would mean that one column is half the size of the other
        # (total size would be 3 units,
        # so the -1 column is 1 unit and -2 column is 2 units).
        # You can mix pixel sizes with proportional sizes,
        # so -1 and 90 means that one is 90 pixels
        # and the other takes up the remaining space.
        self.columns = (("Name", -1),
                        ("Value", -4))

        self.toolTips = {}

    def AddNode(self, name, value=""):
        self.children.append(rm_TreeNode(name, value, self))
        return self.children[-1]

    def ClearSelection(self):

        if self._Primary:
            self.setPrimary()

        self.SetSelected(False)

        for child in self.children:
            child.ClearSelection()

    def SetSelected(self, val=True):

        if val:
            self.setPrimary(self)
        self.selected = val

    def isSelected(self):
        return self.selected

    @classmethod
    def setPrimary(cls, primary=None):
        cls._Primary = primary

    @classmethod
    def getPrimary(cls):
        return cls._Primary

    def setState(self, flag):
        self.state = self.state | flag

    def setToolTip(self, idx, tip):
        self.toolTips[idx] = tip

    def getToolTip(self, idx):
        if idx in self.toolTips:
            return self.toolTips[idx]

    def getValue(self):
        return str(self.value)
    
    def getName(self):
        return str(self.name)
    
    def getSelectedChildren(self,recursive=True):
        sel = []
        for i in self.children:
            if i.isSelected():
                sel.append(i)
            if recursive:
                sel += i.getSelectedChildren()
                
        return sel
    
    def getPath(self,path=[]):
        if self.parent:
            return self.parent.getPath() + [self]
        else:
            return path
        
    def getIndexPath(self):
        path = self.getPath()
        indexPath = []
        for i in path:
            indexPath.append(i.name)
        return indexPath

# -------------------------------------------------------------------------
# Batch data model
# -------------------------------------------------------------------------


class rm_Batch:
    
    def __init__(self, batchFilePath='', batch=[]):
        self._batchFilePath = batchFilePath
        self._batch = batch
        self._tree = rm_TreeNode(TREE_ROOT_TITLE,LIST)
        
        if self._batchFilePath:
            self.update_batch_from_file()
        
        self.rebuild_tree()

    def add_task(self, paths_list):
        try:
            if not paths_list:
                return False

            if not isinstance(paths_list, list):
                paths_list = [paths_list]

            for path in paths_list:
                self._batch.append({
                    PATH: path,
                    FORMAT: monkey.defaults.get('filetype'),
                    FRAMES: monkey.defaults.get('frames'),
                    DESTINATION: monkey.defaults.get('destination'),
                    PATTERN: monkey.defaults.get('output_pattern'),
                    GROUPS: [],
                    WIDTH: None,
                    HEIGHT: None,
                    OUTPUTS: '',
                    CAMERA: '',
                    RENDER_CHANNELS: {}
                })

            self.save_batch_to_file()
            self.rebuild_tree()
                
            return self._batch

        except:
            lx.out(traceback.print_exc())
            return False

    def clear_all_task_parameters(self, task_index):
        try:
            self._batch[task_index] = {}
                
            self.save_batch_to_file()
            self.rebuild_tree()
                
            return self._batch[task_index]

        except:
            lx.out(traceback.print_exc())
            return False

    def clear_task_parameters(self, task_index, parameters_list):
        try:
            for p in parameters_list:
                if p in self._batch[task_index]:
                    del self._batch[task_index][p]
                
            self.save_batch_to_file()
            self.rebuild_tree()
                
            return self._batch[task_index]

        except:
            lx.out(traceback.print_exc())
            return False
        
    def edit_task(self, task_index, parameters_dict):
        try:
            for k, v in parameters_dict.iteritems():
                self._batch[task_index][k] = v

            self.save_batch_to_file()
            self.rebuild_tree()
                
            return self._batch[task_index]

        except:
            lx.out(traceback.print_exc())
            return False
        
    def update_batch_from_file(self, file_path=None):
        try:
            if file_path is None:
                file_path = self._batchFilePath
            else:
                self._batchFilePath = file_path

            self._batch = monkey.util.read_yaml(file_path)
            self.rebuild_tree()
            
            return self._batch
        except:
            lx.out(traceback.print_exc())
            return False

    def save_batch_to_file(self, file_path=None):
        try:
            if file_path:
                return monkey.util.write_yaml(self._batch, file_path)
            
            elif self._batchFilePath:
                return monkey.util.write_yaml(self._batch, self._batchFilePath)

            else:
                return self.save_batch_as()
            
        except:
            lx.out(traceback.print_exc())
            return False

    def save_batch_as(self, file_path=None):
        try:
            if file_path:
                self._batchFilePath = file_path
                return self.save_batch_to_file()
            else:
                return self.save_batch_to_file(
                    monkey.util.yaml_save_dialog()
                )
        except:
            lx.out(traceback.print_exc())
            return False

    def rebuild_tree(self, batch=None):
        try:
            if batch:
                self._batch = batch

            if not self._batch:
                return self.build_empty_tree()

            self.kill_the_kids()
            for o, i in enumerate(self._batch):
                if i[PATH]:
                    j = self._tree.AddNode(o, os.path.basename(i[PATH]))
                    for k, v in iter(sorted(i.iteritems())):
                        if isinstance(v,(list,tuple)):
                            l = j.AddNode(k,LIST)
                            for n, m in enumerate(v):
                                l.AddNode(n,m)
#                            l.AddNode(EMPTY,ADD_GENERIC)
                        elif isinstance(v,dict):
                            l = j.AddNode(k,DICT)
                            for m, n in v.iteritems():
                                l.AddNode(m,n)
#                            l.AddNode(EMPTY,ADD_GENERIC)
                        else:
                            j.AddNode(k, v)
#                    j.AddNode(ADD_PARAM,EMPTY)
                            
#            self._tree.AddNode(ADD_TASK,EMPTY)
#            self._tree.AddNode(EMPTY, UPDATE_FROM_FILE)
#            self._tree.AddNode(EMPTY, REPLACE_BATCH_FILE)
            
            return self._tree

        except:
            lx.out(traceback.print_exc())
            return False
        
    def build_empty_tree(self):
        try:
            self.kill_the_kids()
            self._tree.AddNode(EMPTY,EMPTY_PROMPT)
            return self._tree
        except:
            lx.out(traceback.print_exc())
            return False
    
    def kill_the_kids(self):
        try:
            self._tree.children = []
        except:
            lx.out(traceback.print_exc())
            return False
    
    def batch_file_path(self):
        return self._batchFilePath
    
    
# -------------------------------------------------------------------------
# Tree View
# -------------------------------------------------------------------------

# Not sure why this variable needs to be external to the view object,
# but it does. (Crash.)
_BATCH = rm_Batch()


class rm_BatchView(lxifc.TreeView,
                        lxifc.Tree,
                        lxifc.ListenerPort,
                        lxifc.Attributes
                        ):

    # Gloabal list of all created tree views.
    # These are used for shape and attribute changes
    _listenerClients = {}

    def __init__(self, node=None, curIndex=0):

        if node is None:
            node = _BATCH._tree

        self._currentNode = node
        self._currentIndex = curIndex

    # -------------------------------------------------------------------------
    # Listener port
    # -------------------------------------------------------------------------

    @classmethod
    def addListenerClient(cls, listener):
        """
            Whenever a new tree view is created, we will add
            a copy of its listener so that it can be notified
            of attribute or shape changes
        """
        treeListenerObj = lx.object.TreeListener(listener)
        cls._listenerClients[treeListenerObj.__peekobj__()] = treeListenerObj

    @classmethod
    def removeListenerClient(cls, listener):
        """
            When a view is destroyed, it will be removed from
            the list of clients that need notification.
        """
        treeListenerObject = lx.object.TreeListener(listener)
        if treeListenerObject.__peekobj__() in cls._listenerClients:
            del cls._listenerClients[treeListenerObject.__peekobj__()]

    @classmethod
    def notify_NewShape(cls):
        for client in cls._listenerClients.values():
            if client.test():
                client.NewShape()

    @classmethod
    def notify_NewAttributes(cls):
        for client in cls._listenerClients.values():
            if client.test():
                client.NewAttributes()

    # -----------------------------------------------------------------------

    def lport_AddListener(self, obj):
        """
            Called from core code with the object that wants to
            bind to the listener port
        """
        self.addListenerClient(obj)

    def lport_RemoveListener(self, obj):
        """
            Called from core when a listener needs to be removed from
            the port.
        """
        self.removeListenerClient(obj)

    # -------------------------------------------------------------------------
    # Target layer in the tree
    # -------------------------------------------------------------------------

    def targetNode(self):
        """
            Returns the targeted layer node in the current tier
        """
        return self._currentNode.children[self._currentIndex]

    # -------------------------------------------------------------------------
    # Each time the tree is spawned, we create a copy of ourselves at current
    # location in the tree and return it
    # -------------------------------------------------------------------------

    def tree_Spawn(self, mode):
        """
            Spawn a new instance of this tier in the tree.
        """

        # create an instance of our current location in the tree
        newTree = rm_BatchView(self._currentNode, self._currentIndex)

        # Convert to a tree interface
        newTreeObj = lx.object.Tree(newTree)

        if mode == lx.symbol.iTREE_PARENT:
            newTreeObj.ToParent()

        elif mode == lx.symbol.iTREE_CHILD:
            newTreeObj.ToChild()

        elif mode == lx.symbol.iTREE_ROOT:
            newTreeObj.ToRoot()

        return newTreeObj

    def tree_ToParent(self):
        """
            Step up to the parent tier and set the selection in this
            tier to the current items index
        """
        parent = self._currentNode.parent

        if parent:
            self._currentIndex = parent.children.index(self._currentNode)
            self._currentNode = parent

    def tree_ToChild(self):
        """
            Move to the child tier and set the selected node
        """
        self._currentNode = self._currentNode.children[self._currentIndex]

    def tree_ToRoot(self):
        """
            Move back to the root tier of the tree
        """
        self._currentNode = _BATCH._tree

    def tree_IsRoot(self):
        """
            Check if the current tier in the tree is the root tier
        """
        if self._currentNode is _BATCH._tree:
            return True
        else:
            return False

    def tree_ChildIsLeaf(self):
        """
            If the current tier has no children then it is
            considered a leaf
        """
        if len(self._currentNode.children) > 0:
            return False
        else:
            return True

    def tree_Count(self):
        """
            Returns the number of nodes in this tier of
            the tree
        """
        return len(self._currentNode.children)

    def tree_Current(self):
        """
            Returns the index of the currently targeted item in
            this tier
        """
        return self._currentIndex

    def tree_SetCurrent(self, index):
        """
            Sets the index of the item to target in this tier
        """
        self._currentIndex = index

    def tree_ItemState(self, guid):
        """
            Returns the item flags that define the state.

        """
        return self.targetNode().state

    def tree_SetItemState(self, guid, state):
        """
            Set the item flags that define the state.

        """
        self.targetNode().state = state

    # -------------------------------------------------------------------------
    # Tree view
    # -------------------------------------------------------------------------

    def treeview_StoreState(self, uid):
        lx.notimpl()

    def treeview_RestoreState(self, uid):
        lx.notimpl()

    def treeview_ColumnCount(self):
        return len(_BATCH._tree.columns)

    def treeview_ColumnByIndex(self, columnIndex):
        return _BATCH._tree.columns[columnIndex]

    def treeview_ToPrimary(self):
        """
            Move the tree to the primary selection
        """
        if self._currentNode._Primary:
            self._currentNode = self._currentNode._Primary
            self.tree_ToParent()
            return True
        return False

    def treeview_IsSelected(self):
        return self.targetNode().isSelected()

    def treeview_Select(self, mode):

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY or \
           mode == lx.symbol.iTREEVIEW_SELECT_ADD:
                
            _BATCH._tree.ClearSelection()
            self.targetNode().SetSelected()
            

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().SetSelected(False)

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            _BATCH._tree.ClearSelection()

    def treeview_CellCommand(self, columnIndex):
        lx.notimpl()

    def treeview_BatchCommand(self, columnIndex):
        lx.notimpl()

    def treeview_ToolTip(self, columnIndex):
        toolTip = self.targetNode().getToolTip(columnIndex)
        if toolTip:
            return toolTip
        lx.notimpl()

    def treeview_BadgeType(self, columnIndex, badgeIndex):
        lx.notimpl()

    def treeview_BadgeDetail(self, columnIndex, badgeIndex, badgeDetail):
        lx.notimpl()

    def treeview_IsInputRegion(self, columnIndex, regionID):
        lx.notimpl()

    def treeview_SupportedDragDropSourceTypes(self, columnIndex):
        lx.notimpl()

    def treeview_GetDragDropSourceObject(self, columnIndex, type):
        lx.notimpl()

    def treeview_GetDragDropDestinationObject(self, columnIndex):
        lx.notimpl()

    # -------------------------------------------------------------------------
    # Attributes
    # -------------------------------------------------------------------------

    def attr_Count(self):
        return len(_BATCH._tree.columns)

    def attr_GetString(self, index):
        if index == 0:
            return self.targetNode().getName()
        
        elif self.targetNode().getValue():
            return self.targetNode().getValue()
        
        else:
            return ""


sTREEVIEW_TYPE = " ".join((VPTYPE, IDENT, sSRV_USERNAME, NICE_NAME))

tags = {lx.symbol.sSRV_USERNAME:  sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE}

lx.bless(rm_BatchView, SERVERNAME, tags)


# -------------------------------------------------------------------------
# Request a batch file
# -------------------------------------------------------------------------


class requestBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.yaml_open_dialog()
        if path:
            _BATCH.update_batch_from_file(path)
            rm_BatchView.notify_NewShape()
        
lx.bless(requestBatchFile, CMD_requestBatchFile)


# -------------------------------------------------------------------------
# Request an LXO file and add a task
# -------------------------------------------------------------------------


class addBatchTask(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        paths_list = os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileOpen',
                title='Select Scene File',
                names=('lxo',),
                unames=('MODO Scene file',),
                patterns=('*.lxo',),
                path=None
            )
        )
        if not isinstance(paths_list,list):
            paths_list = [paths_list]
            
        if paths_list:
            for path in paths_list:
                _BATCH.add_task(path)
            rm_BatchView.notify_NewShape()
        
lx.bless(addBatchTask, CMD_addBatchTask)


# -------------------------------------------------------------------------
# Run the currently open batch
# -------------------------------------------------------------------------


class runCurrentBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batchFilePath:
            return monkey.batch.run(_BATCH._batchFilePath)

# WIP - NEED  NOTIFIER TO UPDATE THIS WHEN TREE UPDATES
#    def basic_Enable(self, msg):
#        if _BATCH._batchFilePath:
#            return True
#        else:
#            return False
        
lx.bless(runCurrentBatch, CMD_runCurrentBatch)



# -------------------------------------------------------------------------
# Export batch template and open
# -------------------------------------------------------------------------


class exampleBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.yaml_save_dialog()
        if path:
            lx.eval('renderMonkey.batchTemplate {%s}' % path)
            _BATCH.update_batch_from_file(path)
            rm_BatchView.notify_NewShape()
        
        
lx.bless(exampleBatch, CMD_exampleBatch)



# -------------------------------------------------------------------------
# Open batch in text editor
# -------------------------------------------------------------------------


class openBatchInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batchFilePath:
            lx.eval('file.open {%s}' % _BATCH._batchFilePath)
            
# WIP - NEED  NOTIFIER TO UPDATE THIS WHEN TREE UPDATES
#    def basic_Enable(self, msg):
#        if _BATCH._batchFilePath:
#            return True
#        else:
#            return False
        
        
lx.bless(openBatchInFilesystem, CMD_openBatchInFilesystem)



# -------------------------------------------------------------------------
# Remove selected task
# -------------------------------------------------------------------------


class echoSelected(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH._tree.getSelectedChildren()
        for i in sel:
            path = i.getPath()
            idxPath = i.getIndexPath()
            lx.out(len(path))
            lx.out(idxPath)
            
lx.bless(echoSelected, CMD_echoSelected)


