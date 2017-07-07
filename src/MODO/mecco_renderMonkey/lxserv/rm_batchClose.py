# python

import lx, monkey, os, modo
from monkey import message as message

class BatchCloseCommand(monkey.commander.CommanderClass):

    def commander_arguments(self):
        return [
            {
                'name': 'prompt_save',
                'datatype': 'boolean',
                'flags': ['optional']
            }
        ]

    def commander_execute(self, msg, flags):
        prompt_save = self.commander_arg_value(0, True)

        batch = monkey.Batch()

        # If content is not empty ask user for save
        if prompt_save and batch.unsaved_changes and not batch.is_empty:
            file_path = batch.batch_file_path
            if file_path is None:
                file_path = "Untitled"
            if modo.dialogs.yesNo(message("MECCO_RM", "ASK_FOR_SAVE_DIALOG_TITLE"), message("MECCO_RM", "ASK_FOR_SAVE_DIALOG_MSG")) == 'yes':
                # If file path is not assigned ask for new file path
                if macro.file_path is None:
                    file_path = monkey.io.yaml_save_dialog()
                    if file_path is None:
                        return
                        
                batch.save_to_file(file_path)
             
        # Rebuild the tree
        try:
            batch.close_file()
            batch.unsaved_changed = False
        except Exception as err:
            modo.dialogs.alert(message("MECCO_RM", "CLOSE_FILE_FAIL"), message("MECCO_RM", "CLOSE_FILE_FAIL_MSG", str(err)), dtype='warning')

        finally:
            batch.rebuild_view()
            notifier = monkey.Notifier()
            notifier.Notify(lx.symbol.fCMDNOTIFY_CHANGE_ALL)

    def basic_Enable(self, msg):
        return True

lx.bless(BatchCloseCommand, "monkey.BatchClose")
