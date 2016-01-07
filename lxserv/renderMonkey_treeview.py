# python

import lx
import lxifc
import modo
import monkey
import traceback

try:
    import wingdbstub
except:
    pass
    
SERVERNAME = 'RenderMonkeyBatch'
SELECT_BATCH_FILE_PROMPT = '(select batch file)'
TREE_ROOT_TITLE = 'Tasks'
TASK = 'task'
EMPTY = ''
ADD_TASK = '(add task...)'
UPDATE_FROM_FILE = '(update)'
REPLACE_BATCH_FILE = '(open batch file...)'
ADD_PARAMETER = '(add parameter...)'
sSRV_USERNAME = "rendermonkeybatch"
NICE_NAME = "RenderMonkey_Batch"
OPEN_FILE_DIALOG_TITLE = 'Open File(s)'
LXO_FILE = '$LXOB'

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

fTREE_VIEW_ITEM_ATTR = 0x00000001
fTREE_VIEW_ITEM_EXPAND = 0x00000002
fTREE_VIEW_ATTR_EXPAND = 0x00000004
fTREE_VIEW_ROWCOLOR_ORANGE = 0x00050000
fTREE_VIEW_ROWCOLOR_RED = 0x00010000

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
                        ("Value", -3))

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

        
# -------------------------------------------------------------------------
# Batch data model
# -------------------------------------------------------------------------


class rm_Batch:
    
    def __init__(self, batchFilePath='', batch=[]):
        self._batchFilePath = batchFilePath
        self._batch = batch
        
        if self._batchFilePath:
            self.update_batch_from_file()
        
        self.rebuild_tree()

    def select_batch_file(self):
        try:
            self._batchFilePath = monkey.util.yaml_open_dialog()
            return self._batchFilePath
        except:
            lx.out(traceback.print_exc())
            return False

    def add_task(self, batch=[]):
        try:
            if batch:
                self._batch = batch
                
            if not self._batch:
                return False
            
            paths_list = modo.dialogs.fileOpen(
                ftype=LXO_FILE,
                title=OPEN_FILE_DIALOG_TITLE,
                multi=True,
                path=None
            )

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

            self.rebuild_tree()
                
            return self._batch

        except:
            lx.out(traceback.print_exc())
            return False

    def update_batch_from_file(self, file_path=None):
        try:
            if file_path is None:
                file_path = self._batchFilePath

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

            self._tree = rm_TreeNode(TREE_ROOT_TITLE)
            for i in self._batch:
                if i[PATH]:
                    j = self._tree.AddNode(TASK, os.path.basename(i[PATH]))
                    for k, v in iter(sorted(i.iteritems())):
                        j.AddNode(k, v)
            self._tree.AddNode(EMPTY, ADD_TASK)
            self._tree.AddNode(EMPTY, UPDATE_FROM_FILE)
            self._tree.AddNode(EMPTY, REPLACE_BATCH_FILE)
            return self._tree

        except:
            lx.out(traceback.print_exc())
            return False
        
    def build_empty_tree(self):
        try:
            self._tree = rm_TreeNode(TREE_ROOT_TITLE)
            self._tree.AddNode(EMPTY, SELECT_BATCH_FILE_PROMPT)
            return self._tree
        except:
            lx.out(traceback.print_exc())
            return False
        
    def tree(self):
        return self._tree
    
    def batch(self):
        return self._batch
    
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

        self._currentIndex = curIndex
        self._currentNode = node
        
        if not self._currentNode:
            self._currentNode = _BATCH.tree()

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
            # move the tree to the parent tier
            newTreeObj.ToParent()

        elif mode == lx.symbol.iTREE_CHILD:
            # move tree to child tier
            newTreeObj.ToChild()

        elif mode == lx.symbol.iTREE_ROOT:
            # move tree to root tier
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
        self._currentNode = _BATCH.tree()

    def tree_IsRoot(self):
        """
            Check if the current tier in the tree is the root tier
        """
        if self._currentNode == _BATCH.tree():
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
        return len(_BATCH.tree().columns)

    def treeview_ColumnByIndex(self, columnIndex):
        return _BATCH.tree().columns[columnIndex]

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
        if self.targetNode().value == SELECT_BATCH_FILE_PROMPT:
            _BATCH.tree().ClearSelection()
            self.targetNode().SetSelected(False)
            _BATCH.select_batch_file()

        elif self.targetNode().value == UPDATE_FROM_FILE:
            _BATCH.tree().ClearSelection()
            self.targetNode().SetSelected(False)
            _BATCH.update_batch_from_file()
            _BATCH.rebuild_tree()

        elif self.targetNode().value == REPLACE_BATCH_FILE:
            _BATCH.tree().ClearSelection()
            self.targetNode().SetSelected(False)
            _BATCH.select_batch_file()
            _BATCH.update_batch_from_file()
            _BATCH.rebuild_tree()

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            _BATCH.tree().ClearSelection()
            self.targetNode().SetSelected(False)
            self.targetNode().SetSelected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
            # Don't allow multi-selection.
            _BATCH.tree().ClearSelection()
            self.targetNode().SetSelected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().SetSelected(False)

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            _BATCH.tree().ClearSelection()

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
        return len(_BATCH.tree().columns)

    def attr_GetString(self, index):
        if index == 0:
            return self.targetNode().name
        
        elif self.targetNode().value:
            return self.targetNode().value
        
        else:
            return ""


sTREEVIEW_TYPE = " ".join(('vpapplication', 'WSTV', sSRV_USERNAME, NICE_NAME))

tags = {lx.symbol.sSRV_USERNAME:  sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE}

lx.bless(rm_BatchView, SERVERNAME, tags)
