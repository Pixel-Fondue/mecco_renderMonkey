# python

import lxifc, lx
import json

DROPSOURCE_COMMAND = "rm_command"
DROP_SERVER = "rm_dropserver"
DROPSERVERUNIQUEKEY = "118310"


class TreeView( lxifc.TreeView,
                lxifc.Tree,
                lxifc.ListenerPort,
                lxifc.Attributes):

    """TreeView interface for the MODO API. Boilerplate pulled from:
    http://modo.sdk.thefoundry.co.uk/wiki/Python_Treeview_Example

    There is a lot of dark magic involved in the MODO API. Don't mess
    with this unless you know what you're doing."""

    # Global list of all created tree views.
    # These are used for shape and attribute changes
    _listenerClients = {}

    def __init__(self, **kwargs):
        # `self._root` returns the root TreeNode() object for the treeview.
        # Fun fact about MODO API inheritance: if our TreeView class were to
        # inherit `object` as is the norm, everything breaks. This causes various
        # problems with inheritance. For one, class variables are only reliable
        # if they are defined during `__init__()`, NOT up above it as normal.

        # Note: TreeView classes require a root TreeNode object. Without this,
        # Bad Things happen. Be sure to include this parameter when instantiating
        # the class for the first time.
        if 'root' in kwargs:
            self.__class__._root = kwargs.get('root')

        # Moves the primary column to the specified column index.
        #
        # The "primary" column (i.e. the one with the twirly carrot icon for hide/show
        # node children) is always the first column in the columns list, but is not
        # necessarily left-most in the TreeView (witness the items list).
        #
        # To move it over to the selcond-from-left slot, for example, provide this
        # function a value of 1.
        if 'primary_column_position' in kwargs:
            self.__class__._primary_column_position = kwargs.get('primary_column_position')

        # The available input regions as blessed by the parent `Lumberjack.bless()`
        # function. Once blessed, this should not change at any time during a MODO session.
        if 'input_regions' in kwargs:
            self.__class__._input_regions = kwargs.get('input_regions')

        # The controller object for the TreeNode and TreeView objects. We occasionally
        # need to phone home to tell it about important updates or ask for global information.
        # Added during the blessing.
        if 'controller' in kwargs:
            self.__class__._controller = kwargs.get('controller')


        # Because TreeView() does not inherit `object`, you cannot put a
        # classvariable declaration outside of __init__() without affecting all
        # subclasses.
        try:
            self._root
        except AttributeError:
            lx.out ('%s requires a root TreeNode on init.' % self.__class__.__name__)
            raise Exception('%s requires a root TreeNode on init.' % self.__class__.__name__)

        try:
            self._primary_column_position
        except AttributeError:
            self.__class__._primary_column_position = 0

        try:
            self._input_regions
        except AttributeError:
            self.__class__._input_regions = []

        try:
            self._controller
        except AttributeError:
            lx.out('%s requires a root controller object on init.' % self.__class__.__name__)
            raise Exception('%s requires a root controller object on init.' % self.__class__.__name__)


        # Finally, initialize the current node in the iterator.
        self.m_currentNode = kwargs.get('node') if kwargs.get('node') else self._root
        self.m_currentIndex = kwargs.get('curIndex') if 'curIndex' in kwargs else 0

    # --------------------------------------------------------------------------------------------------
    # Listener port
    # --------------------------------------------------------------------------------------------------

    @classmethod
    def addListenerClient(cls,listener):
        """Whenever a new tree view is created, we will add a copy of its
        listener so that it can be notified of attribute or shape changes"""
        treeListenerObj = lx.object.TreeListener(listener)
        cls._listenerClients[treeListenerObj.__peekobj__()] = treeListenerObj

    @classmethod
    def removeListenerClient(cls,listener):
        """When a view is destroyed, it will be removed from the list of clients
        that need notification."""
        treeListenerObject = lx.object.TreeListener(listener)
        if cls._listenerClients.has_key(treeListenerObject.__peekobj__()):
            del cls._listenerClients[treeListenerObject.__peekobj__()]

    @classmethod
    def notify_NewShape(cls):
        """Called whenever nodal hierarchy changes in any way. Slower than
        `notify_NewAttributes`, but necessary when nodes are added/removed/reparented."""
        for client in cls._listenerClients.values():
            if client.test():
                client.NewShape()

    @classmethod
    def notify_NewAttributes(cls):
        """Called when cell values are updated, but nodal hierarchy is unchanged.
        Faster than `notify_NewShape`, but does not update added/removed/reparented
        nodes."""
        for client in cls._listenerClients.values():
            if client.test():
                client.NewAttributes()

    #---  --------------------------------------------------------------------

    def lport_AddListener(self,obj):
        """Called from core code with the object that wants to
        bind to the listener port"""
        self.addListenerClient(obj)

    def lport_RemoveListener(self,obj):
        """Called from core when a listener needs to be removed from
        the port."""
        self.removeListenerClient(obj)

    # --------------------------------------------------------------------------------------------------
    # Target layer in the tree
    # --------------------------------------------------------------------------------------------------

    def targetNode(self):
        """Returns the targeted layer node in the current tier"""
        if self.m_currentIndex >= len(self.m_currentNode.children):
            return None
        return self.m_currentNode.children[ self.m_currentIndex ]

    # --------------------------------------------------------------------------------------------------
    # Each time the tree is spawned, we create a copy of ourselves at current
    # location in the tree and return it
    # --------------------------------------------------------------------------------------------------

    def tree_Spawn(self, mode):
        """Spawn a new instance of this tier in the tree."""

        # create an instance of our current location in the tree
        newTree = self.__class__(node=self.m_currentNode, curIndex=self.m_currentIndex)

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
        """Step up to the parent tier and set the selection in this tier to the
        current items index"""
        m_parent = self.m_currentNode.parent

        if m_parent:
            self.m_currentIndex = self.m_currentNode.index
            self.m_currentNode = m_parent
            return True
        return False

    def tree_ToChild(self):
        """Move to the child tier and set the selected node"""
        self.m_currentNode = self.m_currentNode.children[self.m_currentIndex]

    def tree_ToRoot(self):
        """Move back to the root tier of the tree"""
        self.m_currentNode = self._root

    def tree_IsRoot(self):
        """Check if the current tier in the tree is the root tier"""
        return (self.m_currentNode == self._root)

    def tree_ChildIsLeaf(self):
        """If the current tier has no children then it is
        considered a leaf"""
        return (len( self.m_currentNode.children ) == 0)

    def tree_Count(self):
        """Returns the number of nodes in this tier of
        the tree"""
        return len( self.m_currentNode.children )

    def tree_Current(self):
        """Returns the index of the currently targeted item in
        this tier"""
        return self.m_currentIndex

    def tree_SetCurrent(self, index):
        """Sets the index of the item to target in this tier"""
        self.m_currentIndex = index

    def tree_ItemState(self, guid):
        """Returns the item flags that define the state."""
        return self.targetNode().state

    def tree_SetItemState(self, guid, state):
        """Set the item flags that define the state."""
        self.targetNode().state = state


    # --------------------------------------------------------------------------------------------------
    # Tree view
    # --------------------------------------------------------------------------------------------------

    def treeview_StoreState(self, uid):
        lx.notimpl()

    def treeview_RestoreState(self, uid):
        lx.notimpl()

    def treeview_ColumnCount(self):
        """Returns the number of columns in the treeview."""
        return len(self._root.column_definitions)

    def treeview_ColumnInternalName(self, columnIndex):
        """Returns the internal name of a given column for use in configs, etc.
        Important that these never change."""
        if columnIndex < len(self._root.column_definitions):
            return self._root.column_definitions[columnIndex].get('name')

    def treeview_ColumnIconResource(self, columnIndex):
        """Returns the name of a 13px icon resource for the column header."""
        if columnIndex < len(self._root.column_definitions):
            icon_resource = self._root.column_definitions[columnIndex].get('icon_resource')
            if icon_resource:
                return icon_resource
        # Without returning something, MODO will crash.
        return ""

    def treeview_ColumnJustification(self, columnIndex):
        """Returns the desired justification setting for a given column.
        Expects the column to have a 'justify' key with a value of 'left',
        'center', or 'right'."""

        # define LXiTREEJUST_LEFT                0
        # define LXiTREEJUST_CENTER              1
        # define LXiTREEJUST_RIGHT               2

        lookup = {
            'left': 0,
            'center': 1,
            'right': 2
        }

        if columnIndex < len(self._root.column_definitions):
            string_value = self._root.column_definitions[columnIndex].get('justify', 'left')
            return lookup[string_value]

    def treeview_PrimaryColumnPosition(self):
        """Returns True for the column that should be 'primary', i.e. should have the carrot
        display for children, etc."""
        return self._primary_column_position

    def treeview_ColumnByIndex(self, columnIndex):
        """Returns a tuple with the name and width of a given column."""
        try:
            name = self._root.column_definitions[columnIndex]['name']
            width = self._root.column_definitions[columnIndex]['width']
            return (name, width)
        except:
            raise Exception('treeview_ColumnByIndex failed. Possibly malformed column dictionary.')

    def treeview_ToPrimary(self):
        """Move the tree to the primary selection"""
        if self._controller.primary:
            self.m_currentNode = self._controller.primary
            self.tree_ToParent()
            return True
        return False


    def treeview_IsSelected(self):
        return self.targetNode().selected

    def treeview_IsDescendantSelected (self):
        # Backwards for some reason...
        for child in self.targetNode().children:
            if child.selected:
                return False
        return True

    def treeview_Select(self, mode):
        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            self._controller.clear_selection()
            self.targetNode().selected = True

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD:
            self.targetNode().selected = True

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().selected = False

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            self._controller.clear_selection()

        self._controller.select_event_treeview()

    def treeview_CellCommand(self, columnIndex):
        """Cells can contain commands similar to Forms, and this is especially
        useful with query commands like booleans. Note that in order for the `treeview_CellCommand`
        to work, we must also specify a `treeview_BatchCommand` for multi-selections."""

        # Wisdom from Joe:
        # If GetString() returns NOTIMPL, then the value of the cell comes from whatever
        # is queried from the command cell. In core code, GetString() is just a Value() callback,
        # and if it returns NULL then we know to use the queried command's value.
        # It makes slightly more sense there.  The idea is that GetString() (Value()) are kind
        # of the override, and the queried value from CommandCell() is the default.
        # Mostly you use the override if you want an eyeball icon instead of a checkmark, for example.

        column_name = self._root.column_definitions[columnIndex]['name']
        cell_value_obj = self.targetNode().columns.get(column_name)
        if cell_value_obj is not None:
            if cell_value_obj.cell_command is not None:
                return cell_value_obj.cell_command
        lx.notimpl()

    def treeview_BatchCommand(self, columnIndex):
        """Similar to `treeview_CellCommand`, except this one is fired on batch selections.
        For `treeview_CellCommand` to work properly, an accompanying `treeview_BatchCommand` is required."""

        # From Joe:
        # BatchCommand() is used if you have multiple cells selected, and is
        # used to change all of them with a single click.

        column_name = self._root.column_definitions[columnIndex]['name']
        cell_value_obj = self.targetNode().columns.get(column_name)
        if cell_value_obj is not None:
            if cell_value_obj.batch_command is not None:
                return cell_value_obj.batch_command
            # If no BatchCommand() is implemented, fall back on CellCommand().
            elif cell_value_obj.cell_command is not None:
                return cell_value_obj.cell_command
        lx.notimpl()

    def treeview_ToolTip(self, columnIndex):
        if self.targetNode() is not None:
            toolTip = self.targetNode().tooltip(columnIndex)
            if toolTip:
                return toolTip
        lx.notimpl()

    def treeview_BadgeType(self, columnIndex, badgeIndex):
        lx.notimpl()

    def treeview_BadgeDetail(self, columnIndex, badgeIndex, badgeDetail):
        lx.notimpl()

    def treeview_IsInputRegion(self, columnIndex, regionID):
        """Returns True if the provided columnIndex corresponds to the provided regionID."""
        # NOTE: This code fires very, very frequently.
        # Speed is very important.

        column_name = self._root.column_definitions[columnIndex]['name']

        try:
            target_region = self.targetNode().columns[column_name].input_region
        except AttributeError:
            # The column has no input region assignment.
            return False

        # regionID zero is reserved for .anywhere. It should always return True.
        if regionID == 0:
            return True

        if target_region == self._input_regions[regionID]:
            return True

        return False

    def treeview_SupportedDragDropSourceTypes(self, columnIndex):
        """Wisdom from Joe:

        The tree has to implement 2 methods to be a source,  SupportedDragDropTypes()
        and GetDragDropSourceObject().    To be a destination, it has to impelment
        GetDragDropDestinationObject()

        SupportedDragDropTypes() is a space-delimited list of source types you
        can support for a drag.  These can be your own strings if you want to
        define your own types, or it can be standard drop types,
        like LXsDROUPSOURCE_ITEMS.

        GetDragDropSourceObject() returns a COM object (however those are wrapped in Python)
        representing the source item being dragged.  Often we use ILxValueArray
        (even if it's just one item, just in case there are more) containing the
        elements, but you can use an arbitrary object if you want.  You can define
        your own COM objects as by adding the ILxValue interface to your class,
        although I'm not sure how you do that in Python.

        Together, that gets D&D going.  To accept drops, you have to implement
        GetDragDropDestinationObject(), which just returns a COM object representing
        the drop point.

        Be aware that this is called frequently (like, on every mouse move over your tree).

        An separate ILxDrop server then takes the source and destination objects
        and decides if it can drop there.  If the user decides to use an action from
        that server, then it does the actual work for the drop (although sometimes
        the destination object does the actual drop, such as for color presets).

        That's it, really.
        """
        if columnIndex != 0:
            return ""
        if all(node.draggable() for node in self._root.selected_descendants):
            return DROPSOURCE_COMMAND
        else:
            return ""

    def treeview_GetDragDropSourceObject(self, columnIndex, type):
        if columnIndex != 0:
            return None

        if type != DROPSOURCE_COMMAND:
            return None

        # Create a string value object.
        cmd_svc = lx.service.Command ()
        vaQuery = cmd_svc.CreateQueryObject(lx.symbol.sTYPE_STRING)

        # Create a value array so we can access it.
        va = lx.object.ValueArray ()
        va.set(vaQuery)

        # Add unique key
        va.AddString(DROPSERVERUNIQUEKEY)

        # Add selected children indices
        for child in self._root.selected_descendants:
            assert(child.draggable())
            va.AddString(json.dumps(child.path))

        return va

    def treeview_GetDragDropDestinationObject(self, columnIndex, location):
        if columnIndex != 0:
            return None

        if location != 0 and location != 2:
            return None

        # Create a string value object.
        cmd_svc = lx.service.Command ()
        vaQuery = cmd_svc.CreateQueryObject(lx.symbol.sTYPE_STRING)

        # Create a value array so we can access it.
        va = lx.object.ValueArray ()
        va.set(vaQuery)

        # Add unique key
        va.AddString(DROPSERVERUNIQUEKEY)

        # Add target index
        if location == 2:
            idx = self.m_currentIndex + 1
        else:
            idx = self.m_currentIndex

        va.AddString(json.dumps(self.m_currentNode.path + [idx]))

        return va
    # --------------------------------------------------------------------------------------------------
    # Attributes
    # --------------------------------------------------------------------------------------------------

    def attr_Count(self):
        return len(self._root.column_definitions)

    def attr_GetString(self, index):
        """Returns a rich text string to display in a cell. Rich text can include
        flags for font, color, and/or icons inline with the rest of the text.

        e.g. '\x03(c:4113)Gray Text' < prints "Gray Text" in... gray.

        We handle most of the rich text formatting in the TreeValue object and
        its Font and Color sidecar objects.

        This value should be thought of as an override for `treeview_CellCommand()`.
        If `attr_GetString()` fires `lx.notimpl()`, the tree will fallback on
        the result of the `CellCommand`. If neither is implemented, the cell will
        be blank.

        (NOTE: Empty cells render with zero height in the tree. Ugly.)"""

        column_definitions = self._root.column_definitions
        node = self.targetNode()

        # I'll be honest: I don't understand this loop. It's here for some
        # reason, and the method fails if I try to do it without the loop.
        # So it's here. If you can think of a better way, by all means.
        for n in range(len(column_definitions)):
            if index == n:

                # If we're using a treeview_CellCommand() query to render the cell,
                # we don't send a string.
                if node.columns[column_definitions[n]['name']].use_cell_command_for_display:
                    lx.notimpl()

                try:
                    # Print the `display_value` in the cell
                    return node.columns[column_definitions[n]['name']].display_value
                except:
                    break

        # If node.columns[] doesn't contain a key for some reason,
        # we need to fail gracefully lest we crash MODO.
        lx.notimpl()
