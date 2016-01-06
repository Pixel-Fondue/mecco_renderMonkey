# python

import lx, lxifc, modo, monkey, traceback

import wingdbstub

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


class TreeNode(object):

    _Primary = None

    def __init__(self, name, value=None, parent=None):
        self.m_name = name
        self.m_value = value
        self.m_parent = parent
        self.m_children = []
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
        self.m_children.append(TreeNode(name, value, self))
        return self.m_children[-1]

    def ClearSelection(self):

        if self._Primary:
            self.setPrimary()

        self.SetSelected(False)

        for child in self.m_children:
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
# Build the structure
# -------------------------------------------------------------------------

# scenefile = _emptyTree.AddNode('file.lxo')
#
# a_path = "/path/to/file/that/might/be/deep.lxo"
# scenefile_path = scenefile.AddNode("path", a_path)
# scenefile_path.setToolTip(0,"")
#
# scenefile_frames = scenefile.AddNode("frames", "1-5,6,9-7")
# scenefile_frames.setToolTip(0,"")
#
# scenefile_destination = scenefile.AddNode("destination", "./frames")
# scenefile_destination.setToolTip(0,"")
#
# scenefile_format = scenefile.AddNode("format", "JPG")
# scenefile_format.setToolTip(0,"")
#
# scenefile_width = scenefile.AddNode("width", "")
# scenefile_width.setToolTip(0,"")
#
# scenefile_height = scenefile.AddNode("height", "")
# scenefile_height.setToolTip(0,"")
#
# scenefile_groups = scenefile.AddNode("groups", "")
# scenefile_groups.setToolTip(0,"")
#
# scenefile_outputs = scenefile.AddNode("outputs", "")
# scenefile_outputs.setToolTip(0,"")

# expand the first node
# scenefile.setState(fTREE_VIEW_ITEM_EXPAND)

# -------------------------------------------------------------------------
# Tree View
# -------------------------------------------------------------------------


class RenderMonkeyBatch(lxifc.TreeView,
                        lxifc.Tree,
                        lxifc.ListenerPort,
                        lxifc.Attributes
                        ):

    # Gloabal list of all created tree views.
    # These are used for shape and attribute changes
    _listenerClients = {}

    def __init__(self,
                 node=None,
                 curIndex=0,
                 batchFilePath=None,
                 treeData=None
                 ):

        if node is None:
            self.m_currentNode = self.build_empty_tree()

        self.m_currentIndex = curIndex

        if batchFilePath is None:
            self.m_batchFilePath = self.select_batch_file()

        if treeData is None:
            self.m_treeData = self.update_treeData_from_file(batchFilePath)

        self.tree = self.build_tree(self.m_treeData)

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
        return self.m_currentNode.m_children[self.m_currentIndex]

    # -------------------------------------------------------------------------
    # Each time the tree is spawned, we create a copy of ourselves at current
    # location in the tree and return it
    # -------------------------------------------------------------------------

    def tree_Spawn(self, mode):
        """
            Spawn a new instance of this tier in the tree.
        """

        # create an instance of our current location in the tree
        newTree = RenderMonkeyBatch(self.m_currentNode, self.m_currentIndex)

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
        m_parent = self.m_currentNode.m_parent

        if m_parent:
            self.m_currentIndex = m_parent.m_children.index(self.m_currentNode)
            self.m_currentNode = m_parent

    def tree_ToChild(self):
        """
            Move to the child tier and set the selected node
        """
        self.m_currentNode = self.m_currentNode.m_children[self.m_currentIndex]

    def tree_ToRoot(self):
        """
            Move back to the root tier of the tree
        """
        self.m_currentNode = self.m_tree

    def tree_IsRoot(self):
        """
            Check if the current tier in the tree is the root tier
        """
        if self.m_currentNode == self.m_tree:
            return True
        else:
            return False

    def tree_ChildIsLeaf(self):
        """
            If the current tier has no children then it is
            considered a leaf
        """
        if len(self.m_currentNode.m_children) > 0:
            return False
        else:
            return True

    def tree_Count(self):
        """
            Returns the number of nodes in this tier of
            the tree
        """
        return len(self.m_currentNode.m_children)

    def tree_Current(self):
        """
            Returns the index of the currently targeted item in
            this tier
        """
        return self.m_currentIndex

    def tree_SetCurrent(self, index):
        """
            Sets the index of the item to target in this tier
        """
        self.m_currentIndex = index

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

    def treeview_StoreState(self, guid):
        lx.notimpl()

    def treeview_RestoreState(self, guid):
        lx.notimpl()

    def treeview_ColumnCount(self):
        return len(self.m_tree.columns)

    def treeview_ColumnByIndex(self, columnIndex):
        return self.m_tree.columns[columnIndex]

    def treeview_ToPrimary(self):
        """
            Move the tree to the primary selection
        """
        if self.m_currentNode._Primary:
            self.m_currentNode = self.m_currentNode._Primary
            self.tree_ToParent()
            return True
        return False

    def treeview_IsSelected(self):
        return self.targetNode().isSelected()

    def treeview_Select(self, mode):

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            self.m_tree.ClearSelection()
            self.targetNode().SetSelected()

            if self.targetNode().m_value == SELECT_BATCH_FILE_PROMPT:
                self.m_tree.ClearSelection()

                self.select_batch_file()

            elif self.targetNode().m_value == UPDATE_FROM_FILE:
                self.m_tree.ClearSelection()

                data = self.update_treeData_from_file(self.m_batchFilePath)
                self.m_tree = self.build_tree(data)

            elif self.targetNode().m_value == REPLACE_BATCH_FILE:
                self.m_tree.ClearSelection()

                path = self.select_batch_file()
                data = self.update_treeData_from_file(path)
                self.m_tree = self.build_tree(data)

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
            # Don't allow multi-selection.
            self.m_tree.ClearSelection()
            self.targetNode().SetSelected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().SetSelected(False)

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            self.m_tree.ClearSelection()

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
    # Monkey
    # -------------------------------------------------------------------------

    def build_empty_tree(self):
        try:
            emptyTree = TreeNode(TREE_ROOT_TITLE)
            emptyTree.AddNode(EMPTY, SELECT_BATCH_FILE_PROMPT)
            return emptyTree
        except:
            lx.out(traceback.print_exc())
            return False

    def select_batch_file(self):
        try:
            self.m_batchFilePath = monkey.util.yaml_open_dialog()

            return self.m_batchFilePath
        except:
            lx.out(traceback.print_exc())
            return False

    def add_task(self, treeData=None):
        try:
            if treeData is None:
                treeData = self.treeData

            paths_list = modo.dialogs.fileOpen(
                ftype='$LXOB',
                title=OPEN_FILE_DIALOG_TITLE,
                multi=True,
                path=None
            )

            if not paths_list:
                return False

            if not isinstance(paths_list, list):
                paths_list = [paths_list]

            for path in paths_list:
                i = self.m_tree.AddNode(os.path.basename(path))

            return True

        except:
            lx.out(traceback.print_exc())
            return False

    def update_treeData_from_file(self, file_path=None):
        try:
            if file_path is None:
                file_path = self.m_batchFilePath

            return monkey.util.read_yaml(file_path)
        except:
            lx.out(traceback.print_exc())
            return False

    def save_treeData_to_file(self, file_path=None):
        try:
            if file_path is None:
                file_path = self.m_batchFilePath

            return monkey.util.write_yaml(self.treeData, file_path)
        except:
            lx.out(traceback.print_exc())
            return False

    def save_treeData_as(self, file_path=None):
        try:
            if file_path is None:
                file_path = self.m_batchFilePath

            return self.save_treeData_to_file(
                monkey.util.yaml_save_dialog()
            )
        except:
            lx.out(traceback.print_exc())
            return False

    def build_tree(self, treeData=None):
        try:
            if treeData is None:
                treeData = self.treeData

            if not treeData:
                return False

            tree = TreeNode(TREE_ROOT_TITLE)
            for i in treeData:
                if i[PATH]:
                    j = tree.AddNode(TASK, os.path.basename(i[PATH]))
                    for k, v in iter(sorted(i.iteritems())):
                        j.AddNode(k, v)
            tree.AddNode(EMPTY, ADD_TASK)
            tree.AddNode(EMPTY, UPDATE_FROM_FILE)
            tree.AddNode(EMPTY, REPLACE_BATCH_FILE)
            return tree

        except:
            lx.out(traceback.print_exc())
            return False

    # -------------------------------------------------------------------------
    # Attributes
    # -------------------------------------------------------------------------

    def attr_Count(self):
        return len(self.m_tree.columns)

    def attr_GetString(self, index):
        node = self.targetNode()

        if index == 0:
            return node.m_name
        elif node.m_value:
            return node.m_value
        else:
            return ""

sTREEVIEW_TYPE = " ".join(('vpapplication', 'WSTV', sSRV_USERNAME, NICE_NAME))

tags = {lx.symbol.sSRV_USERNAME:  sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE}

lx.bless(RenderMonkeyBatch, SERVERNAME, tags)
