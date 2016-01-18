# python

import lx
import lxu
import lxifc
import modo

import monkey
from monkey.symbols import *
from monkey.util import debug, breakpoint

import traceback
import os
from os.path import basename
import sys

try:
    import wingdbstub
except:
    pass
    

# -------------------------------------------------------------------------
# Node styles
# -------------------------------------------------------------------------

# Icons added via markup in the string itself.
# "\x03(i:uiicon_bm_overlay) Some text" < Adds icon resource "bm_overlay" to cell

# All markup flags have the format '\03(pre:string)', where 'pre' is the
# letter f (font), c (color), or i (icon), so we may as well:
def markup(pre,string):
    return '\03(%s:%s)' % (pre,string)

# "\03(c:color)Some Text" < Where "color" is a string representing a decimal
# integer computed with 0x01000000 | ((r << 16) | (g << 8) | b)
def bitwise_rgb(r,g,b):
	return str(0x01000000 | ((r << 16) | (g << 8 | b)))

RED = markup('c',bitwise_rgb(255,0,0))

# I happen to hate 8-bit RGB values. Let's use hex instead.
def bitwise_hex(h):
    h = h.strip()
    if h[0] == '#': h = h[1:]
    r, g, b = h[:2], h[2:4], h[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return bitwise_rgb(r, g, b)

BLUE = markup('c',bitwise_hex('#0e76b7'))

# The below "c:4113" is a special case pre-defined gray color for text,
# which is why the format is different from that of arbitrary colors above.
GRAY = markup('c','4113')

# Italics and bold are done with:
# "\03(c:font)" where "font" is the string "FONT_DEFAULT", "FONT_NORMAL",
# "FONT_BOLD" or "FONT_ITALIC"
DEFAULT = markup('f','FONT_DEFAULT')
NORMAL = markup('f','FONT_NORMAL')
BOLD = markup('f','FONT_BOLD')
ITALIC = markup('f','FONT_ITALIC')

# You can combine styles by stringing them together:
GRAY_ITALIC = GRAY + ITALIC

# These flags are pilfered from the modo source code itself:
fTREE_VIEW_ITEM_ATTR = 0x00000001
fTREE_VIEW_ITEM_EXPAND = 0x00000002
fTREE_VIEW_ATTR_EXPAND = 0x00000004

# -------------------------------------------------------------------------
# Generic layer node object that represents each entry in the tree
# -------------------------------------------------------------------------


class rm_TreeNode(object):

    _Primary = None

    def __init__(self, key, value=None, parent=None, name=None):
        self.key = key
        self.name = name if name else key
        self.value = value
        self.parent = parent
        self.children = []
        self.state = 0
        self.selected = False
        self.expanded = False

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

    def AddNode(self, key, value=None, name=None):
        self.children.append(rm_TreeNode(key, value, self, name))
        return self.children[-1]
    
    def Prune(self):
        if self.children:
            for i in self.children:
                i.Prune()
            self.children = []

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
        if flag == fTREE_VIEW_ITEM_EXPAND:
            self.setExpanded(True)
        else:
            self.state = self.state | flag
            
    def setExpanded(self, state=True):
        # Do not know how to set flag to false,
        # so for now we can only set it to True
        self.state = self.state | fTREE_VIEW_ITEM_EXPAND
        self.expanded = state
        
    def getExpanded(self):
        return self.expanded

    def setToolTip(self, idx, tip):
        self.toolTips[idx] = tip

    def getToolTip(self, idx):
        if idx in self.toolTips:
            return self.toolTips[idx]

    def getValue(self):
        return str(self.value)
    
    def getName(self):
        return str(self.name)
    
    def getKey(self):
        return str(self.key)
    
    def getChildByKey(self,key):
        for i in self.children:
            if key == i.key:
                return i
        return False
    
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
        for i in path[1:]:
            indexPath.append(i.key)
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
        
        self.regrow_tree()

    def add_task(self, paths_list):
        try:
            if not paths_list:
                return False

            if not isinstance(paths_list, list):
                paths_list = [paths_list]

            for path in paths_list:
                self._batch.append({
                    SCENE_PATH: path,
                    FORMAT: monkey.defaults.get('filetype'),
                    FRAMES: monkey.defaults.get('frames'),
                    DESTINATION: monkey.defaults.get('destination'),
                    PATTERN: monkey.defaults.get('output_pattern'),
                    GROUPS: [],
                    WIDTH: None,
                    HEIGHT: None,
                    OUTPUTS: [],
                    CAMERA: '',
                    RENDER_CHANNELS: {}
                })

            self.save_batch_to_file()
            self.regrow_tree()
                
            return self._batch

        except:
            debug(traceback.print_exc())
            return False
        
    def remove_sel(self, keys_list):
        try:
            if not keys_list:
                debug(traceback.print_exc())
                return False

            # The following is stupid. Please forgive.
            
            k = keys_list
            
            if len(keys_list)==1:
                del _BATCH._batch[k[0]]

            if len(keys_list)==2:
                del _BATCH._batch[k[0]][k[1]]

            if len(keys_list)==3:
                del _BATCH._batch[k[0]][k[1]][k[2]]
                    
            if len(keys_list)==4:
                del _BATCH._batch[k[0]][k[1]][k[2]][k[3]]
                    
            if len(keys_list)==5:
                del _BATCH._batch[k[0]][k[1]][k[2]][k[3]][k[4]]

            self.save_batch_to_file()
            self.regrow_tree()
            
            return self._batch
            
        except:
            debug(traceback.print_exc())
            return False  

    def clear_all_task_parameters(self, task_index):
        try:
            self._batch[task_index] = {}
                
            self.save_batch_to_file()
            self.regrow_tree()
                
            return self._batch[task_index]

        except:
            debug(traceback.print_exc())
            return False

    def clear_task_parameters(self, task_index, parameters_list):
        try:
            for p in parameters_list:
                if p in self._batch[task_index]:
                    del self._batch[task_index][p]
                
            self.save_batch_to_file()
            self.regrow_tree()
                
            return self._batch[task_index]

        except:
            debug(traceback.print_exc())
            return False
        
    def edit_task(self, task_index, parameters_dict):
        try:
            for k, v in parameters_dict.iteritems():
                self._batch[task_index][k] = v

            self.save_batch_to_file()
            self.regrow_tree()
                
            return self._batch[task_index]

        except:
            debug(traceback.print_exc())
            return False
        
    def update_batch_from_file(self, file_path=None):
        try:
            if file_path is None:
                file_path = self._batchFilePath
            else:
                self._batchFilePath = file_path

            self._batch = monkey.util.read_yaml(file_path)
            self.regrow_tree()
            
            return self._batch
        except:
            debug(traceback.print_exc())
            return False
        
    def closeBatchFile(self):
        try:
            self._batchFilePath = None

            self._batch = None
            self.build_empty_tree()
            
            return self._batch
        except:
            debug(traceback.print_exc())
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
            debug(traceback.print_exc())
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
            debug(traceback.print_exc())
            return False
        
    
    def regrow_tree(self):
        try:
            if not self._batch:
                return self.build_empty_tree()

            self._tree.Prune()
            
            file_root = self._tree.AddNode( 
                BATCHFILE,
                BOLD + basename(self._batchFilePath),
                BOLD + BATCHFILE.replace('_',' ')
            )
            
            file_root.setState(fTREE_VIEW_ITEM_EXPAND)
            
            for task_index, task in enumerate(self._batch):
                
                if not task[SCENE_PATH]:
                    break

                task_node = file_root.AddNode(
                    task_index, 
                    basename(task[SCENE_PATH]), 
                    " ".join((TASK,str(task_index+1)))
                )
                
                for param_key, param_value in iter(sorted(task.iteritems())):
                    
                    param_nicename = param_key.replace('_',' ')
                    
                    if isinstance(param_value,(list,tuple)):
                        param_node = task_node.AddNode(
                            param_key,
                            GRAY+LIST, 
                            param_nicename
                        )
                        
                        for k, v in enumerate(param_value):
                            param_node.AddNode(k,v,GRAY + str(k+1))
                        
                        param_node.AddNode(GRAY + ADD_GENERIC, EMPTY)
                        
                    elif isinstance(param_value,dict):
                        param_node = task_node.AddNode(
                            param_key,
                            GRAY+DICT, 
                            param_nicename
                        )
                        
                        for k, v in param_value.iteritems():
                            param_node.AddNode(k,v,k.replace('_',' '))
                        
                        param_node.AddNode(GRAY + ADD_GENERIC, EMPTY)
                        
                    else:
                        task_node.AddNode(param_key, param_value, param_nicename)
                        
                task_node.AddNode(GRAY + ADD_PARAM,EMPTY)
                            
            self._tree.AddNode(GRAY + ADD_TASK,EMPTY)
            
            return self._tree

        except:
            debug(traceback.print_exc())
            return False
        
    def build_empty_tree(self):
        try:
            self._tree.Prune()
            self._tree.AddNode(EMPTY,GRAY_ITALIC + EMPTY_PROMPT)
            return self._tree
        except:
            debug(traceback.print_exc())
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
# Open a batch file
# -------------------------------------------------------------------------


class openBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.yaml_open_dialog()
        if path:
            _BATCH.update_batch_from_file(path)
            rm_BatchView.notify_NewShape()
        
lx.bless(openBatchFile, CMD_openBatchFile)


# -------------------------------------------------------------------------
# Close a batch file
# -------------------------------------------------------------------------


class closeBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        _BATCH.closeBatchFile()
        rm_BatchView.notify_NewShape()
        
lx.bless(closeBatchFile, CMD_closeBatchFile)


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
# Remove selected batch task
# -------------------------------------------------------------------------


class removeBatchSel(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH._tree.getSelectedChildren()
        for i in sel:
            _BATCH.remove_sel(i.getIndexPath())
            
        rm_BatchView.notify_NewShape()
            
        
lx.bless(removeBatchSel, CMD_removeBatchSel)


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
# Echo selected task info for debug purposes
# -------------------------------------------------------------------------


class echoSelected(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH._tree.getSelectedChildren()
        for i in sel:
            path = i.getPath()
            idxPath = i.getIndexPath()
            lx.out(idxPath)
            lx.out('parent:%s' % i.parent.name)
            lx.out('children:')
            for j in i.children:
                lx.out('\t- %s' % j.name)
            
lx.bless(echoSelected, CMD_echoSelected)


