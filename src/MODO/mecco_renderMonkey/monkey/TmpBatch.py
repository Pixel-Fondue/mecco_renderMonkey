# python

import lumberjack, io
from symbols import *
from BatchTreeNode import BatchTreeNode

# TODO refactor names
NO_FILE_SELECTED = "(no batch file)"
BATCHFILE = "batch"
ADD_GENERIC = '(add...)'
ADD_TASK = '(add task...)'
ADD_PARAM = '(add parameter...)'
EMPTY = ''

class Batch(lumberjack.Lumberjack):

    _batch_file_path = ''

    def __init__(self):
        super(Batch, self).__init__(on_bless=self.on_bless)
        
    def on_bless(self):
        self.regrow_tree()
        
    def batch_file_path():
        def fget(self):
            return self.__class__._batch_file_path
        def fset(self, value):
            self.__class__._batch_file_path = value
        return locals()

    batch_file_path = property(**batch_file_path())
    
    # We extend the default Lumberjack `TreeNode` object for our own nefarious purposes.
    # To use this class in Lumberjack, we overwrite the create_child method to create our `TreeNode` subclasses.
    def create_child_node(self, **kwargs):
        return BatchTreeNode(**kwargs)
    
    def add_task(self, paths_list, batch_root_node=None):
        if not batch_root_node:
            batch_root_node = self.root.children()[0]

        if not paths_list:
            return False

        paths_list = paths_list if isinstance(paths_list, list) else [paths_list]

        for path in paths_list:
            self.grow_node([{SCENE_PATH: path, FRAMES: monkey.defaults.get(FRAMES)}], batch_root_node, 1)

        if self.batch_file_path:
            self.save_to_file()
        else:
            self.save_temp_file()

        self.regrow_tree()

    def node_file_root(self, tree_node):
        return tree_node.ancestors()[0]

    def set_batch_file(self, file_path=None):
        self.batch_file_path = file_path

    def close_file(self):
        self.clear_selection()
        self.batch_file_path = None
        self.regrow_tree()

    def save_to_file(self, file_path=None):
        if file_path:
            self.batch_file_path = file_path

        elif not self.batch_file_path:
            self.batch_file_path = monkey.io.yaml_save_dialog()

        return monkey.io.write_yaml(self.tree_to_object(), self.batch_file_path)

    def save_temp_file(self):
        file_path = monkey.util.path_alias(':'.join((KIT_ALIAS, QUICK_BATCH_PATH)))
        if monkey.batch.batch_has_status(file_path):
            monkey.batch.batch_status_delete(file_path)
        self.save_to_file(file_path)

    @staticmethod
    def iterate_anything(obj):
        if isinstance(obj, (list, tuple)):
            return {k: v for k, v in enumerate(obj)}.iteritems()
        if isinstance(obj, dict):
            return obj.iteritems()

    def grow_node(self, branch, parent_node, depth=0):

        if depth == 0:
            node_region = REGIONS[1]
            add_node = ADD_TASK
            add_region = REGIONS[8]
        elif depth == 1:
            node_region = REGIONS[2]
            add_node = ADD_PARAM
            add_region = REGIONS[9]
        elif depth == 2:
            node_region = REGIONS[4]
            add_node = ADD_GENERIC
            if isinstance(branch, dict):
                add_region = REGIONS[11]
            else:
                add_region = REGIONS[10]
        else:
            node_region = REGIONS[6]
            add_node = ADD_GENERIC
            if isinstance(branch, dict):
                add_region = REGIONS[11]
            else:
                add_region = REGIONS[10]

        if isinstance(branch, (list, tuple, dict)):
            for key, value in sorted(self.iterate_anything(branch)):

                if key == SCENE_PATH:
                    value_type = PATH_OPEN_SCENE
                elif key == DESTINATION:
                    value_type = PATH_SAVE_IMAGE
                elif key == FORMAT:
                    value_type = IMAGE_FORMAT
                elif key == FRAMES:
                    value_type = FRAME_RANGE
                else:
                    value_type = type(value).__name__

                if isinstance(value, (list, tuple, dict)):
                    node = self.add_child(parent=parent_node, key=key, value=value_type, node_region=node_region, value_type=value_type)
                    self.grow_node(value, node, depth + 1)

                else:
                    node = self.add_child(parent=parent_node, key=key, value=value, node_region=node_region, value_type=value_type)

        self.add_child(parent=parent_node, key=add_node, value=EMPTY, node_region=add_region, selectable=False, ui_only=True)

    def regrow_tree(self):
        batch_file_path = self.batch_file_path if self.batch_file_path else NO_FILE_SELECTED

        self.clear_selection()
        self.clear()

        batch_root_node = self.add_child(parent=self.root, key=BATCHFILE, value=batch_file_path, node_region=REGIONS[7])

        batch_root_node.add_state_flag(lumberjack.fTREE_VIEW_ITEM_EXPAND)

        if self.batch_file_path:
            batch = io.read_yaml(self.batch_file_path)
            self.grow_node(batch, batch_root_node)

        if len(batch_root_node.children) == 0:
            self.add_child(parent=batch_root_node, key=ADD_TASK, value=EMPTY, node_region=REGIONS[8], selectable=False, ui_only=True)

        return self.root

    def node_data(self, node):
        if node.value_type() in (list.__name__, tuple.__name__):
            data = []
            for child in node.children():
                if not child.ui_only():
                    child_value = self.node_data(child)
                    data.append(child_value)
            return data

        elif node.value_type() == dict.__name__:
            data = {}
            for child in node.children():
                if not child.ui_only():
                    child_value = self.node_data(child)
                    data[child.key()] = child_value
            return data

        elif node.value_type() == type(None).__name__:
            return None

        else:
            return node.raw_value()

    def tree_to_object(self):
        batch = []
        for child in self.root.child_by_key(BATCHFILE).children():
            if child.value_type() is not None:
                batch.append(self.node_data(child))
        return batch

    def select_event_treeview(self):
        pass
0