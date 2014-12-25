# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import weakref

from twisted.internet import defer

_services = weakref.WeakValueDictionary()
def dump(msg):
    print msg
    for svc in _services.values():
        print '', svc, svc._debug_status

def assert_all_stopped():
    for svc in _services.values():
        if svc._debug_status != 'stopped':
            dump("un-stopped services")
            raise AssertionError()

def patch():
    """
    Patch startService and stopService so that they check the previous state
    first.

    (used for debugging only)
    """
    from twisted.application.service import Service
    old_setServiceParent = Service.setServiceParent

    def setServiceParent(self, parent):
        if id(self) in _services:
            return old_setServiceParent(self, parent)
        _services[id(self)] = self
        self._debug_status = 'stopped'

        # patch these methods on the *instance*, so we are at the bottom
        # of the chain of calls up the inheritance hierarchy
        old_startService = self.startService
        def startService():
            assert self._debug_status == 'stopped', \
                    "%r already %s" % (self, self._debug_status)
            self._debug_status = 'starting'
            d = old_startService()
            if isinstance(d, defer.Deferred):
                @d.addCallback
                def status(x):
                    self._debug_status = 'running'
                    return x
                return d
            else:
                self._debug_status = 'running'
                return d
        self.startService = startService

        old_stopService = self.stopService
        def stopService():
            assert self._debug_status == 'running', \
                    "%r already %s" % (self, self._debug_status)
            self._debug_status = 'stopping'
            d = old_stopService()
            if isinstance(d, defer.Deferred):
                @d.addCallback
                def status(x):
                    self._debug_status = 'stopped'
                    return x
                return d
            else:
                self._debug_status = 'stopped'
                return d
        self.stopService = stopService

        return old_setServiceParent(self, parent)

    Service.setServiceParent = setServiceParent
