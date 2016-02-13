#python

import lx, modo
import os
import util

def toConsole(state):
    debug('log.toConsole %s' % str(state))
    lx.eval('log.toConsole %s' % str(state))
    lx.eval('log.toConsoleRolling %s' % str(state))

def render_frame(frame, outputPath="*", outputFormat="*", clear=False, group=None):
    """
    By Simon Lundberg and Adam O'Hern for Mechanical Color

    renders a specific frame

    frame:          Integer to choose frame
    outputPath:     String for output if useOutput is False
    outputFormat:   String for output format if useOutput is False
    clear:          Boolean, if True it will clear render on finish
    group:          Pass group to render

    NOTE: returns False if user aborted frame or if there is some error
          in the render process.
          returns True if frame completes without error.
    """

    first = modo.Scene().renderItem.channel('first').get()
    last = modo.Scene().renderItem.channel('last').get()

    modo.Scene().renderItem.channel('first').set(frame)
    modo.Scene().renderItem.channel('last').set(frame)

    group = " group:{%s}" % group if group else ""

    try:
        lx.eval('render.animation {%s} {%s}%s' % (outputPath,outputFormat,group))

    except:
        modo.Scene().renderItem.channel('first').set(first)
        modo.Scene().renderItem.channel('last').set(last)
        lx.out("User aborted")
        return False

    modo.Scene().renderItem.channel('first').set(first)
    modo.Scene().renderItem.channel('last').set(last)

    sleep(0.1)

    if clear:
        lx.eval("!render.clear")

    return True


def render_frames(frames_list, dest_path=None, dest_format=None):
    """
    By Simon Lundberg and Adam O'Hern for Mechanical Color

    takes a list of ints as an argument
    renders all frames in list
    """

    progressbarEnable = True

    try:
        group = lx.eval("!group.current ? pass")
        group_name = lx.eval("query sceneservice item.name ? {%s}" % group)
        if not modo.dialogs.yesNo("Use Pass Group",'Use render pass group "%s"?' % group_name):
            group = None
    except:
        group = None


    if check_output_paths():
        output_dests = "Use filenames specified in render outputs?\n\n"
        for i in [i for i in modo.Scene().iterItems('renderOutput')]:
            dest = i.channel('filename').get()
            dest = '.'.join((dest,get_imagesaver(i.channel('format').get())[2])) if dest else "none"
            output_dests += "%s: %s\n" % (i.name,dest)

        if modo.dialogs.yesNo("Destination", output_dests)=='yes':
            dest_path = "*"
            dest_format = "*"
        else:
            dest_path = None
            dest_format = None

    if not dest_path:
        try:
            try:
                prev = lx.eval("!user.value mecco_renderPath ?")
            except:
                prev = None

            try:
                proj = os.path.join(lx.eval("query platformservice path.path ? project"),"")
            except:
                proj = None

            try:
                scene = os.path.join(os.path.dirname(lx.eval("query sceneservice scene.file ? current")),"")
            except:
                scene = None

            try:
                home = os.path.join(os.path.expanduser("~"),"")
            except:
                home = None

            previous_path = prev if prev else proj if proj else scene if scene else home if home else None

            try:
                previous_format = lx.eval("!user.value mecco_renderFormat ?")
            except:
                previous_format = "openexr"

            savers = util.get_imagesavers()
            savers.insert(0, savers.pop(savers.index([i for i in savers if previous_format in i][0])))

            dest_path = modo.dialogs.customFile(
                'fileSave',
                'Destination',
                [i[0] for i in savers],
                [i[1] for i in savers],
                ext=[i[2] for i in savers],
                path=previous_path
            )

            dest_format = lx.eval("dialog.fileSaveFormat ? format")
            dest_ext = lx.eval("dialog.fileSaveFormat ? extension")
            dest_path = dest_path.rsplit(".", 1)[0]

            set_or_create_user_value("mecco_renderPath", os.path.dirname(dest_path))
            set_or_create_user_value("mecco_renderFormat", dest_format)

        except:
            lx.out("User aborted")
            return

    lx.out("Rendering frames:")
    lx.out(frames_list)

    if progressbarEnable:
        progressbar = lx.Monitor(len(frames_list))
        progressbar.init(len(frames_list))

    for frame in frames_list:
        clearFrame = False if frame == frames_list[-1] else True

        if not render_frame(frame, dest_path, dest_format, clearFrame, group=group):
                break

        sleep(0.5)
        if progressbarEnable:
            progressbar.step(1)
