#python

# By Adam O'Hern for Mechanical Color LLC

import monkey, modo, lx, lxu, traceback, os

CMD_NAME = 'renderMonkey.batchTemplate'

    
class CMD(lxu.command.BasicCommand):
    
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.startPath = None
    
    def basic_Execute(self, msg, flags):
        try:
            tree = [
                {
                    "path":"~/Desktop/scene.lxo"
                },{
                    "path":"~/Desktop/scene1.lxo",
                    "format":"JPG",
                    "frames":"*",
                    "destination":"./frames/filename.x"
                    "passgroups":'passgroup1'
                },{
                    "path":"~/Desktop/scene2.lxo",
                    "format":"JPG",
                    "frames":"1-5",
                    "destination":"./frames/filename2.xyz"
                    "suffix":'[<pass>_][<output>_][<LR>_]<FFFF>'
                    "passgroups":['colorways','cameraAngles']
                }
            ]
            
            output_path = os.path.normpath(
                modo.dialogs.customFile(
                    dtype='fileSave', 
                    title='Save Batch File Template',
                    names=('json',),
                    unames=('Batch File',),
                    patterns=('*.json',),
                    os.path.expanduser("~")
                )
            )
            
            target = open(output_path,'w')
            target.write(json.dumps(tree, sort_keys=False, indent=4, separators=(',', ': ')))
            target.close()
            
            readme = 
            
"""
Only 'path' is required. All other parameters are optional, see default values below.

*path* - (required) Should contain a valid OS path to a MODO scene file. 

*format* - (default: *) Defaults to render output setting or, if none available, 16-bit EXR. Allows any of the following:
"""
            
            readme += ["    %s: %s (%s)\n" % (i[0],i[1],i[2]) for i in get_imagesavers()] + "\n"
            readme +=
            
"""
*frames* - (default: *) A comma-delimited list of frame ranges in the format "start-end:step". Examples:
    "*" : [As defined in file.]         << Use frame frange defined in 'start' and 'end' render channels.
    "1" : [1]
    "1-5" : [1,2,3,4,5]
    "5-1" : [5,4,3,2,1]                 << Frames rendered in the order expressed, not necessarily numerical order.
    "0-10:2" : [0,2,4,6,8,10]           << Frames between zero and ten by twos.
    "1-21:5" : [1,6,11,16,21]           << Frames between one and twenty-one by fives.
    "1,1-5" : [1,2,3,4,5]               << Redundant frames will only be rendered once.
    "(1 - 3),, 4-!@#5" : [1,2,3,4,5]    << Special and redundant characters are stripped.

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
                
        except Exception:
            monkey.util.debug(traceback.format_exc())
    
    
lx.bless(CMD, CMD_NAME)