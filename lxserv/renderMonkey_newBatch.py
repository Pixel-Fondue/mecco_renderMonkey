#python

# By Adam O'Hern for Mechanical Color LLC

import monkey, modo, lx, lxu, traceback, os, yaml

CMD_NAME = 'monkey.newBatch'
    
class CMD(lxu.command.BasicCommand):
    
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.startPath = None
    
    def basic_Execute(self, msg, flags):
        try:
            tree = []
            
            output_path = os.path.normpath(
                modo.dialogs.customFile(
                    dtype='fileSave', 
                    title='Save Batch File Template',
                    names=['yaml'],
                    unames=['Batch File (YAML)'],
                    patterns=['*.yaml'],
                    ext=['yaml']
                )
            )
            
            target = open(output_path,'w')
            target.write(yaml.dump(tree, indent=4,width=999,default_flow_style = False).replace("\n-","\n\n-"))
            target.close()
                
        except Exception:
            monkey.util.debug(traceback.format_exc())
    
    
lx.bless(CMD, CMD_NAME)