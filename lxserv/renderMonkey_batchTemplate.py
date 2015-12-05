#python

# By Adam O'Hern for Mechanical Color LLC

import monkey, modo, lx, lxu, traceback, os, json, yaml

CMD_NAME = 'renderMonkey.batchTemplate'

PATH = monkey.symbols.SCENE_PATH
FORMAT = monkey.symbols.FORMAT
FRAMES = monkey.symbols.FRAMES
DESTINATION = monkey.symbols.DESTINATION
PATTERN = monkey.symbols.PATTERN
GROUPS = monkey.symbols.GROUPS

    
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
                }
            ]
            
            output_path = os.path.normpath(
                modo.dialogs.customFile(
                    dtype='fileSave', 
                    title='Save Batch File Template',
                    names=['json'],
                    unames=['Batch File'],
                    patterns=['*.json'],
                    ext=['json']
                )
            )
            
            target = open(output_path,'w')
            target.write(json.dumps(tree, sort_keys=False, indent=4, separators=(',', ': ')))
            target.close()
            
            
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
            
            readme = """Only 'path' is required. All other parameters are optional, see default values below.

*path* - (required) Should contain a valid OS path to a MODO scene file. 

*format* - (default: "*") Defaults to render output setting or, if none available, 16-bit EXR. Allows any of the following:
"""
            
            readme += "\n".join(["    %s: %s (*.%s)" % (i[0],i[1],i[2]) for i in monkey.util.get_imagesavers()]) + "\n\n"
            readme += """*frames* - (default: *) A comma-delimited list of frame ranges in the format "start-end:step". Examples:
    "*" : [As defined in file.]         << Use frame frange defined in 'start' and 'end' render channels.
    "1" : [1]                           << Single frame
    "1-5" : [1,2,3,4,5]                 << Frame sequence rendered in order.
    "5-1" : [5,4,3,2,1]                 << Frames rendered in reverse order.
    "0-10:2" : [0,2,4,6,8,10]           << Frames between zero and ten by twos.
    "1-21:5" : [1,6,11,16,21]           << Frames between one and twenty-one by fives.
    "1,1-5" : [1,2,3,4,5]               << Redundant frames will only be rendered once.
    "(1 - 3),, 4-!@#5" : [1,2,3,4,5]    << Extra characters are stripped.

*width* - (default: scene) Frame width in pixels. If a width is supplied but no height--or vise verse--the scene aspect ratio will be maintained.

*height* - (default: scene) Frame height in pixels. If a width is supplied but no height--or vise verse--the scene aspect ratio will be maintained.

*outputs* - (default: scene) List of render outputs to save, by name or id. If none are provided, all available render outputs will be rendered as per scene settings.

*destination* - (default: "./frames/") Where to save the rendered frames. Examples:
    "/already/perfectly/good/path/"     becomes     "/already/perfectly/good/path/"
    "/path/with/file.xyz"               becomes     "/path/with/file.jpg" (extension ignored, will use format extension)
    "/path/with/no_trailing_slash"      becomes     "/path/with/no_trailing_slash/"
    "frames/"                           becomes     "/path/to/scene/file/frames/"
    "./frames/"                         becomes     "/path/to/scene/file/frames/"
    "~/fruit/loops/"                    becomes     "/path/to/user/home/fruit/loops/"
    "pathalias:path/to/righteousness"   becomes     "/expanded/path/alias/path/to/righteousness/"
    
    Path aliases are useful for cross-platform LAN-based rendering, where drives cannot always be mapped to a common
    system path between machines. These can be defined in MODO's preferences or programatically via kits or configs. See
    MODO documentation.
    
*suffix* - (default: *) Sets the output pattern for file naming. Defaults to the scene file setting. For syntax, see
    Output Patterns in MODO documentation.

*passgroups* - (default: None) Pass groups to render for each frame. If a list of groups is provided, it will multiply
    each successive group by the former. For example, ['group1','group2'] renders each pass of group2 for each pass of group1.
    This is useful for pass groups containing orthogonal information, e.g. ['variations','views'] renders each view for each
    variation.
"""
            
            target = open(os.path.splitext(output_path)[0]+"_readme.md",'w')
            target.write(readme)
            target.close()
                
        except Exception:
            monkey.util.debug(traceback.format_exc())
    
    
lx.bless(CMD, CMD_NAME)