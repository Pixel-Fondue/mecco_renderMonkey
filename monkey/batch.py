#python

import lx, os, util, defaults, traceback, modo, symbols

PATH = symbols.SCENE_PATH
FORMAT = symbols.FORMAT
FRAMES = symbols.FRAMES
DESTINATION = symbols.DESTINATION
PATTERN = symbols.PATTERN
GROUPS = symbols.GROUPS

def run(batch_file_path):
    scene = modo.Scene()
    restore = {}

    util.debug('Setting up job.')
    util.toConsole(True)
    
    restore['threads'] = lx.eval('pref.value render.threads ?')
    lx.eval('pref.value render.threads auto')

    batch_json = util.read_json(batch_file_path)

    if not batch_json:
        
        util.debug("Unable to read JSON.")
        return lx.symbol.e_FAILED

    util.debug("Beginning task loop.")
    while True:
        
        util.debug("Scanning for task.")
        for task in batch_json:
            
            if PATH in task:
                
                util.debug("Task path: %s" % task[PATH])
                
                task_path = util.expand_path(task[PATH])
                util.debug("Expanded task path: %s" % task_path)
                
                if os.path.isfile(task_path):
                    
                    try:
                        util.debug("Opening scene.")
                        lx.eval('scene.open {%s} normal' % task_path)
                    except:
                        util.debug('Failed to open "%s". Skip task.' % os.path.basename(task_path))
                        util.debug(traceback.format_exc())
                        break

                    
                    
                    
                    try:
                        util.debug("Getting image saver.")
                        imagesaver = task[FORMAT] if FORMAT in task else defaults.get('filetype')
                        destination_extension = util.get_imagesaver(imagesaver)[2].lower()
                    except:
                        util.debug('Failed to get image saver "%s". Skip task.' % imagesaver)
                        util.debug(traceback.format_exc())
                        break

                        
                    
                    
                    try:
                        util.debug("Parsing frames.")
                        frames = task[FRAMES] if FRAMES in task else util.get_scene_render_range()
                        frames_list = util.range_from_string(frames)
                    except:
                        util.debug('Failed to parse frame range. Skip task.')
                        util.debug(traceback.format_exc())
                        break
                        
                        
                        
                         

                    try:
                        util.debug("Getting output pattern.")
                        
                        #Bug. Either of the following should work, and does work in isolation. Crashing MODO in this context:
                        #scene_pattern = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).get()
                        #scene_pattern = lx.eval('item.channel item:{%s} name:{%s} value:?' % (scene.renderItem.id,lx.symbol.sICHAN_POLYRENDER_OUTPAT))
                        
                        #Because of bug above, using default value instead (for now):
                        scene_pattern = defaults.get('output_pattern')
                        
                        output_pattern = task['suffix'] if 'suffix' in task else scene_pattern
                    except:
                        util.debug('Failed to parse suffix (i.e. output pattern). Skip task.')
                        util.debug(traceback.format_exc())
                        break                        
                         

                            
                            
                            
                    try:
                        util.debug("Getting pass groups.")
                        
                        # CRASH
                        
                        pass_group_names = task[GROUPS] if GROUPS in task else None
                        pass_group_names = pass_group_names if isinstance(pass_group_names,list) else [pass_group_names]
                        
                        util.debug("Making sure pass groups are legit...")
                        pass_groups = set()
                        for group in pass_group_names:
                            i = scene.item(group)
                            if i:
                                pass_groups.add(i)
                            else:
                                util.debug('Could not find group called "%s". Skipping.' % group)
                        util.debug("Pass groups now legit.")
                                
                        util.debug("Making master pass group.")
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
                        

                    util.debug("Begin rendering loop.")
                    for frame in frames_list:
                        util.debug("Rendering frame %04d" % frame)
                        
                        scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).set(output_pattern)
                        util.setFrames(frame,frame)
                        
                        args = util.build_arg_string({
                                "filename":destination,
                                "format":imagesaver,
                                "group":master_pass_group.name
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