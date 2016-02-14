# python

import lx, lxu, lxifc

import monkey
from monkey.symbols import *
from monkey.util import debug, markup, bitwise_rgb, bitwise_hex, breakpoint

import traceback
from os.path import basename

RED = markup('c',bitwise_rgb(255,0,0))
BLUE = markup('c',bitwise_hex('#0e76b7'))
GRAY = markup('c','4113')

FONT_DEFAULT = markup('f','FONT_DEFAULT')
FONT_NORMAL = markup('f','FONT_NORMAL')
FONT_BOLD = markup('f','FONT_BOLD')
FONT_ITALIC = markup('f','FONT_ITALIC')

fTREE_VIEW_ITEM_ATTR = 0x00000001
fTREE_VIEW_ITEM_EXPAND = 0x00000002
fTREE_VIEW_ATTR_EXPAND = 0x00000004

REGIONS = [NODETYPE_BATCHFILE,
           NODETYPE_BATCHTASK,
           NODETYPE_TASKPARAM,
           NODETYPE_TASKPARAM_MULTI,
           NODETYPE_TASKPARAM_SUB,
           NODETYPE_ADDNODE,
           NODETYPE_NULL]


class TreeNode(object):

    _primary = None

    def __init__(self, key, value=None, parent=None, node_type=None, value_type=None):
        self._key = key
        self._value = value
        self._parent = parent
        self._node_type = node_type
        self._value_type = value_type
        self._children = []
        self._state = 0
        self._selected = False
        self._tooltips = {}

        self._columns = ((COL_NAME, -1),
                        (COL_VALUE, -3))

    @classmethod
    def set_primary(cls,primary=None):
        cls._primary = primary

    @classmethod
    def primary(cls):
        return cls._primary

    def add_child(self, key, value=None, node_type=None, value_type=None):
        self._children.append(TreeNode(key, value, self, node_type, value_type))
        return self._children[-1]

    def clear_children(self):
        if len(self._children) > 0:
            for child in self._children:
                self._children.remove(child)

    def clear_selection(self):
        if self._primary:
            self.set_primary(None)

        self.set_selected(False)

        for child in self._children:
            child.clear_selection()

    def set_selected(self, val=True):
        if val:
            self.set_primary(self)
        self._selected = val

    def is_selected(self):
        return self._selected

    def set_state(self, flag):
        self._state = self._state | flag

    def set_tooltip(self, idx, tip):
        self._tooltips[idx] = tip

    def tooltip(self, idx):
        if self._tooltips.has_key(idx):
            return self._tooltips[idx]

    def value(self):
        m = ''
        if self._value_type in (list.__name__,dict.__name__,tuple.__name__):
            m = GRAY
        elif self._node_type == NODETYPE_BATCHTASK:
            m = GRAY
        elif self._node_type == NODETYPE_ADDNODE:
            m = GRAY

        if self._node_type == NODETYPE_BATCHTASK:
            v = self.child_by_key(SCENE_PATH).value()
        else:
            v = str(self._value)

        return m + v

    def name(self):
        m = ''
        if self._node_type in (NODETYPE_ADDNODE,NODETYPE_NULL):
            m = GRAY
        elif self._node_type == NODETYPE_BATCHFILE:
            m = FONT_BOLD
        elif isinstance(self._key,int):
            m = GRAY

        if self._node_type == NODETYPE_BATCHTASK:
            k = basename(self.child_by_key(SCENE_PATH).value())
        elif isinstance(self._key,int):
            k = str(self._key + 1)
        else:
            k = str(self._key)
            k = k.replace('_',' ')
            k = k.title() if "." not in k else k

        return m + k

    def key(self):
        return str(self._key)

    def node_type(self):
        return str(self._node_type)

    def set_node_type(self, node_type):
        self._node_type = node_type
        return self._node_type

    def value_type(self):
        return self._value_type

    def set_value_type(self, value_type):
        self._value_type = value_type
        return self._value_type

    def columns(self):
        return self._columns

    def child_by_key(self,key):
        for i in self._children:
            if key == i._key:
                return i
        return False

    def selected_children(self,recursive=True):
        sel = []
        for i in self._children:
            if i.is_selected():
                sel.append(i)
            if recursive:
                sel += i.selected_children()

        return sel

    def get_by_keys(self,keys_list):
        if len(keys_list) > 1:
            return self.child_by_key(keys_list[0]).get_by_keys(keys_list[1:])
        else:
            return self.child_by_key(keys_list[0])

    def ancestors(self,path=None):
        if self._parent:
            return self._parent.ancestors() + [self]
        else:
            return path if path else []

    def ancestor_keys(self):
        return [i._key for i in self.ancestors()[1:]]

    def parent(self):
        return self._parent

    def children(self):
        return self._children

    def update_child_keys(self):
        for n, child in enumerate(sorted(self.children(), key=lambda x: x._key)):
            child._key = n if isinstance(child._key,int) else child._key

    def destroy(self):
        self.clear_selection()
        self.parent().children().remove(self)

    def tier(self):
        return len(self.ancestors())


class BatchManager:

    def __init__(self, batch_file_path='', batch=None):
        self._batch_file_path = batch_file_path
        self._batch = batch if batch else []
        self._tree = TreeNode(TREE_ROOT_TITLE,LIST)

        if self._batch_file_path:
            self.load_from_file()

        self.regrow_tree()

    def add_task(self, paths_list):
        try:
            if not self._batch_file_path:
                self.save_temp_file()

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
                file_path = self._batch_file_path
            else:
                self._batch_file_path = file_path

            self._batch = monkey.io.read_yaml(file_path)
            self.regrow_tree()

            return self._batch
        except:
            debug(traceback.print_exc())
            return False

    def close_file(self):
        try:
            self._tree.clear_selection()
            self.build_empty_tree()
            self._batch_file_path = None
            self._batch = None

            return self._batch
        except:
            debug(traceback.print_exc())
            return False

    def save_to_file(self, file_path=None):
        try:
            if file_path:
                self._batch_file_path = file_path
                return monkey.io.write_yaml(self._batch, file_path)

            elif self._batch_file_path:
                return monkey.io.write_yaml(self._batch, self._batch_file_path)

            else:
                return self.save_batch_as()

        except:
            debug(traceback.print_exc())
            return False

    def save_temp_file(self, file_path=None):
        try:
            if file_path:
                return monkey.io.write_yaml(self._batch, file_path)
            else:
                file_path = monkey.util.path_alias(':'.join((KIT_ALIAS, QUICK_BATCH_PATH)))
                return self.save_to_file(file_path)

        except:
            debug(traceback.print_exc())
            return False

    def save_batch_as(self, file_path=None):
        try:
            if file_path:
                self._batch_file_path = file_path
                return self.save_to_file()
            else:
                path = monkey.io.yaml_save_dialog()
                if path:
                    return self.save_to_file(path)
                else:
                    return False
        except:
            debug(traceback.print_exc())
            return False

    def iterate_anything(self, obj):
        if isinstance(obj, (list, tuple)):
            return {k:v for k, v in enumerate(obj)}.iteritems()
        if isinstance(obj, dict):
            return obj.iteritems()

    def grow_node(self, branch, parent_node, depth=0):

        if depth == 0:      node_type = NODETYPE_BATCHTASK
        elif depth == 1:    node_type = NODETYPE_TASKPARAM
        elif depth == 2:    node_type = NODETYPE_TASKPARAM_SUB
        else:               node_type = NODETYPE_NULL

        if isinstance(branch, (list, tuple, dict)):
            for key, value in sorted(self.iterate_anything(branch)):

                value_type = type(value).__name__

                if isinstance(value, (list, tuple, dict)):
                    node = parent_node.add_child(key, value_type, node_type, value_type)
                    self.grow_node(value, node, depth + 1)

                else:
                    parent_node.add_child(key, value, node_type, value_type)

        parent_node.add_child(ADD_GENERIC, EMPTY, NODETYPE_ADDNODE)

    def regrow_tree(self):
        try:
            if not self._batch_file_path:
                return self.build_empty_tree()

            self._tree.clear_children()

            file_root = self._tree.add_child(
                BATCHFILE,
                FONT_BOLD + basename(self._batch_file_path),
                NODETYPE_BATCHFILE
            )

            file_root.set_state(fTREE_VIEW_ITEM_EXPAND)

            if self._batch:
                self.grow_node(self._batch, file_root)

            return self._tree

        except:
            debug(traceback.print_exc())
            return False

    def build_empty_tree(self):
        try:
            self._tree.clear_children()
            self._tree.add_child(EMPTY_PROMPT, EMPTY, NODETYPE_NULL)
            self._tree.clear_selection()
            return self._tree
        except:
            debug(traceback.print_exc())
            return False

    def batch_file_path(self):
        return self._batch_file_path

    def remove_by_key(self, keys):
        obj = self._batch
        if keys:
            for key in keys[:-1]:
                obj = obj[key]
            del obj[keys[-1]]

            self.tree().get_by_keys(keys).destroy()

            if len(keys) > 1:
                if type(self.get_by_keys(keys[:-1])) in (list, tuple):
                    self.tree().get_by_keys(keys[:-1]).update_child_keys()
            else:
                self.tree().update_child_keys()

            return True

        else:
            return False

    def bumpByKey(self, keys, direction):
        # TODO bumpByKey to reorder tasks
        pass

    def get_by_keys(self, keys):
        obj = self._batch
        if keys:
            for key in keys[:-1]:
                obj = obj[key]
            return obj[keys[-1]]
        else:
            return obj

    def get_selection(self):
        return self._tree.selected_children()

    def clear_selection(self):
        self._tree.clear_selection()

    def tree(self):
        return self._tree.child_by_key(BATCHFILE)

    def batch(self):
        return self._batch


_BATCH = BatchManager()


class BatchTreeView(lxifc.TreeView,
                        lxifc.Tree,
                        lxifc.ListenerPort,
                        lxifc.Attributes
                        ):

    _listenerClients = {}

    def __init__(self, node=None, curIndex=0):

        if node is None:
            node = _BATCH._tree

        self.m_currentNode = node
        self.m_currentIndex = curIndex

    @classmethod
    def addListenerClient(cls, listener):
        tree_listener_obj = lx.object.TreeListener(listener)
        cls._listenerClients[tree_listener_obj.__peekobj__()] = tree_listener_obj

    @classmethod
    def removeListenerClient(cls, listener):
        tree_listener_object = lx.object.TreeListener(listener)
        if cls._listenerClients.has_key(tree_listener_object.__peekobj__()):
            del cls._listenerClients[tree_listener_object.__peekobj__()]

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

    def lport_AddListener(self, obj):
        self.addListenerClient(obj)

    def lport_RemoveListener(self, obj):
        self.removeListenerClient(obj)

    def targetNode(self):
        return self.m_currentNode._children[self.m_currentIndex]

    def tree_Spawn(self, mode):
        new_tree = BatchTreeView(self.m_currentNode, self.m_currentIndex)
        new_tree_obj = lx.object.Tree(new_tree)

        if mode == lx.symbol.iTREE_PARENT:
            new_tree_obj.ToParent()

        elif mode == lx.symbol.iTREE_CHILD:
            new_tree_obj.ToChild()

        elif mode == lx.symbol.iTREE_ROOT:
            new_tree_obj.ToRoot()

        return new_tree_obj

    def tree_ToParent(self):
        m_parent = self.m_currentNode._parent

        if m_parent:
            self.m_currentIndex = m_parent._children.index(self.m_currentNode)
            self.m_currentNode = m_parent

    def tree_ToChild(self):
        self.m_currentNode = self.m_currentNode._children[self.m_currentIndex]

    def tree_ToRoot(self):
        self.m_currentNode = _BATCH._tree

    def tree_IsRoot(self):
        if self.m_currentNode == _BATCH._tree:
            return True
        else:
            return False

    def tree_ChildIsLeaf(self):
        if len(self.m_currentNode._children) > 0:
            return False
        else:
            return True

    def tree_Count(self):
        return len(self.m_currentNode._children)

    def tree_Current(self):
        return self.m_currentIndex

    def tree_SetCurrent(self, index):
        self.m_currentIndex = index

    def tree_ItemState(self, guid):
        return self.targetNode()._state

    def tree_SetItemState(self, guid, state):
        self.targetNode()._state = state

    def treeview_ColumnCount(self):
        return len(_BATCH._tree.columns())

    def treeview_ColumnByIndex(self, columnIndex):
        return _BATCH._tree.columns()[columnIndex]

    def treeview_ToPrimary(self):
        if self.m_currentNode.primary():
            self.m_currentNode = self.m_currentNode.primary()
            self.tree_ToParent()
            return True
        return False

    def treeview_IsSelected(self):
        return self.targetNode().is_selected()

    def treeview_Select(self, mode):

        special = [
            ADD_TASK,
            ADD_PARAM,
            ADD_GENERIC,
            REPLACE_BATCH_FILE
        ]

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            _BATCH.clear_selection()

            if self.targetNode().key() in special:
                self.targetNode().parent().set_selected()
            else:
                self.targetNode().set_selected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
            if self.targetNode().key() not in special:
                self.targetNode().set_selected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().set_selected(False)

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            _BATCH.clear_selection()

    def treeview_ToolTip(self, column_index):
        toolTip = self.targetNode().tooltip(column_index)
        if toolTip:
            return toolTip
        lx.notimpl()

    def treeview_IsInputRegion(self, column_index, regionID):
        if regionID == 0:
            return True
        if self.targetNode().node_type() == REGIONS[regionID]:
            return True

        return False

    def attr_Count(self):
        return len(_BATCH._tree.columns())

    def attr_GetString(self, index):
        if index == 0:
            return self.targetNode().name()

        elif self.targetNode().value():
            return self.targetNode().value()

        else:
            return EMPTY


class openBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_open_dialog()
        if path:
            _BATCH.load_from_file(path)
            BatchTreeView.notify_NewShape()


class closeBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        _BATCH.close_file()
        BatchTreeView.notify_NewShape()


class addBatchTask(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        paths_list = monkey.io.lxo_open_dialog()
        if not isinstance(paths_list,list):
            paths_list = [paths_list]

        if paths_list:
            for path in paths_list:
                _BATCH.add_task(path)
            BatchTreeView.notify_NewShape()


class removeBatchSel(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH.get_selection()
        _BATCH.clear_selection()
        for i in sel:
            keys = i.ancestor_keys()

            _BATCH.remove_by_key(keys)
            _BATCH.save_to_file()

            BatchTreeView.notify_NewShape()


class bumpBatchSel(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('up/down', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        direction = self.dyna_String(0)

        sel = _BATCH.get_selection()
        for i in sel:
            keys = i.ancestor_keys()

            _BATCH.bumpByKey(keys,direction)
            _BATCH.save_to_file()

            BatchTreeView.notify_NewShape()


class runCurrentBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batch_file_path:
            return monkey.batch.run(_BATCH._batch_file_path)


class exampleBatch(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            lx.eval('{} {{{}}}'.format(CMD_batchTemplate,path))
            _BATCH.load_from_file(path)
            BatchTreeView.notify_NewShape()


class openBatchInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batch_file_path:
            lx.eval('file.open {{{}}}'.format(_BATCH._batch_file_path))


class revealBatchInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH._batch_file_path:
            lx.eval('file.revealInFileViewer {{{}}}'.format(_BATCH._batch_file_path))


class newBatchFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            monkey.io.write_yaml([],path)

            _BATCH.load_from_file(path)
            BatchTreeView.notify_NewShape()


class saveBatchAs(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            monkey.io.write_yaml(_BATCH.batch(),path)

            _BATCH.load_from_file(path)
            BatchTreeView.notify_NewShape()



sTREEVIEW_TYPE = " ".join((VPTYPE, IDENT, sSRV_USERNAME, NICE_NAME))
sINMAP = "name[{}] regions[{}]".format(sSRV_USERNAME," ".join(['{}@{}'.format(n, i) for n, i in enumerate(REGIONS)]))

tags = {lx.symbol.sSRV_USERNAME: sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE,
        lx.symbol.sINMAP_DEFINE: sINMAP}

lx.bless(BatchTreeView, SERVERNAME, tags)

lx.bless(openBatchFile, CMD_openBatchFile)
lx.bless(closeBatchFile, CMD_closeBatchFile)
lx.bless(addBatchTask, CMD_addBatchTask)
lx.bless(removeBatchSel, CMD_removeBatchSel)
lx.bless(runCurrentBatch, CMD_runCurrentBatch)
lx.bless(exampleBatch, CMD_exampleBatch)
lx.bless(openBatchInFilesystem, CMD_openBatchInFilesystem)
lx.bless(revealBatchInFilesystem, CMD_revealBatchInFilesystem)
lx.bless(newBatchFile, CMD_newBatchFile)
lx.bless(saveBatchAs, CMD_saveBatchAs)
