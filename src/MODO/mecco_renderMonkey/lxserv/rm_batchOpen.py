# python

import lx, monkey, os
from monkey import message as message

class BatchOpenCommand(monkey.commander.CommanderClass):
    _path = lx.eval('query platformservice alias ? {scripts:}')

    def commander_arguments(self):
        return [
            {
                'name': 'path',
                'datatype': 'string',
                'flags': ['optional']
            }
        ]

    def basic_ButtonName(self):
        input_path = self.commander_arg_value(0)
        if input_path:
            return os.path.basename(input_path)
        else:
            lx.notimpl()

    def commander_execute(self, msg, flags):
        # Open the replay palette
        lx.eval('layout.createOrClose cookie:{renderMonkeyBatch} layout:{Monkey Batch} title:{renderMonkey Batch} width:720 height:300 persistent:1 style:palette open:?')

        # Try to get the path from the command line:
        input_path = self.commander_arg_value(0)

        batch = monkey.Batch()

        # Get the path from the user, if not given as argument:
        if not input_path:
            input_path = monkey.io.yaml_open_dialog()
            if input_path is None:
                return
            self.__class__._path = input_path

        # Rebuild the tree
        try:
            batch.set_batch_file(input_path)
            batch.regrow_tree()
        except Exception as err:
            modo.dialogs.alert(message("MECCO_RM", "OPEN_FILE_FAIL"), message("MECCO_RM", "OPEN_FILE_FAIL_MSG", str(err)), dtype='warning')

        finally:
            batch.rebuild_view()
            notifier = monkey.Notifier()
            notifier.Notify(lx.symbol.fCMDNOTIFY_CHANGE_ALL)

    def basic_Enable(self, msg):
        return True

lx.bless(BatchOpenCommand, "monkey.BatchOpen")