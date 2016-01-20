#python

import lx, os, json, modo, defaults, traceback, re, sys, yaml, random

from symbols import *
from os.path import basename
from time import sleep
from math import copysign


def debug(string):
    """
    By Adam O'Hern for Mechanical Color

    Prints a string to lx.out() if defaults.get('debug') returns True. (See defaults.py)
    Intended for developer debugging only; user messages should use 'status'.
    """
    if defaults.get('debug'):
        t = traceback.extract_stack()[-2]
        lx.out("debug '%s' line %s, %s(): %s" % (basename(t[0]), t[1], t[2], string))

def breakpoint(string):
    """
    By Adam O'Hern for Mechanical Color

    Essentially a breakpoint function for debugging purposes.
    Prints a string to lx.out() and, if defaults.get('breakpoint') returns True, throws a dialog as well. (See defaults.py)
    """
    t = traceback.extract_stack()[-2]
    string = "'%s' line %s, %s(): %s" % (basename(t[0]), t[1], t[2], string)

    if defaults.get('breakpoints'):
        lx.out("breakpoint: %s" % string)
        if defaults.get('breakpoints'):
            if modo.dialogs.okCancel("breakpoint",string) == 'cancel':
                sys.exit()

def status(string):
    """
    By Adam O'Hern for Mechanical Color

    Prints a string to lx.out(). Differs from "debug" only in that it's always enabled. Useful for user-related messages.
    """

    lx.out("status: %s" % string)

def batch_status_file(batch_file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns the correct path for a batch file's status sidecar file.
    """
    split = os.path.splitext(batch_file_path)
    return "%s_%s%s" % (split[0],STATUS_FILE_SUFFIX,split[1])

def batch_status_create(data,batch_file_path):
    """
    By Adam O'Hern for Mechanical Color

    Creates a sidecar file to monitor batch progress if none exists.
    """
    if not os.path.isfile(batch_status_file(batch_file_path)):
        status_file = open(batch_status_file(batch_file_path),'w')
        status_file.write(yamlize(data))
        status_file.close()

def batch_has_status(batch_file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns True if the supplied batch list contains any status markers.
    """
    if os.path.isfile(batch_status_file(batch_file_path)):
        return True

    return False

def batch_status_reset(batch_file_path):
    """
    By Adam O'Hern for Mechanical Color

    Resets all status markers on a partially finished batch.
    """
    try:
        status_file = open(batch_status_file(batch_file_path),'w')
    except:
        debug(traceback.format_exc())
        return False

    data = read_yaml(batch_file_path)

    try:
        status_file.write(yaml.dump(data, indent=4,width=999,default_flow_style = False).replace("\n-","\n\n-"))
    except:
        debug(traceback.format_exc())
        status_file.close()
        return False

    status_file.close()
    return True

def test_writeable(test_dir_path):
    """
    By Adam O'Hern for Mechanical Color

    Easier to ask forgiveness than permission.
    If the test path doesn't exist, tries to create it. If it can't, returns False.
    Then writes to a file in the target directory. If it can't, returns False.
    If all is well, returns True.
    """

    if not os.path.exists(test_dir_path):
        try:
            os.mkdir(test_dir_path)
        except OSError:
            return False

    test_path = os.path.join(test_dir_path,"tmp_%s.txt" % random.randint(100000,999999))
    try:
        test = open(test_path,'w')
        test.write("Testing write permissions.")
        test.close()
        os.remove(test_path)
        return True
    except:
        return False


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

    debug('log.toConsole %s' % str(state))
    lx.eval('log.toConsole %s' % str(state))
    lx.eval('log.toConsoleRolling %s' % str(state))

def yaml_save_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting YAML file destination.
    """

    try:
        return os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileSave',
                title='Save Batch File Template',
                names=['yaml'],
                unames=['Batch File (YAML)'],
                patterns=['*.yaml'],
                ext=['yaml']
            )
        )
    except:
        return False

def lxo_open_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting LXO file source.
    """

    try:
        path = os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileOpen',
                title='Select Scene File',
                names=('lxo',),
                unames=('MODO Scene file',),
                patterns=('*.lxo',),
                path=None
            )
        )

        return path

    except:
        return False

def yaml_open_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting YAML file source.
    """

    try:
        path = os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileOpen',
                title='Select Batch File',
                names=('yaml',),
                unames=('renderMonkey Batch File',),
                patterns=('*.yaml',),
                path=None
            )
        )

        return path

    except:
        return False

def yaml_save_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting YAML file source.
    """

    try:
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

        return output_path

    except:
        return False

def read_json(file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns a Python object (list or dict, as appropriate) from a given JSON file path.
    """

    try:
        json_file = open(file_path,'r')
    except:
        debug(traceback.format_exc())
        return False

    try:
        json_object = json.loads(json_file.read())
    except:
        debug(traceback.format_exc())
        json_file.close()
        return False

    json_file.close()
    return json_object


def read_yaml(file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns a Python object (list or dict, as appropriate) from a given YAML file path.
    We use YAML because it's easier and more human readable than JSON. It's harder to mess up,
    easier to learn, and--imagine!--it supports commenting.

    Note: YAML does not support hard tabs (\t), so this script replaces those with four spaces ('    ').
    """

    try:
        yaml_file = open(file_path,'r')
    except:
        debug(traceback.format_exc())
        return False

    try:
        yaml_object = yaml.safe_load(re.sub('\\t','    ',yaml_file.read()))
    except:
        debug(traceback.format_exc())
        yaml_file.close()
        return False

    yaml_file.close()
    return yaml_object

def yamlize(data):
    return yaml.dump(data, indent=4,width=999,default_flow_style = False).replace("\n-","\n\n-")

def write_yaml(data,output_path):
    try:
        target = open(output_path,'w')
        target.write(yamlize(data))
        target.close()
        return True
    except:
        return False


def get_imagesaver(key):
    """
    By Adam O'Hern for Mechanical Color

    Returns a tuple with three elements: name, username, and file extension.
    """

    savers = get_imagesavers()

    match = None
    for i in savers:
        if str(i[0]).lower() == key.lower():
            match = i
            break

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

    inputString = os.path.normpath(inputString)


    if inputString.startswith(os.path.sep):
        full_path = inputString


    elif inputString.startswith('~'):
        try:
            full_path = os.path.expanduser(inputString)
        except:
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
        except:
            debug('Could not get current scene folder. Path cannot be parsed.')
            return False

        if inputString.startswith('.'):
            full_path = os.path.join(current_scene_path,inputString[1:])
        else:
            full_path = os.path.join(current_scene_path,inputString)


    if not os.path.splitext(full_path)[1]:
        full_path = os.path.join(full_path,'')

    full_path = os.path.normpath(full_path)
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
        if inputString == "*":
            inputString = get_scene_render_range()

        #first we clean up the string, removing any illegal characters
        legalChars = "0123456789-:,"
        cleanString = ""
        frames = []

        for char in inputString:
            if char in legalChars:
                cleanString += char

        rangeStrings = re.findall(r"[-0123456789:]+", cleanString) #splits up by commas

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


        #we now have our list of frames, but it's full of duplicates
        #let's filter the list so each frame exists only once
        frames = filter_uniques(frames)

        #All done! If frames, return frames, otherwise exit with error
        if frames:
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
        lx.eval("!user.value {%s} {%s}" % (name, value))
        if username:
            lx.eval("!user.def name:{%s} attr:username value:{%s}" % (name, username))
    except:
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
        for action in [i for i in groups[0].itemGraph('itemGroups').forward() if i.type == lx.symbol.a_ACTIONCLIP]:
            action.actionClip.SetActive(0)

    master_group = scene.addGroup(delimeter.join([g.name for g in groups]),'render')

    for channel in channels:
        master_group.addChannel(channel)

    combine(master_group,groups,channels,len(groups))

    return master_group


def set_task_status(batch_file_path,task_index,status):
    batch_file_path = batch_status_file(batch_file_path)
    batch = read_yaml(batch_file_path)

    if not batch:
        return False

    try:
        if STATUS not in batch[task_index] or not isinstance(batch[task_index][STATUS],list):
            batch[task_index][STATUS] = []

        batch[task_index][STATUS] = [i for i in batch[task_index][STATUS] if not i.startswith(TASK)]
        batch[task_index][STATUS].append("%s %s" % (TASK,status))

        write_yaml(batch,batch_file_path)
        return True
    except:
        status("Problem writing task status to batch file.")
        return False

def get_task_status(batch_file_path,task_index):
    batch_file_path = batch_status_file(batch_file_path)
    batch = read_yaml(batch_file_path)

    if not batch:
        return STATUS_AVAILABLE

    if STATUS in batch[task_index]:
        for i in batch[task_index][STATUS]:
            if i.startswith(TASK) and not STATUS_AVAILABLE in i:
                return i

    return STATUS_AVAILABLE

def set_frame_status(batch_file_path,task_index,frame_number,status):
    batch_file_path = batch_status_file(batch_file_path)
    batch = read_yaml(batch_file_path)

    if not batch:
        return False

    try:
        if STATUS not in batch[task_index] or not isinstance(batch[task_index][STATUS],list):
            batch[task_index][STATUS] = []

        batch[task_index][STATUS] = [i for i in batch[task_index][STATUS] if not int(re.search('^[0-9]*',i).group(0)) == frame_number]
        batch[task_index][STATUS].append("%04d %s" % (frame_number,status))

        write_yaml(batch,batch_file_path)
        return True
    except:
        status("Problem writing frame status to batch file.")
        return False

def get_frame_status(batch_file_path,task_index,frame_number):
    batch_file_path = batch_status_file(batch_file_path)
    batch = read_yaml(batch_file_path)

    if not batch:
        return STATUS_AVAILABLE

    if STATUS in batch[task_index]:
        for i in batch[task_index][STATUS]:
            if int(re.search('^[0-9]*',i).group(0)) == frame_number and not STATUS_AVAILABLE in i:
                return i

    return STATUS_AVAILABLE

def combine(master_group,groups,channels,max_depth,depth=0,passname_parts=[],delimeter="_"):
    """
    By Adam O'Hern for Mechanical Color

    Recursively walks a list of render pass groups to create every possible combination, excluding disabled passes.
    Intended for use with create_master_pass_group() function.
    """
    if not isinstance(groups,list) and not isinstance(groups,set):
        groups = [groups]

    if depth < max_depth:
        passes = [i for i in groups[0].itemGraph('itemGroups').forward() if i.type == lx.symbol.a_ACTIONCLIP]

        for p in passes:
            if p.actionClip.Enabled():
                p.actionClip.SetActive(1)

                subgroups = [g for g in groups]
                del subgroups[0]

                combine(master_group,subgroups,channels,max_depth,depth+1,passname_parts+[p.name])

    elif depth == max_depth:
        layer_name = delimeter.join(passname_parts)
        lx.eval('group.layer group:{%s} name:{%s} transfer:false grpType:pass' % (master_group.name,layer_name))
        for c in channels:
            try:
                #Set channel to its current value; sets channel to 'edit' layer for absorption into the new pass.
                c.set(c.get())
            except:
                debug('Something went wrong setting channel "" to "".' % (c.name,c.get()))
        lx.eval('edit.apply')



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
