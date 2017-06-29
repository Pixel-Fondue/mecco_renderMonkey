# python

import lx
import lxifc

class Notifier(lxifc.Notifier):
    '''
    An event notifier that hooks into modo's CommandEvent

    Args:
        None

    Returns:
        Notifier
    '''
    masterList = {}

    def noti_Name(self):
        '''
        Name of notification

        Args:
            None

        Returns:
            str: monkey.notifier

        .. todo:
            - these methods occur in the class body of a class called Notifier.
              why do the method names need "noti_" prepended to them?
            - Arman: Good question but need to be addressed to Python API developers. It is from lxifc.Notifier.
              We just overwriting it here.
        '''
        return "monkey.notifier"

    def noti_AddClient(self, event):
        '''
        Registers a client event with the masterlist???

        Args:
            event (???): event to be added

        Returns:
            None
        '''
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient(self, event):
        '''
        Removes event from masterlist

        Args:
            event (???): event to be removed

        Returns:
            None
        '''
        del self.masterList[event.__peekobj__()]

    def Notify(self, flags):
        '''
        Fire each event in masterlist with given flags

        Args:
            flags (???): event flags

        Returns:
            None
        '''
        for event in self.masterList:
            evt = lx.object.CommandEvent(self.masterList[event])
            evt.Event(flags)

lx.bless(Notifier, "monkey.notifier")
