#python

# By Adam O'Hern for Mechanical Color LLC

import monkey, modo, lx, lxu, traceback, os

CMD_NAME = 'renderMonkey.batch'

    
class CMD(lxu.command.BasicCommand):
    """mode:new|open|add|remove|claim|abort|run"""
    
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.startPath = None
        
        self.dyna_Add('mode', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)
        
    def die(self,e = lx.symbol.e_FAILED):
        toConsole(False)
        return e
    
    def last_path(self,new_path=None):
        if new_path:
            self.startPath = new_path
            return self.startPath
            
        if not self.startPath:
            if lx.eval('query sceneservice scene.file ? current'):
                self.startPath = lx.eval('query sceneservice scene.file ? current')
            else:
                self.startPath = os.path.expanduser("~")
        
        return self.startPath
    
    def basic_Execute(self, msg, flags):
        try:
            mode = self.dyna_String(0) if self.dyna_IsSet(0) else 'run'
            
            if mode == 'run':

                batch_file_path = os.path.normpath(modo.dialogs.customFile(dtype='fileOpen', title='Select Batch File',names=('yaml',),unames=('renderMonkey Batch File',), patterns=('*.yaml',), path=self.last_path()))
                self.last_path(os.path.dirname(batch_file_path))
                
                monkey.util.debug("Using batch file:\n%s" % batch_file_path)
                
                if batch_file_path:
                    return monkey.batch.run(batch_file_path)
                else:
                    return lx.symbol.e_FAILED
                
        except SystemExit:
            pass
        except:
            monkey.util.debug(traceback.format_exc())
    
    
lx.bless(CMD, CMD_NAME)