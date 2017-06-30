# python

import lx, lxu, lxifc, modo

import monkey
from monkey.symbols import *
from monkey.util import markup, bitwise_rgb, bitwise_hex
# from monkey.util import debug, breakpoint

from os.path import basename

# Text Colors
RED = markup('c', bitwise_rgb(255, 0, 0))
BLUE = markup('c', bitwise_hex('#0e76b7'))
GRAY = markup('c', '4113')

# Font Styles
FONT_DEFAULT = markup('f', 'FONT_DEFAULT')
FONT_NORMAL = markup('f', 'FONT_NORMAL')
FONT_BOLD = markup('f', 'FONT_BOLD')
FONT_ITALIC = markup('f', 'FONT_ITALIC')

class BatchAddParam(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('parameter', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        param = self.dyna_String(0).lower() if self.dyna_IsSet(0) else None
        if not param:
            return lx.symbol.e_FAILED

        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        sel = set([node for node in sel if node.node_region() == REGIONS[1]])
        sel = [node for node in sel if not param in [child.key() for child in node.children()]]

        val = monkey.defaults.get(param)
        if val is None:
            lx.out("Invalid parameter name.")
            return lx.symbol.e_FAILED

        if isinstance(val, (list, tuple, dict)):
            val = type(val).__name__
            val_type = val
        elif param == SCENE_PATH:
            val_type = PATH_SAVE_SCENE
        elif param == FORMAT:
            val_type = IMAGE_FORMAT
        elif param == DESTINATION:
            val_type = PATH_SAVE_IMAGE
        else:
            val_type = type(val).__name__

        for node in sel:
            new_node = node.add_child(param, val, REGIONS[2], val_type)
            new_node.reorder_bottom()

            if val_type in (list.__name__, tuple.__name__, dict.__name__):
                region = REGIONS[11] if val_type == dict.__name__ else REGIONS[10]
                new_node.add_child(ADD_GENERIC, EMPTY, region, selectable=False, ui_only=True)
                new_node.add_state_flag(fTREE_VIEW_ITEM_EXPAND)

        _BATCH.save_to_file()
        BatchTreeView.notify_NewShape()


class BatchAddToList(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('value', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        value = self.dyna_String(0) if self.dyna_IsSet(0) else None
        if not value:
            return lx.symbol.e_FAILED

        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        sel = set([node for node in sel if node.value_type() in (list.__name__, tuple.__name__)])
        sel = [node for node in sel if not value in [child.raw_value() for child in node.children()]]

        if not sel:
            lx.out("Invalid selection.")
            return lx.symbol.e_FAILED

        for node in sel:
            new_node = node.add_child(len(node.children())-1,value,REGIONS[4],type(value).__name__)
            new_node.reorder_bottom()

        _BATCH.save_to_file()
        BatchTreeView.notify_NewShape()


class BatchAddToDict(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('key', lx.symbol.sTYPE_STRING)
        self.dyna_Add('value', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        key = self.dyna_String(0) if self.dyna_IsSet(0) else None
        value = self.dyna_String(1) if self.dyna_IsSet(0) else None
        if not key or not value:
            return lx.symbol.e_FAILED

        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        sel = set([node for node in sel if node.value_type() == dict.__name__])
        sel = [node for node in sel if not key in [child.key() for child in node.children()]]

        if not sel:
            lx.out("Invalid selection.")
            return lx.symbol.e_FAILED

        for node in sel:
            new_node = node.add_child(key,value,REGIONS[4],type(value).__name__)
            new_node.reorder_bottom()

        _BATCH.save_to_file()
        BatchTreeView.notify_NewShape()


class BatchDeleteNodes(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH.tree().selected_children()
        _BATCH.tree().clear_selection()

        for node in sel:
            if node.key() != SCENE_PATH:
                node.destroy()
                node.parent().update_child_keys()

        _BATCH.save_to_file()

        BatchTreeView.notify_NewShape()


class BatchReorderNodes(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('mode', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        mode = self.dyna_String(0).lower() if self.dyna_IsSet(0) else REORDER_ARGS['TOP']

        if mode not in [v for k, v in REORDER_ARGS.iteritems()]:
            lx.out("Wow, no idea to do with \"{}\". Sorry.".format(mode))
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().selected_children()

        for node in sel:
            if mode == REORDER_ARGS['TOP']:
                node.reorder_top()
            elif mode == REORDER_ARGS['BOTTOM']:
                node.reorder_bottom()
            elif mode == REORDER_ARGS['UP']:
                node.reorder_up()
            elif mode == REORDER_ARGS['DOWN']:
                node.reorder_down()

        _BATCH.save_to_file()
        BatchTreeView.notify_NewShape()

        # Unsure why we lose selection, but we do. Have to re-select.
        _BATCH.tree().clear_selection()
        for node in sel:
            node.set_selected()


class BatchSelectShift(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('mode', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        mode = self.dyna_String(0).lower() if self.dyna_IsSet(0) else SELECT_SHIFT_ARGS['UP']

        if mode not in [v for k, v in SELECT_SHIFT_ARGS.iteritems()]:
            lx.out("Wow, no idea to do with \"{}\". Sorry.".format(mode))
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().selected_children()

        for node in sel:
            if mode == SELECT_SHIFT_ARGS['UP']:
                node.select_shift_up()
            elif mode == SELECT_SHIFT_ARGS['DOWN']:
                node.select_shift_down()

        BatchTreeView.notify_NewShape()

        # Unsure why we lose selection, but we do. Have to re-select.
        _BATCH.tree().clear_selection()
        for node in sel:
            node.set_selected()


class BatchEditNodes(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        if len(set([i.value_type() for i in sel])) > 1:
            sel = [_BATCH.tree().primary()]

        if primary_node.node_region() == REGIONS[1]:
            path = monkey.io.lxo_open_dialog()
            if path is not False:
                for node in sel:
                    node.child_by_key(SCENE_PATH).set_value(path)

        elif primary_node.value_type() == PATH_OPEN_SCENE:
            path = monkey.io.lxo_open_dialog()
            if path is not False:
                for node in sel:
                    node.set_value(path)

        elif primary_node.value_type() == PATH_SAVE_IMAGE:
            path = monkey.io.image_save_dialg()
            format = lx.eval("dialog.fileSaveFormat ? format")

            if path is not False:
                for node in sel:
                    node.set_value(path)
                    if node.parent().child_by_key(FORMAT):
                        node.parent().child_by_key(FORMAT).set_value(format)
                    else:
                        new_node = node.parent().add_child(FORMAT, format, REGIONS[2], IMAGE_FORMAT)
                        new_node.reorder_bottom()

        elif primary_node.value_type() == IMAGE_FORMAT:
            path = monkey.io.image_save_dialg()
            format = lx.eval("dialog.fileSaveFormat ? format")

            if path is not False:
                for node in sel:
                    if node.parent().child_by_key(DESTINATION):
                        node.parent().child_by_key(DESTINATION).set_value(path)
                    else:
                        new_node = node.parent().add_child(DESTINATION, path, REGIONS[2], PATH_SAVE_IMAGE)
                        new_node.reorder_bottom()

                    node.set_value(format)

        elif primary_node.value_type() == FRAME_RANGE:
            old_value = primary_node.raw_value()
            lx.eval('monkey.BatchEditString')
            frames_list = monkey.util.frames_from_string(primary_node.raw_value())
            if not frames_list:
                modo.dialogs.alert('Invalid Frame Range','Invalid frame range.','error')
                primary_node.set_value(old_value)
            else:
                for node in sel:
                    node.set_value(''.join([i for i in primary_node.raw_value() if i in "0123456789-:,"]))


        elif primary_node.value_type() in (int.__name__, float.__name__):
            try:
                lx.eval('monkey.BatchEditNumber')
            except:
                pass

        elif primary_node.value_type() == (str.__name__):
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        BatchTreeView.notify_NewShape()
        _BATCH.save_to_file()


class BatchEditNodesAdvanced(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        if len(set([i.value_type() for i in sel])) > 1:
            sel = [_BATCH.tree().primary()]

        if primary_node.node_region() == REGIONS[1]:
            path = monkey.io.lxo_open_dialog()
            if path is not False:
                for node in sel:
                    node.child_by_key(SCENE_PATH).set_value(path)

        elif primary_node.value_type() == PATH_OPEN_SCENE:
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        elif primary_node.value_type() == PATH_SAVE_IMAGE:
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        elif primary_node.value_type() == IMAGE_FORMAT:
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        elif primary_node.value_type() == FRAME_RANGE:
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        elif primary_node.value_type() in (int.__name__, float.__name__):
            try:
                lx.eval('monkey.BatchEditNumber')
            except:
                pass

        elif primary_node.value_type() == (str.__name__):
            try:
                lx.eval('monkey.BatchEditString')
            except:
                pass

        BatchTreeView.notify_NewShape()
        _BATCH.save_to_file()


class BatchEditNumber(lxu.command.BasicCommand):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('value', lx.symbol.sTYPE_FLOAT)

    def basic_Execute(self, msg, flags):
        if not self.dyna_IsSet(0) or self.dyna_Float(0) is None:
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        if not sel:
            return lx.symbol.e_FAILED

        if len(set([i.value_type() for i in sel])) > 1:
            sel = [_BATCH.tree().primary()]

        for node in sel:
            if self.dyna_Float(0).is_integer():
                node.set_value(int(self.dyna_Float(0)))
            else:
                node.set_value(self.dyna_Float(0))

    def cmd_DialogInit(self):
        self.attr_SetFlt(0, float(_BATCH.tree().primary().raw_value()))


class BatchEditString(lxu.command.BasicCommand):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('value', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        if not self.dyna_IsSet(0) or self.dyna_String(0) is None:
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        if not sel:
            return lx.symbol.e_FAILED

        if len(set([i.value_type() for i in sel])) > 1:
            sel = [_BATCH.tree().primary()]

        for node in sel:
            node.set_value(self.dyna_String(0))

    def cmd_DialogInit(self):
        self.attr_SetString(0, str(_BATCH.tree().primary().raw_value()))


class BatchResetNodes(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        primary_node = _BATCH.tree().primary()
        if not primary_node:
            lx.out("Nothing selected.")
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().children()[0].selected_children()
        sel = set([node for node in sel if node.node_region() == REGIONS[2]])

        for node in sel:
            node.set_value(monkey.defaults.get(node.key()))

        BatchTreeView.notify_NewAttributes()
        _BATCH.save_to_file()


class BatchRender(lxu.command.BasicCommand):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('mode', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        try:
            mode = self.dyna_String(0).lower() if self.dyna_IsSet(0) else 'run'

            if _BATCH._batch_file_path:
                dry = False
                if mode == 'test':
                    dry = True

                res = 1
                if mode == 'half':
                    res = .5
                elif mode == 'quarter':
                    res = .25
                elif mode == 'eighth':
                    res = .125
                elif mode == 'sixteenth':
                    res = 1.0/16

                monkey.batch.run(_BATCH.batch_file_path(), dry_run=dry, res_multiply=res)

            else:
                return lx.symbol.e_FAILED

        except SystemExit:
            pass


class BatchExample(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.util.path_alias(':'.join((KIT_ALIAS, QUICK_BATCH_PATH)))
        if path:
            lx.eval('{} {{{}}}'.format(CMD_BatchExportTemplate, path))
            _BATCH.set_batch_file(path)
            _BATCH.regrow_tree()
            BatchTreeView.notify_NewShape()


class BatchOpenStatusFile(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = _BATCH.batch_file_path()
        if not path:
            modo.dialogs.alert("no batch file", "No batch file selected.", 'error')
            return lx.symbol.e_FAILED
        if not monkey.batch.batch_has_status(path):
            modo.dialogs.alert("no status file", "No batch status file exists.", 'error')
            return lx.symbol.e_FAILED

        lx.eval('file.open {{{}}}'.format(monkey.batch.batch_status_file(path)))


class BatchOpenInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH.batch_file_path():
            lx.eval('file.open {{{}}}'.format(_BATCH.batch_file_path()))


class BatchRevealInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH.batch_file_path():
            lx.eval('file.revealInFileViewer {{{}}}'.format(_BATCH.batch_file_path()))


class BatchNew(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            monkey.io.write_yaml([], path)

            _BATCH.set_batch_file(path)
            _BATCH.regrow_tree()
            BatchTreeView.notify_NewShape()


class BatchSaveAs(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            _BATCH.save_to_file(path)
            BatchTreeView.notify_NewShape()


class BatchOpenTaskScene(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH.tree().children()[0].selected_children()
        sel = set([node for node in sel if node.node_region() == REGIONS[1]])
        if len(sel):
            for node in sel:
                lx.eval('scene.open {{{}}}'.format(node.child_by_key(SCENE_PATH).raw_value()))

sTREEVIEW_TYPE = " ".join((VPTYPE, IDENT, sSRV_USERNAME, NICE_NAME))

sINMAP = "name[{}] regions[{}]".format(
    sSRV_USERNAME, " ".join(
        ['{}@{}'.format(n, i) for n, i in enumerate(REGIONS) if n != 0]
    )
)

#tags = {lx.symbol.sSRV_USERNAME: sSRV_USERNAME,
#        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE,
#        lx.symbol.sINMAP_DEFINE: sINMAP}

#lx.bless(BatchTreeView, SERVERNAME, tags)

lx.bless(BatchAddParam, CMD_BatchAddParam)
lx.bless(BatchAddToList, CMD_BatchAddToList)
lx.bless(BatchAddToDict, CMD_BatchAddToDict)
lx.bless(BatchDeleteNodes, CMD_BatchDeleteNodes)
lx.bless(BatchReorderNodes, CMD_BatchReorderNodes)
lx.bless(BatchSelectShift, CMD_BatchSelectShift)
lx.bless(BatchEditNodes, CMD_BatchEditNodes)
lx.bless(BatchEditNodesAdvanced, CMD_BatchEditNodesAdvanced)
lx.bless(BatchResetNodes, CMD_BatchResetNodes)
lx.bless(BatchOpenTaskScene, CMD_BatchOpenTaskScene)
lx.bless(BatchRender, CMD_BatchRender)
lx.bless(BatchExample, CMD_BatchExample)
lx.bless(BatchOpenInFilesystem, CMD_BatchOpenInFilesystem)
lx.bless(BatchRevealInFilesystem, CMD_BatchRevealInFilesystem)
lx.bless(BatchNew, CMD_BatchNew)
lx.bless(BatchSaveAs, CMD_BatchSaveAs)
lx.bless(BatchOpenStatusFile, CMD_BatchOpenStatusFile)

lx.bless(BatchEditNumber, CMD_BatchEditNumber)
lx.bless(BatchEditString, CMD_BatchEditString)
