# !/usr/bin/env python
 
import lx,lxifc,modo
 
SERVERNAME = 'RenderMonkeyBatch'
 
# --------------------------------------------------------------------------------------------------
# Node styles
# --------------------------------------------------------------------------------------------------
 
fTREE_VIEW_ITEM_ATTR =               0x00000001
fTREE_VIEW_ITEM_EXPAND =             0x00000002
fTREE_VIEW_ATTR_EXPAND =             0x00000004
fTREE_VIEW_ROWCOLOR_ORANGE =	     0x00050000
fTREE_VIEW_ROWCOLOR_RED =		     0x00010000
 
# --------------------------------------------------------------------------------------------------
# Generic layer node object that represents each entry in the tree
# --------------------------------------------------------------------------------------------------
 
class TreeNode(object):
 
    _Primary = None
 
    def __init__(self, name, value=None, parent=None):
        self.m_name = name
        self.m_value = value
        self.m_parent = parent
        self.m_children = []
        self.state = 0
        self.selected = False
        

        #For column sizes you can use proportions via negative values.  
        #So -1 and -2 would mean that one column is half the size of the other 
        #(total size would be 3 units, so the -1 column is 1 unit and -2 column is 2 units).  
        #You can mix pixel sizes with proportional sizes, 
        #so -1 and 90 means that one is 90 pixels and the other takes up the remaining space.
        self.columns = (("Name", -1),
                        ("Value", -3))
 
        self.toolTips = {}
 
    def AddNode(self, name, value=""):
        self.m_children.append( TreeNode(name, value, self) )
        return self.m_children[-1]
 
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
 
 
# --------------------------------------------------------------------------------------------------
# Build the structure
# --------------------------------------------------------------------------------------------------
 
_theTree = TreeNode('Tasks')
 
scenefile = _theTree.AddNode('file.lxo')

scenefile_path = scenefile.AddNode("path", "/path/to/file/that/might/be/deep.lxo")
scenefile_path.setToolTip(0,"")

scenefile_frames = scenefile.AddNode("frames", "1-5,6,9-7")
scenefile_frames.setToolTip(0,"")

scenefile_destination = scenefile.AddNode("destination", "./frames")
scenefile_destination.setToolTip(0,"")

scenefile_format = scenefile.AddNode("format", "JPG")
scenefile_format.setToolTip(0,"")

scenefile_width = scenefile.AddNode("width", "")
scenefile_width.setToolTip(0,"")

scenefile_height = scenefile.AddNode("height", "")
scenefile_height.setToolTip(0,"")

scenefile_groups = scenefile.AddNode("groups", "")
scenefile_groups.setToolTip(0,"")

scenefile_outputs = scenefile.AddNode("outputs", "")
scenefile_outputs.setToolTip(0,"")

# expand the first node
scenefile.setState(fTREE_VIEW_ITEM_EXPAND)

scenefile2 = _theTree.AddNode('file2.lxo')
scenefile3 = _theTree.AddNode('file3.lxo')
 

    
# --------------------------------------------------------------------------------------------------
# Tree View
# --------------------------------------------------------------------------------------------------
 
class RenderMonkeyBatchView(lxifc.TreeView,
                    lxifc.Tree,
                    lxifc.ListenerPort,
                    lxifc.Attributes):
 
    # Gloabal list of all created tree views.
    # These are used for shape and attribute changes
    _listenerClients = {}
 
    def __init__(self, node = None, curIndex = 0):
 
        if node is None:
            node = _theTree
 
        self.m_currentNode = node
        self.m_currentIndex = curIndex
 
    # --------------------------------------------------------------------------------------------------
    # Listener port
    # --------------------------------------------------------------------------------------------------
 
    @classmethod
    def addListenerClient(cls,listener):
        """
            Whenever a new tree view is created, we will add
            a copy of its listener so that it can be notified
            of attribute or shape changes
        """
        treeListenerObj = lx.object.TreeListener(listener)
        cls._listenerClients[treeListenerObj.__peekobj__()] = treeListenerObj
 
    @classmethod
    def removeListenerClient(cls,listener):
        """
            When a view is destroyed, it will be removed from
            the list of clients that need notification.
        """
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
 
    #---  --------------------------------------------------------------------
 
    def lport_AddListener(self,obj):
        """
            Called from core code with the object that wants to
            bind to the listener port
        """
        self.addListenerClient(obj)
 
    def lport_RemoveListener(self,obj):
        """
            Called from core when a listener needs to be removed from
            the port.
        """
        self.removeListenerClient(obj)
 
    # --------------------------------------------------------------------------------------------------
    # Target layer in the tree
    # --------------------------------------------------------------------------------------------------
 
    def targetNode(self):
        """
            Returns the targeted layer node in the current tier
        """
        return self.m_currentNode.m_children[ self.m_currentIndex ]
 
    # --------------------------------------------------------------------------------------------------
    # Each time the tree is spawned, we create a copy of ourselves at current
    # location in the tree and return it
    # --------------------------------------------------------------------------------------------------
 
    def tree_Spawn(self, mode):
        """
            Spawn a new instance of this tier in the tree.
        """
 
        # create an instance of our current location in the tree
        newTree = RenderMonkeyBatchView(self.m_currentNode,self.m_currentIndex)
 
        # Convert to a tree interface
        newTreeObj = lx.object.Tree(newTree)
 
        if mode == lx.symbol.iTREE_PARENT:
            # move the tree to the parent tier
            newTreeObj.ToParent()
 
        elif mode == lx.symbol.iTREE_CHILD:
            # move tree to child tier
            newTreeObj.ToChild()
 
        elif mode == lx.symbol.iTREE_ROOT:
            #move tree to root tier
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
        self.m_currentNode = _theTree
 
    def tree_IsRoot(self):
        """
            Check if the current tier in the tree is the root tier
        """
        if self.m_currentNode == _theTree:
            return True
        else:
            return False
 
    def tree_ChildIsLeaf(self):
        """
            If the current tier has no children then it is
            considered a leaf
        """
        if len( self.m_currentNode.m_children ) > 0:
            return False
        else:
            return True
 
    def tree_Count(self):
        """
            Returns the number of nodes in this tier of
            the tree
        """
        return len( self.m_currentNode.m_children )
 
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
 
 
    # --------------------------------------------------------------------------------------------------
    # Tree view
    # --------------------------------------------------------------------------------------------------
 
    def treeview_StoreState(self, uid):
        lx.notimpl()
 
    def treeview_RestoreState(self, uid):
        lx.notimpl()
 
    def treeview_ColumnCount(self):
        return len(_theTree.columns)
 
    def treeview_ColumnByIndex(self, columnIndex):
        return _theTree.columns[columnIndex]
 
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
            _theTree.ClearSelection()
            self.targetNode().SetSelected()
 
        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
            #Don't allow multi-selection.
            _theTree.ClearSelection()
            self.targetNode().SetSelected()
 
        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().SetSelected(False)
 
        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            _theTree.ClearSelection()
 
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
 
    # --------------------------------------------------------------------------------------------------
    # Attributes
    # --------------------------------------------------------------------------------------------------
 
    def attr_Count(self):
        return len(_theTree.columns)
 
    def attr_GetString(self, index):
        node = self.targetNode()
 
        if index == 0:
            return node.m_name
        elif node.m_value:
            return node.m_value
        else:
            return ""
 
 
tags = {lx.symbol.sSRV_USERNAME:  "RenderMonkeyBatch",
        lx.symbol.sTREEVIEW_TYPE: "vpapplication WSTV RenderMonkeyBatchView RenderMonkey_Batch"}
 
lx.bless(RenderMonkeyBatchView, SERVERNAME, tags)