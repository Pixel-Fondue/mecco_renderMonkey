#python

import lx, os, json, modo, defaults, traceback, re, sys, yaml

from time import sleep
from math import copysign

DEBUG = True


def debug(string):
    """
    By Adam O'Hern for Mechanical Color
    
    Prints a string to lx.out() if defaults.get('debug') returns True. (See defaults.py)
    """
    if defaults.get('debug'):
        lx.out(string)
        if defaults.get('annoy'):
            if modo.dialogs.okCancel("debug",string) == 'cancel':
                sys.exit()
            
    
    
def setFrames(first,last):
    """
    By Adam O'Hern for Mechanical Color
    
    Sets
    """
    
    scene = modo.Scene()
    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).set(first)
    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).set(last)   
    
    
def get_scene_render_range():
    """
    By Adam O'Hern for Mechanical Color
    
    Sets
    """
    
    scene = modo.Scene()
    start = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).get()
    end = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).get()
    
    return "%s-%s" % (start,end)
    
def toConsole(state):
    """
    By Adam O'Hern for Mechanical Color
    
    Enables or disables console logging. Useful for render monitoring.
    """
    
    pass
#    debug('log.toConsole %s' % str(state))
#    lx.eval('log.toConsole %s' % str(state))
#    lx.eval('log.toConsoleRolling %s' % str(state))
    
    
def read_json(file_path):
    """
    By Adam O'Hern for Mechanical Color
    
    Returns a Python object (list or dict, as appropriate) from a given JSON file path.
    """
    
    debug('Reading file: %s' % file_path)
    try:
        json_file = open(file_path,'r')
        debug("...success.")
    except:
        debug("...failed.")
        debug(traceback.format_exc())
        return False
        
    debug('Parsing JSON for %s' % os.path.basename(file_path))
    try:
        json_object = json.loads(json_file.read())
        debug("...success.")
    except:
        debug("...failed.")
        debug(traceback.format_exc())
        
        debug('Closing %s.' % os.path.basename(file_path))
        json_file.close()
        return False

    debug('Closing %s.' % os.path.basename(file_path))
    json_file.close()
    return json_object    
    
def read_yaml(file_path):
    """
    By Adam O'Hern for Mechanical Color
    
    Returns a Python object (list or dict, as appropriate) from a given YAML file path.
    We use YAML because it's easier and more human readable than JSON. It's harder to mess up,
    easier to learn, and--imagine!--it supports commenting.
    """
    
    debug('Reading file: %s' % file_path)
    try:
        yaml_file = open(file_path,'r')
        debug("...success.")
    except:
        debug("...failed.")
        debug(traceback.format_exc())
        return False
        
    debug('Parsing YAML for %s' % os.path.basename(file_path))
    try:
        yaml_object = yaml.safe_load(yaml_file.read())
        debug("...success.")
    except:
        debug("...failed.")
        debug(traceback.format_exc())
        
        debug('Closing %s.' % os.path.basename(file_path))
        yaml_file.close()
        return False

    debug('Closing %s.' % os.path.basename(file_path))
    yaml_file.close()
    return yaml_object

def write_yaml(data,output_path):
    debug("Writing YAML to '%s'." % output_path)
    try:
        target = open(output_path,'w')
        target.write(yaml.dump(data, indent=4,width=999,default_flow_style = False).replace("\n-","\n\n-"))
        target.close()
        debug("...success.")
        return True
    except:
        debug("...failed. Return False." % output_path)
        return False


def get_imagesaver(key):
    """
    By Adam O'Hern for Mechanical Color
    
    Returns a tuple with three elements: name, username, and file extension.
    """
    
    debug('Looking for imagesaver "%s"' % key)
    
    savers = get_imagesavers()
    debug("Available image savers:\n%s" % "\n".join(["%s: %s (%s)" % (str(i[0]),str(i[1]),str(i[2])) for i in savers]))
        
    match = None
    for i in savers:
        if str(i[0]).lower() == key.lower():
            match = i
            break

    if match:
        debug('...found %s (%s)' % (i[1],i[2]))
    else:
        debug('...not found.')
        
    return match


def get_imagesavers():
    """ 
    By The Foundry
    http://sdk.luxology.com/wiki/Snippet:Image_Savers
    
    Returns a list of available image savers. Each entry in the returned list
       is a tuple made up of the format's internal name, it's username and it's
       DOS type (extension).
    """
    host_svc = lx.service.Host()
    savers = []
    for x in range(host_svc.NumServers('saver')):
        saver = host_svc.ServerByIndex('saver', x)
        out_class = saver.InfoTag(lx.symbol.sSAV_OUTCLASS)
        if  (out_class == 'image' or out_class == 'layeredimage'):
            name = saver.Name()
            uname = saver.UserName()
            try:
                dostype = saver.InfoTag(lx.symbol.sSAV_DOSTYPE)
            except:
                dostype = ''
            savers.append((name, uname, dostype,))
    return savers


def expand_path(inputString):
    """
    By Adam O'Hern for Mechanical Color
    
    Returns a normalized absolute path with trailing slash based on an input string.
    
    Examples:
    "/path/with/file.xyz"               becomes     "/path/with/file.xyz"
    "/path/with/no_trailing_slash"      becomes     "/path/with/no_trailing_slash/"
    "/already/perfectly/good/path/"     becomes     "/already/perfectly/good/path/"
    "frames/"                           becomes     "/path/to/scene/file/frames/"
    "./frames/"                         becomes     "/path/to/scene/file/frames/"
    "~/fruit/loops/"                    becomes     "/path/to/user/home/fruit/loops/"
    "pathalias:path/to/righteousness"   becomes     "/expanded/path/alias/path/to/righteousness/"
    
    NOTE: Parsing is rather primitive. If the string begins with "~", it assumes you're parsing a
    user folder. If it starts with ".", it assumes a relative path from the current scene. If it
    contains a ":" anywhere at all, it assumes a MODO path alias.
    """
    
    debug('Parsing path: %s' % inputString)
    inputString = os.path.normpath(inputString)
    
    
    if inputString.startswith(os.path.sep):
        full_path = inputString
        
    
    elif inputString.startswith('~'):
        try:
            full_path = os.path.expanduser(inputString)
        except:
            debug('Could not expand user folder. Path cannot be parsed.')
            return False
        
        
    elif ":" in inputString:
        try:
            full_path = lx.eval("query platformservice alias ? {%s}" % inputString)
        except:
            debug('Could not expand path alias. Path cannot be parsed.')
            return False
        
        
    else:
        try:
            current_scene_path = os.path.dirname(lx.eval('query sceneservice scene.file ? current'))
            debug('Scene path: %s' % current_scene_path)
        except:
            debug('Could not get current scene folder. Path cannot be parsed.')
            return False
        
        if inputString.startswith('.'):
            full_path = os.path.join(current_scene_path,inputString[1:])
        else:
            full_path = os.path.join(current_scene_path,inputString)
        
        
    if not os.path.splitext(full_path)[1]:
        debug('Adding trailing slash:')
        full_path = os.path.join(full_path,'')
        debug('...%s' % full_path)
        
    full_path = os.path.normpath(full_path)
    
    debug('Full path: %s' % full_path)
    return full_path


def range_from_string(inputString="*"):
    """
    By Simon Lundberg & Adam O'Hern for Mechanical Color
    
    function:
        parses a string on the form "1, 5, 10-20:2" into a range like this:
        [1, 5, 10, 12, 14, 16, 18, 20]
        Filters out illegal stuff to it won't break if you make typos.
        Filters out duplicate frames, so "1, 1, 1, 1-5" will only output
        [1, 2, 3, 4, 5], rather than [1, 1, 1, 1, 2, 3, 4, 5]
    syntax:
        Commas divide up each "chunk".
        If there is a dash ("-") in a chunk, it gets treated as a range of frames.
        If there is also a colon (":") in the chunk, that number indicates the frame step.

        In the case of two colons present, like this: "2:0-100:3", the last one
        will take prescedence (the range becomes 0-100 step 3, not step 2).

        In the case of a colon but no dash, like this: "3:5", the colon is ignored and
        only the first number is parsed.

        To get a negative frame step (rendering 1-100, starting at 100), simply enter
        the large number first and the lower number after, like this: "100-1". Negative
        frame steps are ignored.
    output:
        returns a LIST object with INTEGERS for each frame in the range, in the same order
        they were entered. Does NOT SORT. This is easy to do once it's a list anyway:
            sortedList = range_from_string(myRangeString).sort()
    """
    try:
        debug("Parsing render range: \"%s\"" % inputString)
        
        
        if inputString == "*":
            inputString = get_scene_render_range()
            debug("Using scene render range: \"%s\"" % inputString)
        
        #first we clean up the string, removing any illegal characters
        legalChars = "0123456789-:,"
        cleanString = ""
        frames = []
        
        debug("Removing illegal characters.")
        for char in inputString:
            if char in legalChars:
                cleanString += char
        debug("Clean string: %s" % cleanString)
        
        rangeStrings = re.findall(r"[-0123456789:]+", cleanString) #splits up by commas
        debug('Range strings:' + ', '.join(['"%s"' % i for i in rangeStrings]))
        
        debug('Parsing range strings.')
        for rangeString in rangeStrings:
            if "-" in rangeString[1:]:
                #is a sequence, so we need to parse it into a range

                #split up into start/end frames
                matchObject = re.search('\d-', rangeString)
                if matchObject:
                    splitIndex = matchObject.start()+1
                start, end = rangeString[:splitIndex], rangeString[splitIndex+1:]
                step = 1 #default value, can get overwritten by next two IF statements
                if ":" in start:
                    #check if there is a "step" setting
                    parts = start.split(":")
                    start = filter_numerical(parts[-1])
                    step = filter_numerical(parts[0])
                if ":" in end:
                    #check if there is a "step" setting
                    parts = end.split(":")
                    end = filter_numerical(parts[0])
                    step = filter_numerical(parts[-1])
                try:
                    start = int(start)
                    end = int(end)
                    step = int(step)
                except ValueError:
                    parse_error(rangeString)
                    break #no recognizable sequence data here, so we skip this one

                step = max(abs(step), 1) #make sure that step isn't negative or zero

                if start>end:
                    step *= -1
                    sign = int(copysign(1, step))
                    first = max(start, end)
                    last = min(start, end)+sign
                else:
                    sign = int(copysign(1, step))
                    first = min(start, end)
                    last = max(start, end)+sign
                try:
                    thisRange = range(first, last, step)
                    frames.extend(thisRange)
                except:
                    parse_error(rangeString) #skip this one


            else:
                #is a single frame; clean up, turn to an integer and append to list
                cleaned = re.split(r"\D", rangeString)
                try:
                    thisFrame = int(cleaned[0])
                    frames.append(thisFrame)
                except:
                    parse_error(rangeString) #skip this one

        debug('...finished parsing range strings.')

        #we now have our list of frames, but it's full of duplicates
        #let's filter the list so each frame exists only once
        debug('Filtering unique frames.')
        frames = filter_uniques(frames)

        #All done! If frames, return frames, otherwise exit with error
        if frames:
            debug('Returning: %s' % str(frames))
            return frames
        else:
            parse_error(inputString)
            return
    except:
        debug(traceback.format_exc())
        
        
def filter_uniques(seq):
    """
    By Simon Lundberg for Mechanical Color
    
    removes duplicates from input iterable
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def filter_numerical(input):
    """   
    By Simon Lundberg for Mechanical Color
    
    removes any non-numerical characters
    keeps dashes and periods for negatives
    and floating point numbers
    """
    numbers = "0123456789.-"
    if input:
        return "".join([c for c in input if c in numbers])
    else:
        return None
    
    
def parse_error(rangeString):
    """
    By Simon Lundberg for Mechanical Color
    
    outputs error message if parsing failed
    """
    debug('No recognizable sequence info in "%s".' % rangeString)
    
    
def get_user_value(name):
    """
    By Simon Lundberg for Mechanical Color
    
    returns a user value
    returns None if value does not exist
    """
    try:
        exists = lx.eval("!query scriptsysservice userValue.isDefined ? {%s}" % name)
        if not exists or exists == "0":
            #user value does not exist; create it with default value
            return None
        else:
            #user value exists; return value
            value = lx.eval("!user.value {%s} ?" % name)
            return value
    except:
        exclog("function \"getUserName(%s)\"" % name)
        return None


def check_output_paths():
    """    
    By Simon Lundberg for Mechanical Color
    
    utility function
    returns True if there is at least one render output that is:
       Enabled, has an output path, an output format, and all its parents
       are enabled as well, and the top-level parent is the Render item
    """

    n_renderOutputs = lx.eval("query sceneservice renderOutput.n ?")
    outputs = [lx.eval("query sceneservice renderOutput.id ? {%s}" % n) for n
                in range(n_renderOutputs)]
    for output in outputs:
        outputPath = lx.eval("item.channel filename ? item:{%s}" % output)
        outputFormat = lx.eval("item.channel format ? item:{%s}" % output)
        outputEnable = check_enable(output)
        if all((outputPath, outputFormat, outputEnable)):
            return True
    return False


def check_enable(texture):
    """    
    By Simon Lundberg for Mechanical Color
    
    iterates through shader tree parents of item "texture"
    returns True if all shader tree parents are enabled; otherwise False
    uses recursion to work its way through hierarchy
    """

    enable = lx.eval("item.channel enable ? item:{%s}" % texture)
    if enable:
        thisParent = lx.eval("query sceneservice item.parent ? {%s}" % texture)
        thisParent_type = lx.eval("query sceneservice item.type ? {%s}" % thisParent)
        if thisParent_type == "polyRender":
            return True
        elif thisParent_type == "scene":
            return False
        else:
            return check_enable(thisParent)
    else:
        return False


def set_or_create_user_value(name, value, valueType="string", life="config", username=None):
    """    
    By Simon Lundberg for Mechanical Color
    
    sets a user value
    if user value does not exist, it creates it first
    """
    try:
        #first we try to just set the value
        #if it fails, it's probably because it does not exist
        lx.eval("!user.value {%s} {%s}" % (name, value))
        if username:
            lx.eval("!user.def name:{%s} attr:username value:{%s}" % (name, username))
    except:
        #it failed; probably does not exist
        #we try to create it and set it instead
        try:
            lx.eval("!user.defNew {%s} {%s} {%s}" % (name, valueType, life))
            lx.eval("!user.value {%s} {%s}" % (name, value))
        except:
            lx.out("Error creating user value:", name, valueType, life)
            exclog()
            return


def create_master_pass_group(groups,delimeter="_x_"):
    """
    By Adam O'Hern for Mechanical Color
    
    Creates a pass group by multiplying any number of existing pass groups by each other.
    For example, you may have one pass group containing color variations, and another containing
    camera angles. This function could combine them such that the resulting pass group contains 
    every camera angle for every color variation.
    """
    
    scene = modo.Scene()
    
    channels = set()
    for group in groups:
        for channel in group.groupChannels:
            channels.add(channel)
        for action in group.itemGraph('itemGroups').forward():
            action.actionClip.SetActive(0)

    master_group = scene.addGroup(delimeter.join([g.name for g in groups]),'render')

    for channel in channels:
        master_group.addChannel(channel)

    combine(master_group,groups,channels,len(groups)) 
    
    return master_group
    
        
def combine(master_group,groups,channels,max_depth,depth=0,passname_parts=[],delimeter="_"):
    """
    By Adam O'Hern for Mechanical Color
    
    Recursively walks a list of render pass groups to create every possible combination. Intended for use with
    create_master_pass_group() function.
    """
    if depth < max_depth:
        passes = groups[0].itemGraph('itemGroups').forward()
        
        for p in passes:
            if p.actionClip.Enabled():
                p.actionClip.SetActive(1)

                subgroups = [g for g in groups]
                del subgroups[0]

                combine(master_group,subgroups,channels,max_depth,depth+1,passname_parts+[p.name])
    
    elif depth == max_depth:
        lx.eval('group.layer group:{%s} name:{%s} transfer:false grpType:pass' % (master_group.name,delimeter.join(passname_parts)))
        for c in channels:
            lx.eval('channel.key channel:{%s:%s}' % (c.item.id,c.name))
            lx.eval('channel.key mode:remove channel:{%s:%s}' % (c.item.id,c.name))
        lx.eval('edit.apply')
        lx.eval('layer.active active:off')
    
    

def build_arg_string(arg_dict):
    arg_string = ''
    for k,v in arg_dict.iteritems():
        if v is not None:
            v = str(v) if str(v).isalnum() else '{%s}' % str(v)
            arg_string += " %s:%s" % (str(k),v)
    return arg_string


        
def render_frame(frame, useOutput=True, outputPath=None, outputFormat=None, clear=False, group=None):
    """    
    By Simon Lundberg for Mechanical Color
    
    renders a specific frame
    
    frame:          Integer to choose frame
    useOutput:      Boolean for using output controls from render outputs
    outputPath:     String for output if useOutput is False
    outputFormat:   String for output format if useOutput is False
    clear:          Boolean, if True it will clear render on finish
    
    NOTE: returns False if user aborted frame or if there is some error
          in the render process.
          returns True if frame completes without error.
    """

    renderItem = modo.Scene().renderItem.id
    #start by reading previous values
    first = lx.eval("item.channel first ? item:{%s}" % renderItem)
    last = lx.eval("item.channel last ? item:{%s}" % renderItem)

    #then we set a single frame as the new range
    lx.eval("item.channel first %s item:{%s}" % (frame, renderItem))
    lx.eval("item.channel last %s item:{%s}" % (frame, renderItem))

    #then we figure out whether to use a render pass group or not
    if group:
        group = "group:{%s}" % group
    else:
        group = ""

    #then we render the current frame
    try:
        if useOutput:
            lx.eval("render.animation * * %s" % group)
        else:
            lx.eval("render.animation {%s} %s %s" % (outputPath, outputFormat, group))
    except:
        #error most likely because user aborted
        #restore frame range, and exit script
        lx.eval("item.channel first %s item:{%s}" % (first, renderItem))
        lx.eval("item.channel last %s item:{%s}" % (last, renderItem))
        lx.out("User aborted")
        return False #rendering failed, so we return False


    #if we complete the render, we restore the original frame range
    lx.eval("item.channel first %s item:{%s}" % (first, renderItem))
    lx.eval("item.channel last %s item:{%s}" % (last, renderItem))
    sleep(0.1)
    if clear:
        lx.eval("!render.clear")
    return True #rendering succeeded, so we return True




def render_range(frames, group=None):
    """
    By Simon Lundberg for Mechanical Color
    
    takes a list of ints as an argument
    renders all frames in list
    """
    #progress bars are disabled for now
    progressbarEnable = False

    #first we need to see if we have an output path in the render outputs:
    usePaths = False
    if check_output_paths():
        if modo.dialogs.yesNo("Save Image Sequence",'Use the filenames specified in the render outputs?' % group_name):
            usePaths = True

    if not usePaths:
        #because usePaths is False, we must ask user for a file location
        try:
            #first we try to get previous values, and use defaults if that fails...
            try:
                #try user value
                previousPath = lx.eval("!user.value mecco_renderPath ?")
            except:
                #No user value for previous path existed
                previousPath = lx.eval("query platformservice path.path ? project")
                if not previousPath:
                    #no project path, so we use scene path instead
                    scenePath = lx.eval("query sceneservice scene.file ? scene001")
                    if scenePath:
                        previousPath = scenePath.rsplit(os.path.sep, 1)[0]
                if not previousPath:
                    #no content path either, so we use user home directory
                    previousPath = os.path.expanduser("~")
                previousPath += os.path.sep
            try:
                #try user value
                previousFormat = lx.eval("!user.value mecco_renderFormat ?")
            except:
                #No user value for previous format existed, default to 16-bit OpenEXR
                previousFormat = "openexr"


            #setting up dialog...
            lx.eval("dialog.setup fileSave")
            lx.eval("dialog.result {%s}" % previousPath)
            lx.eval("dialog.fileType image")
            lx.eval("dialog.fileSaveFormat {%s} format" % previousFormat)
            lx.eval("dialog.open")

            #getting results...
            filePath = lx.eval("dialog.result ?")
            fileFormat = lx.eval("dialog.fileSaveFormat ? format")
            fileExtension = lx.eval("dialog.fileSaveFormat ? extension")
            filePath = filePath.rsplit(".", 1)[0]

            #store output options in a user value...
            dirPath = filePath.rsplit(os.path.sep, 1)[0] + os.path.sep
            set_or_create_user_value("mecco_renderPath", dirPath)
            set_or_create_user_value("mecco_renderFormat", fileFormat)

        except:
            #error probably because user pressed "cancel"
            lx.out("User aborted")
            return
    else:
        #usePaths is True, so we don't need to get any file paths or anything
        pass

    lx.out("Rendering frames:")
    lx.out(frames)

    if progressbarEnable:
        progressbar = lx.Monitor(len(frames))
        progressbar.init(len(frames))
    for frame in frames:
        if frame == frames[-1]:
            clearFrame = False
        else:
            clearFrame = True
        if usePaths:
            if not render_frame(frame, clear=clearFrame, group=group):
                break
                #slight strange syntax to safely catch aborted frames
        else:
            if not render_frame(frame, False, filePath, fileFormat, clearFrame, group=group):
                break
        sleep(0.5)
        if progressbarEnable:
            progressbar.step(1)