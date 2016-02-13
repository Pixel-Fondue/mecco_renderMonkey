#python

import lx, os, util, defaults, traceback, modo, random, sys

from symbols import *

def batch_status_file(batch_file_path):
    split = os.path.splitext(batch_file_path)
    return "%s_%s%s" % (split[0],STATUS_FILE_SUFFIX,split[1])

def batch_status_create(data,batch_file_path):
    if not os.path.isfile(batch_status_file(batch_file_path)):
        status_file = open(batch_status_file(batch_file_path),'w')
        status_file.write(io.yamlize(data))
        status_file.close()

def batch_has_status(batch_file_path):
    if os.path.isfile(batch_status_file(batch_file_path)):
        return True

    return False

def batch_status_reset(batch_file_path):
    try:
        status_file = open(batch_status_file(batch_file_path),'w')
    except:
        debug(traceback.format_exc())
        return False

    data = io.read_yaml(batch_file_path)

    try:
        status_file.write(yaml.dump(data, indent=4,width=999,default_flow_style = False).replace("\n-","\n\n-"))
    except:
        debug(traceback.format_exc())
        status_file.close()
        return False

    status_file.close()
    return True

def set_task_status(batch_file_path,task_index,status):
    batch_file_path = batch_status_file(batch_file_path)
    batch = io.read_yaml(batch_file_path)

    if not batch:
        return False

    try:
        if STATUS not in batch[task_index] or not isinstance(batch[task_index][STATUS],list):
            batch[task_index][STATUS] = []

        batch[task_index][STATUS] = [i for i in batch[task_index][STATUS] if not i.startswith(TASK)]
        batch[task_index][STATUS].append("%s %s" % (TASK,status))

        io.write_yaml(batch,batch_file_path)
        return True
    except:
        status("Problem writing task status to batch file.")
        return False

def get_task_status(batch_file_path,task_index):
    batch_file_path = batch_status_file(batch_file_path)
    batch = io.read_yaml(batch_file_path)

    if not batch:
        return STATUS_AVAILABLE

    if STATUS in batch[task_index]:
        for i in batch[task_index][STATUS]:
            if i.startswith(TASK) and not STATUS_AVAILABLE in i:
                return i

    return STATUS_AVAILABLE

def set_frame_status(batch_file_path,task_index,frame_number,status):
    batch_file_path = batch_status_file(batch_file_path)
    batch = io.read_yaml(batch_file_path)

    if not batch:
        return False

    try:
        if STATUS not in batch[task_index] or not isinstance(batch[task_index][STATUS],list):
            batch[task_index][STATUS] = []

        batch[task_index][STATUS] = [i for i in batch[task_index][STATUS] if not int(re.search('^[0-9]*',i).group(0)) == frame_number]
        batch[task_index][STATUS].append("%04d %s" % (frame_number,status))

        io.write_yaml(batch,batch_file_path)
        return True
    except:
        status("Problem writing frame status to batch file.")
        return False

def get_frame_status(batch_file_path,task_index,frame_number):
    batch_file_path = batch_status_file(batch_file_path)
    batch = io.read_yaml(batch_file_path)

    if not batch:
        return STATUS_AVAILABLE

    if STATUS in batch[task_index]:
        for i in batch[task_index][STATUS]:
            if int(re.search('^[0-9]*',i).group(0)) == frame_number and not STATUS_AVAILABLE in i:
                return i

    return STATUS_AVAILABLE


def run(batch_file_path):

    restore = {}

    util.debug('Setting up job.')
    render.toConsole(True)

    restore['threads'] = lx.eval('pref.value render.threads ?')
    lx.eval('pref.value render.threads auto')

    batch = util.read_yaml(batch_file_path)

    if not batch:
        util.status("Unable to read YAML.")
        return lx.symbol.e_FAILED


    if batch_has_status(batch_file_path):
        reset = modo.dialogs.yesNoCancel('Reset Batch',"Batch file in progress. Reset and start over?\n\nYes: Reset\nNo: Continue\nCancel: Abort")
        if reset in ('ok','yes'):
            util.status("Resetting batch file.")
            if not batch_status_reset(batch_file_path):
                util.status("Could not reset status file. Abort.")
                sys.exit()
        elif reset == "cancel":
            util.status("User cancel.")
            sys.exit()
        else:
            util.status("Continue batch as-is.")
    else:
        batch_status_create(batch,batch_file_path)

    StdDialog = lx.service.StdDialog()
    main_monitor = lx.object.Monitor(StdDialog.MonitorAllocate('Running Batch'))
    main_monitor.Initialize(len(batch))

    util.debug("Scanning for task.")
    for task_index, task in enumerate(batch):


        if not get_task_status(batch_file_path,task_index) == STATUS_AVAILABLE:
            util.status("Task %s status: '%s'. Skip task." % (task_index,get_task_status(batch_file_path,task_index)))
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue


        if PATH not in task:
            util.status("No path specified for task %s. Skip task." % task_index)
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue

        task_path = util.expand_path(task[PATH])

        if not os.path.isfile(task_path):
            util.status('"%s" not found. Skip task.' % os.path.basename(task_path))
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue





        util.status("Begin task %s (%s)" % (task_index,os.path.basename(task_path)))

        try:
            lx.eval('scene.open {%s} normal' % task_path)
            scene = modo.Scene()

        except:
            util.status('Failed to open "%s". Skip task.' % os.path.basename(task_path))
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            continue





        try:
            frames = task[FRAMES] if FRAMES in task else util.get_scene_render_range()
            frames_list = util.range_from_string(frames)

            if not isinstance(frames_list,list) or not len(frames_list)>0:
                util.status('"%s" contains no valid frames. Skip task.') % frames
                set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue

        except:
            util.status('Failed to parse frame range. Skip task.')
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue

        if not frames_list:
            util.status("No valid frames to render. Skip task.")
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue

        if not [i for i in frames_list if get_frame_status(batch_file_path,task_index,i) == STATUS_AVAILABLE]:
            util.status("No available frames. Skip task.")
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        try:
            imagesaver = task[FORMAT] if FORMAT in task else defaults.get('filetype')
            if not util.get_imagesaver(imagesaver):
                util.status("'%s' is not a valid image saver. Skip task." % imagesaver)
                set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue
            destination_extension = util.get_imagesaver(imagesaver)[2].lower()
        except:
            util.status('Failed to get image saver "%s". Skip task.' % imagesaver)
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        try:
            scene_pattern = scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).get()
            output_pattern = task[PATTERN] if PATTERN in task else scene_pattern
        except:
            util.status('Failed to parse suffix (i.e. output pattern). Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        try:
            scene_width = float(scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESX).get())
            scene_height = float(scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESY).get())

            width = round(float(task[WIDTH])) if WIDTH in task else None
            height = round(float(task[HEIGHT])) if HEIGHT in task else None

            if not width and not height:
                width = scene_width
                height = scene_height

            elif width and not height:
                height = int(round(width * (scene_height/scene_width)))

            elif height and not width:
                width = int(round(height * (scene_width/scene_height)))

        except:
            util.status('Something went wrong with width/height. Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        try:
            outputs = task[OUTPUTS] if OUTPUTS in task else None
            if isinstance(outputs,str):
                outputs = [outputs]

            output_items = set()
            if outputs:
                for i in outputs:
                    if scene.item(i) and scene.item(i).type == lx.symbol.sITYPE_RENDEROUTPUT:
                        output_items.add(scene.item(i))
                    else:
                        util.status("'%s' is not a valid render output. Ignore." % i)

        except:
            util.status('Something went wrong getting render outputs. Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





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
            util.status('Something went wrong setting the render camera. Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue






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
                        util.debug('Could not find group called "%s". Ignore.' % group)

                if len(pass_groups) > 1:
                    master_pass_group = util.create_master_pass_group(list(pass_groups))
                    master_pass_group = master_pass_group if master_pass_group else None
                elif len(pass_groups) == 1:
                    master_pass_group = list(pass_groups)[0]
                else:
                    master_pass_group = None


        except:
            util.status('Failed to parse pass groups. Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue





        try:
            destination = task[DESTINATION] if DESTINATION in task else defaults.get('destination')
            destination = util.expand_path(destination)

            if os.path.splitext(destination)[1]:
                destination_filename = os.path.splitext(os.path.basename(destination))[0]
                destination_dirname = os.path.dirname(destination)
            else:
                destination_filename = os.path.splitext(os.path.basename(task_path))[0]
                destination_dirname = destination

            destination = os.path.sep.join([destination_dirname,destination_filename])

        except:
            util.status('Failed to establish valid destination. Skip task.')
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue


        if not util.test_writeable(destination_dirname):
            util.status("Could not write to destination. Skip task.")
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue



        render_channels = task[RENDER_CHANNELS] if RENDER_CHANNELS in task else {}

        if render_channels:
            try:
                for channel, value in render_channels.iteritems():
                    try:
                        scene.renderItem.channel(channel).set(value)
                    except:
                        util.status("%s could not be set. Skip task.")
                        util.debug(traceback.format_exc())
                        lx.eval('!scene.close')
                        continue
            except:
                util.status("Failed to set rener channels. Skip task.")
                util.debug(traceback.format_exc())
                set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue


        try:
            scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_OUTPAT).set(output_pattern)
            scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESX).set(width)
            scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_RESY).set(height)

        except:
            util.status("Failed to set render channels. Skip task.")
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue


        if camera:
            try:
                lx.eval('render.camera {%s}' % camera)
            except:
                util.status("Failed to set render camera. Skip task.")
                util.debug(traceback.format_exc())
                set_task_status(batch_file_path,task_index,STATUS_FAILED)
                lx.eval('!scene.close')
                continue


        try:
            if output_items:
                for o in scene.items(lx.symbol.sITYPE_RENDEROUTPUT):
                    o.channel(lx.symbol.sICHAN_TEXTURELAYER_ENABLE).set(0)
                for o in output_items:
                    o.channel(lx.symbol.sICHAN_TEXTURELAYER_ENABLE).set(1)
        except:
            util.status("Failed to set output visibility. Skip task.")
            util.debug(traceback.format_exc())
            set_task_status(batch_file_path,task_index,STATUS_FAILED)
            lx.eval('!scene.close')
            continue


        try:
            master_pass_group_name = master_pass_group.name
        except:
            util.status("Failed to set master pass group name. Ignore.")
            util.debug(traceback.format_exc())
            master_pass_group_name = None




        util.status("Rendering frames: %s" % str(frames_list))
        for frame in frames_list:
            main_monitor.Increment(1/len(frames_list))

            try:
                scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_FIRST).set(frame)
                scene.renderItem.channel(lx.symbol.sICHAN_POLYRENDER_LAST).set(frame)
            except:
                util.status("Failed to set first/last frames to %04d. Skip frame." % frame)
                util.debug(traceback.format_exc())
                continue


            if not get_frame_status(batch_file_path,task_index,frame) == STATUS_AVAILABLE:
                util.status("frame status: %s. Skip frame." % get_frame_status(batch_file_path,task_index,frame))
                continue


            set_frame_status(batch_file_path,task_index,frame,STATUS_IN_PROGRESS)
            util.status("Rendering frame %04d." % frame)

            args = util.build_arg_string({
                    "filename":destination,
                    "format":imagesaver,
                    "group":master_pass_group_name
                })

            command = 'render.animation %s' % args

            try:
                lx.eval(command)
                set_frame_status(batch_file_path,task_index,frame,STATUS_COMPLETE)
            except:
                util.status('"%s" failed. Skip frame.' % command)
                util.debug(traceback.format_exc())


        util.debug('Completed task %s (%s). Continue.' % (task_index,os.path.basename(task_path)))
        set_task_status(batch_file_path,task_index,STATUS_COMPLETE)
        lx.eval('!scene.close')


    render.toConsole(False)
    lx.eval('pref.value render.threads %s' % restore['threads'])

    return lx.symbol.e_OK
