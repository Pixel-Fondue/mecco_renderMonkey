#python

import lx, os, util, defaults, traceback, modo

def run(batch_file_path):
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
            
            if 'path' in task:
                
                util.debug("Task path: %s" % task['path'])
                
                task_path = util.expand_path(task['path'])
                util.debug("Expanded task path: %s" % task_path)
                
                if os.path.isfile(task_path):
                    
                    try:
                        lx.eval('scene.open {%s} normal' % task_path)
                    except:
                        util.debug('Failed to open "%s". Skip task.' % os.path.basename(task_path))
                        util.debug(traceback.format_exc())
                        break

                    
                    
                    
                    try:
                        imagesaver = task['format'] if 'format' in task else defaults.get('filetype')
                        destination_extension = util.get_imagesaver(imagesaver)[2].lower()
                    except:
                        util.debug('Failed to get image saver "%s". Skip task.' % imagesaver)
                        util.debug(traceback.format_exc())
                        break

                        
                    
                    
                    try:
                        frames = task['frames'] if 'frames' in task else defaults.get('frames')
                        frames_list = util.range_from_string(frames)
                    except:
                        util.debug('Failed to parse frame range. Skip task.')
                        util.debug(traceback.format_exc())
                        break


                    
                    
                    try:
                        destination = task['destination'] if 'destination' in task else defaults.get('destination')
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
                        

                    
                    for frame in frames_list:
                        util.debug("Rendering frame %04d" % frame)
                        
                        util.setFrames(frame,frame)
                        command = 'render.animation filename:{%s} format:%s' % (destination,imagesaver)

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