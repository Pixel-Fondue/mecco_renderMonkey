#python

import lx, os, util, defaults, traceback, modo, symbols, random

PATH = symbols.SCENE_PATH
FORMAT = symbols.FORMAT
FRAMES = symbols.FRAMES
DESTINATION = symbols.DESTINATION
PATTERN = symbols.PATTERN
GROUPS = symbols.GROUPS
WIDTH = symbols.WIDTH
HEIGHT = symbols.HEIGHT
OUTPUTS = symbols.OUTPUTS
CAMERA = symbols.CAMERA

def run(batch_file_path):
    
    restore = {}

    util.debug('Setting up job.')
    util.toConsole(True)
    
    restore['threads'] = lx.eval('pref.value render.threads ?')
    lx.eval('pref.value render.threads auto')

    batch = util.read_yaml(batch_file_path)

    if not batch:
        
        util.debug("Unable to read YAML.")
        return lx.symbol.e_FAILED

    util.debug("Beginning task loop.")
    while True:
        
        util.debug("Scanning for task.")
        for task in batch:
            
            if PATH in task:
                
                util.debug("Task path: %s" % task[PATH])
                
                task_path = util.expand_path(task[PATH])
                util.debug("Expanded task path: %s" % task_path)
                
                if os.path.isfile(task_path):
                    
                    try:
                        util.debug("Opening scene.")
                        lx.eval('scene.open {%s} normal' % task_path)
                        scene = modo.Scene()
                        
                    except:
                        util.debug('Failed to open "%s". Skip task.' % os.path.basename(task_path))
                        util.debug(traceback.format_exc())
                        break

                    
                    
                    try:
                        util.debug("Getting image saver.")
                        imagesaver = task[FORMAT] if FORMAT in task else defaults.get('filetype')
                        if not util.get_imagesaver(imagesaver):
                            util.debug("'%s' is not a valid image saver. Skip task." % imagesaver)
                            util.debug(traceback.format_exc())
                            break
                        destination_extension = util.get_imagesaver(imagesaver)[2].lower()
                    except:
                        util.debug('Failed to get image saver "%s". Skip task.' % imagesaver)
                        util.debug(traceback.format_exc())
                        break

                        
                    
                    
                    try:
                        util.debug("Parsing frames.")
                        frames = task[FRAMES] if FRAMES in task else util.get_scene_render_range()
                        frames_list = util.range_from_string(frames)
                        
                        if not isinstance(frames_list,list) or not len(frames_list)>0:
                            util.debug('"%s" contains no valid frames. Skip task.') % frames
                            util.debug(traceback.format_exc())
                            break
                            
                    except:
                        util.debug('Failed to parse frame range. Skip task.')
                        util.debug(traceback.format_exc())
                        break
                        
                        
                        
                         

                    try:
                        util.debug("Getting output pattern.")
                        scene_pattern = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).get()
                        output_pattern = task[PATTERN] if PATTERN in task else scene_pattern
                    except:
                        util.debug('Failed to parse suffix (i.e. output pattern). Skip task.')
                        util.debug(traceback.format_exc())
                        break        
                         
                            
                            

                    try:
                        util.debug("Getting frame width/height.")
                        
                        scene_width = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESX).get()
                        scene_height = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESY).get()
                        
                        width = int(round(task[WIDTH])) if WIDTH in task else None
                        height = int(round(task[HEIGHT])) if HEIGHT in task else None
                        
                        if not width and not height:
                            width = scene_width
                            height = scene_height
                            
                        elif width and not height:
                            height = int(round(width * (scene_height/scene_width)))
                        
                        elif height and not width:
                            width = int(round(height * (scene_width/scene_height)))
                        
                    except:
                        util.debug('Something went wrong with width/height. Skip task.')
                        util.debug(traceback.format_exc())
                        break         
                         
                            
                            

                    try:
                        util.debug("Getting render outputs.")
                        outputs = task[OUTPUTS] if OUTPUTS in task else None
                        
                        output_items = set()
                        if outputs:
                            for i in outputs:
                                if scene.item(i) and scene.item(i).type == lx.symbol.sITYPE_RENDEROUTPUT:
                                    output_items.add(scene.item(i))
                                else:
                                    util.debug("'%s' is not a valid render output." % i)
                        
                    except:
                        util.debug('Something went wrong getting render outputs. Skip task.')
                        util.debug(traceback.format_exc())
                        break         
                         
                            
                            

                    try:
                        util.debug("Getting render camera.")
                        camera = task[CAMERA] if CAMERA in task else None
                        
                        if camera:
                            try:
                                if not scene.item(camera).type == lx.symbol.sITYPE_CAMERA:
                                    camera = None
                                    raise
                            except:
                                util.debug('Could not set render camera. Skip task.')
                                util.debug(traceback.format_exc())
                                break
                                
                            for i in outputs:
                                if scene.item(i) and scene.item(i).type == lx.symbol.sITYPE_RENDEROUTPUT:
                                    output_items.add(scene.item(i))
                                else:
                                    util.debug("'%s' is not a valid render output." % i)
                        
                    except:
                        util.debug('Something went wrong getting render outputs. Skip task.')
                        util.debug(traceback.format_exc())
                        break                        
                         

                            
                            
                            
                    try:
                        util.debug("Checking pass groups.")
                        
                        pass_group_names = task[GROUPS] if GROUPS in task else None
                        
                        if pass_group_names:
                            pass_group_names = pass_group_names if isinstance(pass_group_names,list) else [pass_group_names]

                            pass_groups = set()
                            for group in pass_group_names:
                                i = scene.item(group)
                                if i:
                                    pass_groups.add(i)
                                else:
                                    util.debug('Could not find group called "%s". Skipping.' % group)

                            util.debug("Creating master pass group.")
                            master_pass_group = create_master_pass_group(pass_groups)
                            master_pass_group = master_pass_group if master_pass_group else None
                            util.debug("...success.")

                        
                    except:
                        util.debug('Failed to parse pass groups. Skip task.')
                        util.debug(traceback.format_exc())
                        break
                        
                        
                        
                    
                    try:
                        util.debug("Getting destination.")
                        destination = task[DESTINATION] if DESTINATION in task else defaults.get('destination')
                        util.debug('Initial destination: %s' % destination)
                        
                        destination = util.expand_path(destination)
                        util.debug('Expanded destination: %s' % destination)
                        
                        if os.path.splitext(destination)[1]:
                            destination_filename = os.path.splitext(os.path.basename(destination))[0]
                            destination_dirname = os.path.dirname(destination)
                        else:
                            destination_filename = os.path.splitext(os.path.basename(task_path))[0]
                            destination_dirname = destination

                        util.debug('Destination dirname: %s' % destination_dirname)
                        util.debug('Destination filename: %s' % destination_filename)
                        
                        destination = os.path.sep.join([destination_dirname,destination_filename])
                        util.debug('Final destination: %s' % destination)

                    except:
                        util.debug('Failed to establish valid destination. Skip task.')
                        util.debug(traceback.format_exc())
                        break
                        
                        
                    if not os.path.exists(destination_dirname):
                        try:
                            os.mkdir(destination_dirname)
                        except OSError:
                            util.debug("Destination directory could not be created. Skip task.")
                            break
                            
                    try:
                        util.debug('Testing write permissions.')
                        test_path = os.path.join(destination_dirname,"tmp_%s.txt" % random.randint(100000,999999))
                        test = open(test_path,'w')
                        test.write("Testing write permissions.")
                        test.close()
                        os.remove(test_path)
                    except:
                        util.debug('Failed to write test file to destination directory. Skip task.')
                        util.debug(traceback.format_exc())
                        break


                        
                        
                    util.debug("Begin rendering loop.")
                    for frame in frames_list:
                        util.debug("Rendering frame %04d" % frame)
                        
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).set(output_pattern)
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).set(frame)
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).set(frame)   
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESX).set(width)
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESY).set(height)
                        
                        if camera:
                            lx.eval('render.camera {%s}' % camera)
                        
                        if outputs_items:
                            for o in scene.items(lx.symbol.sITYPE_RENDEROUTPUT):
                                o.channel(lx.symbol.sICHAN_LOCATOR_VISIBLE).set('off')
                            for o in outputs_items:
                                o.channel(lx.symbol.sICHAN_LOCATOR_VISIBLE).set('on')
                            
                        try:
                            master_pass_group_name = master_pass_group.name
                        except:
                            master_pass_group_name = None
                        
                        args = util.build_arg_string({
                                "filename":destination,
                                "format":imagesaver,
                                "group":master_pass_group_name
                            })
                        
                        command = 'render.animation %s' % args

                        util.debug("Running command: %s" % command)
                        lx.eval(command)
                        
                        
                    util.debug('Completed task "%s". Closing.' % os.path.basename(task_path))
                    lx.eval('!scene.close')
                    
                    
                else:
                    
                    util.debug('"%s" not found. Skip task.' % os.path.basename(task_path))
                
            else:
                
                util.debug("No path specified. Skip task.")
        
        break

    util.toConsole(False)
    lx.eval('pref.value render.threads %s' % restore['threads'])
    
    return lx.symbol.e_OK