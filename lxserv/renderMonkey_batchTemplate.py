#python

# By Adam O'Hern for Mechanical Color LLC

import monkey, modo, lx, lxu, traceback, os, yaml

CMD_NAME = 'renderMonkey.batchTemplate'

PATH = monkey.symbols.SCENE_PATH
FORMAT = monkey.symbols.FORMAT
FRAMES = monkey.symbols.FRAMES
DESTINATION = monkey.symbols.DESTINATION
PATTERN = monkey.symbols.PATTERN
GROUPS = monkey.symbols.GROUPS
WIDTH = monkey.symbols.WIDTH
HEIGHT = monkey.symbols.HEIGHT
OUTPUTS = monkey.symbols.OUTPUTS
CAMERA = monkey.symbols.CAMERA

    
class CMD(lxu.command.BasicCommand):
    
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.startPath = None
    
    def basic_Execute(self, msg, flags):
        try:
            tree = [
                {
                    PATH:monkey.defaults.get('test_path')
                },{
                    PATH:monkey.defaults.get('test_path'),
                    FORMAT:monkey.defaults.get('filetype'),
                    DESTINATION:monkey.defaults.get('test_output_path'),
                    GROUPS:monkey.defaults.get('test_passgroup')
                },{
                    PATH:monkey.defaults.get('test_path'),
                    FORMAT:monkey.defaults.get('filetype'),
                    FRAMES:monkey.defaults.get('test_framerange'),
                    DESTINATION:monkey.defaults.get('test_output_path'),
                    PATTERN:monkey.defaults.get('output_pattern'),
                    GROUPS:monkey.defaults.get('test_passgroups')
                    CAMERA:monkey.defaults.get('test_camera')
                }
            ]
            
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
            

            
            readme = "\n\n# Syntax is YAML (yaml.org), interpreted with pyYAML.\n"
            readme += "# A proper code editor is highly recommended for editing.\n"
            readme += "# Brackets (http://brackets.io) is free, cross-platform, and has built-in YAML support.\n\n"
            
            readme += "# Each list item is a render task.\n"
            readme += "# Only \"%s\" is required for a task to function. All other parameters are optional, see default values below.\n\n" % PATH

            readme += "###\n\n"
            
            readme += "# \"%s\" - (required) Should contain a valid OS path to a MODO scene file.\n\n" % PATH

            readme += "# \"%s\" - (default: *) Defaults to render output setting or, if none available, %s.\n" % (FORMAT,monkey.defaults.get('filetype'))
            readme += "#    Allows any of the following:\n\n"
            
            readme += "#" + "\n#".join(["    %s: %s (*.%s)" % (i[0],i[1],i[2]) for i in monkey.util.get_imagesavers()]) + "\n\n"
            
            readme += "# \"%s\" - (default: *) A comma-delimited list of frame ranges in the format 'start-end:step'.\n" % FRAMES
            readme += "#     Spaces and special characters are ignored, and redundant frames are only rendered once.\n"
            readme += "#     Examples:\n\n"
            
            readme += "#    '*'                       Start/end frames defined in scene file.\n"
            rr = ['1','1-5','5-1','0-10:2','1-21:5','1-3,10-16:2,20-23','1,1-5','(1 - 5),, 10-!@#15']
            readme += "#" + "\n#".join(["    '%s'%s%s" % (i," "*(24-len(i)),str(monkey.util.range_from_string(i))) for i in rr]) + "\n\n"

            readme += "# \"%s\" - (default: scene) Frame width in pixels.\n" % WIDTH
            readme += "#     If a width is supplied but no height--or vise verse--the scene aspect ratio will be maintained.\n\n"

            readme += "# \"%s\" - (default: scene) Frame height in pixels.\n" % HEIGHT
            readme += "#     If a width is supplied but no height--or vise verse--the scene aspect ratio will be maintained.\n\n"

            readme += "# \"%s\" - (default: scene) List of render outputs (by name or id) to save, by name or id.\n" % OUTPUTS
            readme += "#     If none are provided, all available render outputs will be rendered as per scene settings.\n\n"

            readme += "# \"%s\" - (default: scene) Camera (by name or id) to use for rendering.\n" % CAMERA
            readme += "#     If none is provided, the one defined in the scene will be used.\n\n"

            readme += "# \"%s\" - (default: %s) Where to save the rendered frames.\n" % (DESTINATION,monkey.defaults.get('destination'))
            readme += "#    NOTE: Parsing is rather primitive. If the string begins with \"~\", it assumes you're parsing a user folder.\n"
            readme += "#    If it starts with \".\" or lacks a leading slash, it assumes a relative path from the current scene.\n"
            readme += "#    If it contains a \":\" anywhere at all, it assumes a MODO path alias. (Search for 'path alias' in MODO docs.)\n"
            readme += "#    Using a file extension (e.g. 'filename.xyz') designates a file name, but the extension itself will be replaced as appropriate.\n"
            readme += "#    Examples:\n\n"
            
            indent = 32
            
            rr = [
                ['frames' + os.sep, os.path.normpath(os.sep + os.path.join('path','to','scene','file','frames'))],
                ['.frames' + os.sep, os.path.normpath(os.sep + os.path.join('path','to','scene','file','frames'))],
                [os.sep + os.path.join('path','with','filename.xyz'), os.path.normpath(os.sep + os.path.join('path','with','filename.jpg'))]
            ]
            readme += "#" + "\n#".join(["    %s%s%s" % (i[0]," "*(indent-len(i[0])),i[1]) for i in rr]) + "\n"

            rr = [
                os.sep + os.path.join('already','perfectly','good','path') + os.sep,
                os.sep + os.path.join('path','with','no','trailing_slash'),
                os.path.join('~','path','to','righteousness'),
                "kit_mecco_renderMonkey:path" + os.sep
            ]
            readme += "#" + "\n#".join(["    %s%s%s" % (i," "*(indent-len(i)),str(monkey.util.expand_path(i))) for i in rr]) + "\n\n"
    
            readme += "# \"%s\" - (default: *) Sets the output pattern for file naming. Defaults to the scene file setting.\n" % PATTERN
            readme += "#     Note that unlike other fields, output patterns must be wrapped in single quotes (').\n"
            readme += "#     For syntax, search for 'Output Pattern' in MODO docs and click the 'Render Item: Frame' link.\n\n"

            readme += "# \"%s\" - (default: None) Pass groups (by name or id) to render for each frame.\n" % GROUPS
            readme += "#     If a list of groups is provided, it will multiply each successive group by the former.\n"
            readme += "#     For example, ['group1','group2'] renders each pass of group2 for each pass of group1.\n"
            readme += "#     This is useful for pass groups containing orthogonal information,\n"
            readme += "#     e.g. ['variations','views'] renders each 'view' pass for each 'variation' pass.\n"
            
            target = open(output_path,'a')
            target.write(readme)
            target.close()
                
        except Exception:
            monkey.util.debug(traceback.format_exc())
    
    
lx.bless(CMD, CMD_NAME)