# python
'''
The Message module contains the message function, which is used for querying
the modo message service
'''
import lx


def message(table, message_id, *args):
    '''
    A convenience function for querying the modo message service

    Args:
        table (???): table to be queried
        message_id (???): id of message to be found
        \*args: additional message arguments (see modo messageservice msgcompose)

    Returns:
        str: lx.eval of query
    '''
    if len(args) != 0:
        args_list = ["{%s}" % arg for arg in args]
        cmd = ("query messageservice msgcompose ? {@%s@@%s@" + " %s" * len(args) + "}") % tuple([table, message_id] + args_list)
    else:
        cmd = ("query messageservice msgfind ? {@%s@@%s@}") % (table, message_id)
    return lx.eval(cmd)
