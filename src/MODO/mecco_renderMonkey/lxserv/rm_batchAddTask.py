# python

import lx, monkey, os
from monkey import message as message

class BatchAddTaskCommand(monkey.commander.CommanderClass):
    _path_list = [lx.eval('query platformservice alias ? {scripts:}')]

    def commander_arguments(self):
        return [
            {
                'name': 'path',
                'datatype': 'string',
                'flags': ['optional'],
            }
        ]

    def commander_execute(self, msg, flags):
        # Open the batch palette
        lx.eval('layout.createOrClose cookie:{renderMonkeyBatch} layout:{Monkey Batch} title:{renderMonkey Batch} width:720 height:300 persistent:1 style:palette open:?')

        # Try to get the path from the command line:
        path_list = self.commander_arg_value(0, '')
        path_list = None if path_list == '' else path_list.split(';')

        if path_list is None:
            initial_path = None if self.__class__._path_list is None or len(self.__class__._path_list) == 0 else self.__class__._path_list[0]
            path_list = monkey.io.lxo_open_dialog(initial_path)
            if path_list is None:
                return
            
            if not isinstance(path_list, list):
                path_list = [path_list]
                
            self.__class__._path_list = path_list

        batch = monkey.Batch()
        for path in path_list:
            batch.add_task(path)
            batch.unsaved_changed = True
        
        batch.rebuild_view()
        notifier = monkey.Notifier()
        notifier.Notify(lx.symbol.fCMDNOTIFY_CHANGE_ALL)        
        
    def basic_Enable(self, msg):
        return True

lx.bless(BatchAddTaskCommand, "monkey.BatchAddTask")