# python

import lx, monkey, os
from monkey import message as message

class BatchAddParamCommand(monkey.commander.CommanderClass):

    def commander_arguments(self):
        return [
            {
                'name': 'parameter',
                'datatype': 'string',
                'flags': [],
            }
        ]

    def commander_execute(self, msg, flags):
        # Open the batch palette
        lx.eval('layout.createOrClose cookie:{renderMonkeyBatch} layout:{Monkey Batch} title:{renderMonkey Batch} width:720 height:300 persistent:1 style:palette open:?')

        param = self.commander_arg_value(0, None)

        if not param:
            return lx.symbol.e_FAILED

        batch = monkey.Batch()
        primary_node = batch.primary
        
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED
            
        sel_desc = batch.selected_descendants
        sel = []
        for node in batch.selected_descendants:
            while node is not None and node.node_region() != monkey.REGIONS[1]:
                node = node.parent
            if node is not None:
                sel.append(node)

        sel = [node for node in sel if not param in [child.key() for child in node.children]]

        val = monkey.defaults.get(param)
        if val is None:
            lx.out("Invalid parameter name.")
            return lx.symbol.e_FAILED

        if isinstance(val, (list, tuple, dict)):
            val = type(val).__name__
            val_type = val
        elif param == monkey.SCENE_PATH:
            val_type = monkey.PATH_SAVE_SCENE
        elif param == monkey.FORMAT:
            val_type = monkey.IMAGE_FORMAT
        elif param == monkey.DESTINATION:
            val_type = monkey.PATH_SAVE_IMAGE
        else:
            val_type = type(val).__name__

        for node in sel:
            new_node = batch.add_child(parent=node, index = node.non_ui_only_child_count(), key=param, value=val, node_region=monkey.REGIONS[2], value_type=val_type)

            if val_type in (list.__name__, tuple.__name__, dict.__name__):
                region = monkey.REGIONS[11] if val_type == dict.__name__ else monkey.REGIONS[10]
                new_node = batch.add_child(parent=new_node, key=monkey.ADD_GENERIC, value=monkey.EMPTY, node_region=region, selectable=False, ui_only=True)
                new_node.add_state_flag(monkey.lumberjack.fTREE_VIEW_ITEM_EXPAND)

        batch.save_to_file()
        
        batch.unsaved_changed = True
        
        batch.rebuild_view()
        notifier = monkey.Notifier()
        notifier.Notify(lx.symbol.fCMDNOTIFY_CHANGE_ALL)        
        
    def basic_Enable(self, msg):
        return True

lx.bless(BatchAddParamCommand, "monkey.BatchAddParam")