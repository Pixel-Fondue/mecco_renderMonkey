#python

import lx, os, util, defaults, traceback, modo, symbols, random, sys

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
RENDER_CHANNELS = symbols.RENDER_CHANNELS
STATUS = symbols.STATUS
STATUS_COMPLETE = symbols.STATUS_COMPLETE
STATUS_IN_PROGRESS = symbols.STATUS_IN_PROGRESS
STATUS_FAILED = symbols.STATUS_FAILED
STATUS_AVAILABLE = symbols.STATUS_AVAILABLE

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

        
    util.debug("Scanning for task.")
    for task_index, task in enumerate(batch):
        
        
        if not util.get_task_status(batch_file_path,task_index) == STATUS_AVAILABLE:
            util.debug("'%s'. Skip task." % util.get_task_status(batch_file_path,task_index))
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue
        

        if PATH not in task:
            util.debug("No path specified. Skip task.")
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue

        util.status("Begin task: %s" % task[PATH])

        task_path = util.expand_path(task[PATH])
        util.debug("Expanded task path: %s" % task_path)


        if not os.path.isfile(task_path):
            util.debug('"%s" not found. Skip task.' % os.path.basename(task_path))
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue

        util.debug("Opening scene.")
        try:
            lx.eval('scene.open {%s} normal' % task_path)
            scene = modo.Scene()

        except:
            util.status('Failed to open "%s". Skip task.' % os.path.basename(task_path))
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue





        util.debug("Parsing frames.")
        try:
            frames = task[FRAMES] if FRAMES in task else util.get_scene_render_range()
            frames_list = util.range_from_string(frames)

            if not isinstance(frames_list,list) or not len(frames_list)>0:
                util.status('"%s" contains no valid frames. Skip task.') % frames
                util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue

        except:
            util.status('Failed to parse frame range. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue

        if not frames_list:
            util.status("No frames to render. Skip task.")
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue

        if not [i for i in frames_list if util.get_frame_status(batch_file_path,task_index,i) == STATUS_AVAILABLE]:
            util.status("No available_frames. Skip task.")
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        util.debug("Getting image saver.")
        try:
            imagesaver = task[FORMAT] if FORMAT in task else defaults.get('filetype')
            if not util.get_imagesaver(imagesaver):
                util.status("'%s' is not a valid image saver. Skip task." % imagesaver)
                util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue
            destination_extension = util.get_imagesaver(imagesaver)[2].lower()
        except:
            util.status('Failed to get image saver "%s". Skip task.' % imagesaver)
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        util.debug("Getting output pattern.")
        try:
            scene_pattern = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).get()
            output_pattern = task[PATTERN] if PATTERN in task else scene_pattern
        except:
            util.status('Failed to parse suffix (i.e. output pattern). Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue        





        util.debug("Getting frame width/height.")
        try:
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
            util.status('Something went wrong with width/height. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue         





        util.debug("Getting render outputs.")
        try:
            outputs = task[OUTPUTS] if OUTPUTS in task else None

            output_items = set()
            if outputs:
                for i in outputs:
                    if scene.item(i) and scene.item(i).type == lx.symbol.sITYPE_RENDEROUTPUT:
                        output_items.add(scene.item(i))
                    else:
                        util.status("'%s' is not a valid render output." % i)

        except:
            util.status('Something went wrong getting render outputs. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue         





        util.debug("Getting render camera.")
        try:
            camera = task[CAMERA] if CAMERA in task else None

            if camera:
                try:
                    if not scene.item(camera).type == lx.symbol.sITYPE_CAMERA:
                        camera = None
                        raise
                except:
                    util.status('Could not set render camera. Skip task.')
                    continue

        except:
            util.status('Something went wrong getting render outputs. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue                        






        util.debug("Checking pass groups.")    
        try:
            pass_group_names = task[GROUPS] if GROUPS in task else None

            if pass_group_names:
                pass_group_names = pass_group_names if isinstance(pass_group_names,list) else [pass_group_names]

                pass_groups = set()
                for group in pass_group_names:
                    i = scene.item(group)
                    if i:
                        pass_groups.add(i)
                    else:
                        util.debug('Could not find group called "%s". Skipping group.' % group)

                if len(pass_groups) > 1:
                    util.debug("Creating master pass group from provided pass groups.")
                    master_pass_group = util.create_master_pass_group(list(pass_groups))
                    master_pass_group = master_pass_group if master_pass_group else None
                    util.debug("...success.")
                elif len(pass_groups) == 1:
                    util.debug("Only one valid pass group provided. Using as-is.")
                    master_pass_group = list(pass_groups)[0]
                else:
                    util.debug("No valid pass groups provided. Using as-is.")
                    master_pass_group = None
                         

        except:
            util.status('Failed to parse pass groups. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        util.debug("Getting destination.")
        try:
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
            util.status('Failed to establish valid destination. Skip task.')
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue


        util.debug('Testing write permissions.')
        if not util.test_writeable(destination_dirname):
            util.status("Could not write to destination. Skip task.")
            util.set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue



        render_channels = task[RENDER_CHANNELS] if RENDER_CHANNELS in task else {}




        util.debug("Begin rendering loop.")
        for frame in frames_list:

            if (util.get_frame_status(batch_file_path,task_index,frame) == STATUS_AVAILABLE):

                util.set_frame_status(batch_file_path,task_index,frame,symbols.STATUS_IN_PROGRESS)

                util.debug("Setting up frame %04d..." % frame)

                util.debug("Setting render channels.")
                try:
                    if render_channels:
                        util.debug("render_channels: %s" % render_channels)
                        for channel, value in render_channels.iteritems():
                            try:
                                util.debug("Setting '%s' to '%s'" % (channel,str(value)))
                                scene.renderItem.channel(channel).set(value)
                            except:
                                debug("%s could not be set. Skip task.")
                                util.debug("Unexpected error: %s" % sys.exc_info()[0])
                                util.set_frame_status(batch_file_path,task_index,frame,symbols.STATUS_FAILED)
                                continue

                    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).set(output_pattern)
                    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).set(frame)
                    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).set(frame)   
                    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESX).set(width)
                    scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESY).set(height)

                    if camera:
                        lx.eval('render.camera {%s}' % camera)
                except:
                    util.debug("Failed to set render channels. Skip.")
                    util.debug("Unexpected error: %s" % sys.exc_info()[0])
                    util.set_frame_status(batch_file_path,task_index,frame,symbols.STATUS_FAILED)
                    continue



                util.debug("Setting output visibility.")
                try:
                    if output_items:
                        for o in scene.items(lx.symbol.sITYPE_RENDEROUTPUT):
                            o.channel(lx.symbol.sICHAN_LOCATOR_VISIBLE).set('off')
                        for o in output_items:
                            o.channel(lx.symbol.sICHAN_LOCATOR_VISIBLE).set('on')
                    util.debug("...success.")
                except:
                    util.debug("Failed to set output visibility. Skip.")
                    util.debug("Unexpected error: %s" % sys.exc_info()[0])
                    util.set_frame_status(batch_file_path,task_index,frame,symbols.STATUS_FAILED)
                    continue


                util.debug("Setting master pass group name.")
                try:
                    master_pass_group_name = master_pass_group.name
                    util.debug("...success.")
                except:
                    master_pass_group_name = None
                    util.debug("Failed to set master pass group name. Using None.")



                args = util.build_arg_string({
                        "filename":destination,
                        "format":imagesaver,
                        "group":master_pass_group_name
                    })

                command = 'render.animation %s' % args

                util.debug("Running command: %s" % command)
                try:
                    lx.eval(command)
                    util.set_frame_status(batch_file_path,task_index,frame,symbols.STATUS_COMPLETE)

                except:
                    util.debug('Render failed. Skip frame.' % os.path.basename(task_path))

            else:
                util.debug("%s. Skip frame." % util.get_frame_status(batch_file_path,task_index,frame))

        util.debug('Completed task "%s". Closing.' % os.path.basename(task_path))
        util.set_task_status(batch_file_path,task_index,STATUS_COMPLETE)
        lx.eval('!scene.close')


    util.toConsole(False)
    lx.eval('pref.value render.threads %s' % restore['threads'])
    
    return lx.symbol.e_OK