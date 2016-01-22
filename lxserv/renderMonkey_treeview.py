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


def markup(pre,string):
    return '\03(%s:%s)' % (pre,string)

def bitwise_rgb(r,g,b):
    return str(0x01000000 | ((r << 16) | (g << 8 | b)))

def bitwise_hex(h):
    h = h.strip()
    if h[0] == '#': h = h[1:]
    r, g, b = h[:2], h[2:4], h[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return bitwise_rgb(r, g, b)


RED = markup('c',bitwise_rgb(255,0,0))
BLUE = markup('c',bitwise_hex('#0e76b7'))
GRAY = markup('c','4113')

DEFAULT = markup('f','FONT_DEFAULT')
NORMAL = markup('f','FONT_NORMAL')
BOLD = markup('f','FONT_BOLD')
ITALIC = markup('f','FONT_ITALIC')

GRAY_ITALIC = GRAY + ITALIC

fTREE_VIEW_ITEM_ATTR = 0x00000001
fTREE_VIEW_ITEM_EXPAND = 0x00000002
fTREE_VIEW_ATTR_EXPAND = 0x00000004


class rm_TreeNode(object):

    _Primary = None

    def __init__(self, key, value=None, parent=None, prefix=''):
        self.m_key = key
        self.m_value = value
        self.m_parent = parent
        self.m_prefix = prefix
        self.m_children = []
        self.state = 0
        self.selected = False

        self.columns = (("Name", -1),
                        ("Value", -4))

        self.toolTips = {}

    def AddNode(self, key, value=None, prefix=None):
        self.m_children.append(rm_TreeNode(key, value, self, prefix))
        return self.m_children[-1]

    def ClearChildren(self):
        if len(self.m_children) > 0:
            for child in self.m_children:
                self.m_children.remove(child)

    def ClearSelection(self):
        if self._Primary:
            self.setPrimary()

        self.SetSelected(False)

        for child in self.m_children:
            child.ClearSelection()

    def SetSelected(self,val=True):

        if val:
            self.setPrimary(self)
        self.selected = val

    def isSelected(self):
        return self.selected

    @classmethod
    def setPrimary(cls,primary=None):
        cls._Primary = primary

    @classmethod
    def getPrimary(cls):
        return cls._Primary

    def setState(self,flag):
        self.state = self.state | flag

    def setToolTip(self,idx,tip):
        self.toolTips[idx] = tip

    def getToolTip(self,idx):
        if self.toolTips.has_key(idx):
            return self.toolTips[idx]

    def getValue(self):
        return str(self.m_value)

    def getName(self):
        m = str(self.m_prefix) if self.m_prefix else ''
        k = str(self.m_key)
        k = k.replace('_',' ')
        k = k.title()
        return m + k

    def getKey(self):
        return str(self.m_key)

    def getChildByKey(self,key):
        for i in self.m_children:
            if key == i.m_key:
                return i
        return False

    def get_selected_children(self,recursive=True):
        sel = []
        for i in self.m_children:
            if i.isSelected():
                sel.append(i)
            if recursive:
                sel += i.get_selected_children()

        return sel

    def get_by_keys(self,keys_list):
        if len(keys_list) > 1:
            return self.getChildByKey(keys_list[0]).get_by_keys(keys_list[1:])
        else:
            return self.getChildByKey(keys_list[0])

    def get_ancestors(self,path=[]):
        if self.m_parent:
            return self.m_parent.get_ancestors() + [self]
        else:
            return path

    def get_keys(self):
        return [i.m_key for i in self.get_ancestors()[1:]]

    def parent(self):
        return self.m_parent

    def children(self):
        return self.m_children

    def update_child_keys(self):
        for n, child in enumerate(sorted(self.children(), key=lambda x: x.m_key)):
            child.m_key = n if isinstance(child.m_key,int) else child.m_key

    def suicide(self):
        self.ClearSelection()
        self.parent().children().remove(self)


class rm_Batch:

    def __init__(self, batchFilePath='', batch=[]):
        self._batchFilePath = batchFilePath
        self._batch = batch
        self._tree = rm_TreeNode(TREE_ROOT_TITLE,LIST)

        if self._batchFilePath:
            self.load_from_file()

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

            self.save_to_file()
            self.regrow_tree()

            return self._batch

        except:
            debug(traceback.print_exc())
            return False

    def clear_all_task_parameters(self, task_index):
        try:
            self._batch[task_index] = {}

            self.save_to_file()
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

            self.save_to_file()
            self.regrow_tree()

            return self._batch[task_index]

        except:
            debug(traceback.print_exc())
            return False

    def edit_task(self, task_index, parameters_dict):
        try:
            for k, v in parameters_dict.iteritems():
                self._batch[task_index][k] = v

            self.save_to_file()
            self.regrow_tree()

            return self._batch[task_index]

        except:
            debug(traceback.print_exc())
            return False

    def load_from_file(self, file_path=None):
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

    def close_file(self):
        try:
            self._tree.ClearSelection()
            self.build_empty_tree()
            self._batchFilePath = None
            self._batch = None

            return self._batch
        except:
            debug(traceback.print_exc())
            return False

    def save_to_file(self, file_path=None):
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
                return self.save_to_file()
            else:
                return self.save_to_file(
                    monkey.util.yaml_save_dialog()
                )
        except:
            debug(traceback.print_exc())
            return False


    def regrow_tree(self):
        try:
            if not self._batch:
                return self.build_empty_tree()

            self._tree.ClearChildren()

            file_root = self._tree.AddNode(
                BATCHFILE,
                BOLD + basename(self._batchFilePath),
                BOLD
            )

            file_root.setState(fTREE_VIEW_ITEM_EXPAND)

            for task_index, task in enumerate(self._batch):

                if not task[SCENE_PATH]:
                    break

                task_node = file_root.AddNode(
                    task_index,
                    basename(task[SCENE_PATH]),
                    GRAY + TASK + SP
                )

                for param_key, param_value in iter(sorted(task.iteritems())):

                    if isinstance(param_value,(list,tuple)):
                        param_node = task_node.AddNode(
                            param_key,
                            GRAY+LIST
                        )

                        for k, v in enumerate(param_value):
                            param_node.AddNode(k,v,GRAY)

                        param_node.AddNode(ADD_GENERIC, EMPTY, GRAY)

                    elif isinstance(param_value,dict):
                        param_node = task_node.AddNode(
                            param_key,
                            GRAY+DICT
                        )

                        for k, v in param_value.iteritems():
                            param_node.AddNode(k,v)

                        param_node.AddNode(ADD_GENERIC, EMPTY, GRAY)

                    else:
                        task_node.AddNode(param_key, param_value)

                task_node.AddNode(ADD_PARAM,EMPTY,GRAY)

            file_root.AddNode(ADD_TASK,EMPTY,GRAY)

            return self._tree

        except:
            debug(traceback.print_exc())
            return False

    def build_empty_tree(self):
        try:
            self._tree.ClearChildren()
            self._tree.AddNode(EMPTY,GRAY_ITALIC + EMPTY_PROMPT)
            return self._tree
        except:
            debug(traceback.print_exc())
            return False

    def batch_file_path(self):
        return self._batchFilePath

    def remove_by_key(self, keys):
        obj = self._batch
        if keys:
            for key in keys[:-1]:
                obj = obj[key]
            del obj[keys[-1]]

            self.tree().get_by_keys(keys).suicide()

            if len(keys) > 1:
                if type(self.get_by_keys(keys[:-1])) in (list,tuple):
                    self.tree().get_by_keys(keys[:-1]).update_child_keys()
            else:
                self.tree().update_child_keys()

            return True

        else:
            return False

    def get_by_keys(self, keys):
        obj = self._batch
        if keys:
            for key in keys[:-1]:
                obj = obj[key]
            return obj[keys[-1]]
        else:
            return obj

    def get_selection(self):
        return self._tree.get_selected_children()

    def tree(self):
        return self._tree.getChildByKey(BATCHFILE)



_BATCH = rm_Batch()

class rm_BatchView(lxifc.TreeView,
                        lxifc.Tree,
                        lxifc.ListenerPort,
                        lxifc.Attributes
                        ):

    _listenerClients = {}

    def __init__(self, node = None, curIndex = 0):

        if node is None:
            node = _BATCH._tree

        self.m_currentNode = node
        self.m_currentIndex = curIndex

    @classmethod
    def addListenerClient(cls,listener):
        treeListenerObj = lx.object.TreeListener(listener)
        cls._listenerClients[treeListenerObj.__peekobj__()] = treeListenerObj

    @classmethod
    def removeListenerClient(cls,listener):
        treeListenerObject = lx.object.TreeListener(listener)
        if cls._listenerClients.has_key(treeListenerObject.__peekobj__()):
            del  cls._listenerClients[treeListenerObject.__peekobj__()]

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

    def lport_AddListener(self,obj):
        self.addListenerClient(obj)

    def lport_RemoveListener(self,obj):
        self.removeListenerClient(obj)

    def targetNode(self):
        return self.m_currentNode.m_children[ self.m_currentIndex ]

    def tree_Spawn(self, mode):
        newTree = rm_BatchView(self.m_currentNode, self.m_currentIndex)
        newTreeObj = lx.object.Tree(newTree)

        if mode == lx.symbol.iTREE_PARENT:
            newTreeObj.ToParent()

        elif mode == lx.symbol.iTREE_CHILD:
            newTreeObj.ToChild()

        elif mode == lx.symbol.iTREE_ROOT:
            newTreeObj.ToRoot()

        return newTreeObj

    def tree_ToParent(self):
        m_parent = self.m_currentNode.m_parent

        if m_parent:
            self.m_currentIndex = m_parent.m_children.index(self.m_currentNode)
            self.m_currentNode = m_parent

    def tree_ToChild(self):
        self.m_currentNode = self.m_currentNode.m_children[self.m_currentIndex]

    def tree_ToRoot(self):
        self.m_currentNode = _BATCH._tree

    def tree_IsRoot(self):
        if self.m_currentNode == _BATCH._tree:
            return True
        else:
            return False

    def tree_ChildIsLeaf(self):
        if len( self.m_currentNode.m_children ) > 0:
            return False
        else:
            return True

    def tree_Count(self):
        return len( self.m_currentNode.m_children )

    def tree_Current(self):
        return self.m_currentIndex

    def tree_SetCurrent(self, index):
        self.m_currentIndex = index

    def tree_ItemState(self, guid):
        return self.targetNode().state

    def tree_SetItemState(self, guid, state):
        self.targetNode().state = state

    def treeview_StoreState(self, uid):
        lx.notimpl()

    def treeview_RestoreState(self, uid):
        lx.notimpl()

    def treeview_ColumnCount(self):
        return len(_BATCH._tree.columns)

    def treeview_ColumnByIndex(self, columnIndex):
        return _BATCH._tree.columns[columnIndex]

    def treeview_ToPrimary(self):
        if self.m_currentNode._Primary:
            self.m_currentNode = self.m_currentNode._Primary
            self.tree_ToParent()
            return True
        return False

    def treeview_IsSelected(self):
        return self.targetNode().isSelected()

    def treeview_Select(self, mode):

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            _BATCH._tree.ClearSelection()
            self.targetNode().SetSelected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
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

    def treeview_IsInputRegion(self, columnIndex, regionID):
        if regionID == 0:
            return True
        elif columnIndex ==  regionID - 1:
            return True

        return False

    def attr_Count(self):
        return len(_BATCH._tree.columns)

    def attr_GetString(self, index):
        if index == 0:
            return self.targetNode().getName()

        elif self.targetNode().getValue():
            return self.targetNode().getValue()

        else:
            return ""


class openBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.yaml_open_dialog()
        if path:
            _BATCH.load_from_file(path)
            rm_BatchView.notify_NewShape()


class closeBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        _BATCH.close_file()
        rm_BatchView.notify_NewShape()


class addBatchTask(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        paths_list = monkey.util.lxo_open_dialog()
        if not isinstance(paths_list,list):
            paths_list = [paths_list]

        if paths_list:
            for path in paths_list:
                _BATCH.add_task(path)
            rm_BatchView.notify_NewShape()


class removeBatchSel(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        try:
            for i in _BATCH.get_selection():
                keys = i.get_keys()

                _BATCH.remove_by_key(keys)
                _BATCH.save_to_file()

                rm_BatchView.notify_NewShape()
        except:
            debug(traceback.print_exc())
            return False


class runCurrentBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batchFilePath:
            return monkey.batch.run(_BATCH._batchFilePath)


class exampleBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.yaml_save_dialog()
        if path:
            lx.eval('renderMonkey.batchTemplate {%s}' % path)
            _BATCH.load_from_file(path)
            rm_BatchView.notify_NewShape()


class openBatchInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batchFilePath:
            lx.eval('file.open {%s}' % _BATCH._batchFilePath)



sTREEVIEW_TYPE = " ".join((VPTYPE, IDENT, sSRV_USERNAME, NICE_NAME))
sINMAP = "name[%s] regions[1@%s 2@%s 3@%s]" % (sSRV_USERNAME,REGION1,REGION2,REGION3)

tags = {lx.symbol.sSRV_USERNAME:  sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE,
        lx.symbol.sINMAP_DEFINE: sINMAP}

lx.bless(rm_BatchView, SERVERNAME, tags)

lx.bless(openBatchFile, CMD_openBatchFile)
lx.bless(closeBatchFile, CMD_closeBatchFile)
lx.bless(addBatchTask, CMD_addBatchTask)
lx.bless(removeBatchSel, CMD_removeBatchSel)
lx.bless(runCurrentBatch, CMD_runCurrentBatch)
lx.bless(exampleBatch, CMD_exampleBatch)
lx.bless(openBatchInFilesystem, CMD_openBatchInFilesystem)
