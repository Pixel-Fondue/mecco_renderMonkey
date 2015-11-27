#python

import lx, os, json, modo, defaults, traceback, re

DEBUG = True


def debug(string):
    """
    By Adam O'Hern for Mechanical Color LLC
    
    Prints a string to lx.out() if defaults.get('debug') returns True. (See defaults.py)
    """
    if defaults.get('debug'):
        lx.out(string)
    
    
def setFrames(first,last):
    """
    By Adam O'Hern for Mechanical Color LLC
    
    Sets
    """
    
    scene = modo.Scene()
    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).set(first)
    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).set(last)
    
    
def toConsole(state):
    """
    By Adam O'Hern for Mechanical Color LLC
    
    Enables or disables console logging. Useful for render monitoring.
    """
    
    pass
#    debug('log.toConsole %s' % str(state))
#    lx.eval('log.toConsole %s' % str(state))
#    lx.eval('log.toConsoleRolling %s' % str(state))
    
    
def read_json(file_path):
    """
    By Adam O'Hern for Mechanical Color LLC
    
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


def get_imagesaver(key):
    debug('Looking for imagesaver "%s"' % key)
    
    savers = get_imagesavers()
    debug('Available image savers:')
    for i in savers:
        debug("%s: %s (%s)" % (str(i[0]),str(i[1]),str(i[2])))
        
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
    By Gwynne Reddick
    
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
    By Adam O'Hern for Mechanical Color LLC
    
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


def range_from_string(inputString):
    """
    By Simon Lundberg for Mechanical Color LLC
    
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
            sortedList = rangeFromString(myRangeString).sort()
    """
    try:
        debug("Parsing render range: \"%s\"" % inputString)
        #first we clean up the string, removing any illegal characters
        legalChars = "0123456789-:, "
        cleanString = ""
        frames = []
        for char in inputString:
            if char in legalChars:
                cleanString += char

        rangeStrings = re.findall(r"[-0123456789:]+", cleanString) #splits up by commas and spaces
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
                    start = filterNumerical(parts[-1])
                    step = filterNumerical(parts[0])
                if ":" in end:
                    #check if there is a "step" setting
                    parts = end.split(":")
                    end = filterNumerical(parts[0])
                    step = filterNumerical(parts[-1])
                try:
                    start = int(start)
                    end = int(end)
                    step = int(step)
                except ValueError:
                    parseError(rangeString)
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
                    parseError(rangeString) #skip this one


            else:
                #is a single frame; clean up, turn to an integer and append to list
                cleaned = re.split(r"\D", rangeString)
                try:
                    thisFrame = int(cleaned[0])
                    frames.append(thisFrame)
                except:
                    parseError(rangeString) #skip this one


        #we now have our list of frames, but it's full of duplicates
        #let's filter the list so each frame exists only once
        frames = filterUniques(frames)

        #All done! If frames, return frames, otherwise exit with error
        if frames:
            return frames
        else:
            parseError(inputString)
            return
    except:
        debug(traceback.format_exc())
        
def filterUniques(seq):
    """removes duplicates from input iterable"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def filterNumerical(input):
    """    
    removes any non-numerical characters
    keeps dashes and periods for negatives
    and floating point numbers
    """
    numbers = "0123456789.-"
    if input:
        return "".join([c for c in input if c in numbers])
    else:
        return None
    
def parseError(rangeString):
    """outputs error message if parsing failed"""
    debug("No recognizable sequence info in \"%s\"" % rangeString)