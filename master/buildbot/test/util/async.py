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

from twisted.internet import reactor
from twisted.python import util
from twisted.python import log
from twisted.python import failure
import traceback


class CallbacksList(list):
    __slots__ = [ 'creator', 'handled' ]

    def append(self, what):
        self.handled = True
        super(CallbacksList,self).append(what)

    def __del__(self):
        if not self.handled:
            log.msg("Unhandled deferred created at:\n" + ''.join(self.creator),
                    isError=True)
            log.err(failure.Failure(RuntimeError("Unhandled Deferred")))


def mustHandleDeferred(fn):
    "Decorate a function that returns a Deferred which callers must handle."
    def wrap(*args, **kwargs):
        # Callbacks are "normally" added by the d.addXxx methods, but when
        # chaining Deferreds by returning them from a callback, the callbacks
        # are appended directly to d.callbacks.  So we interpret
        # d.callbacks.append as "handling" the Deferred, and garbage-collection
        # of d.callbacks as the Deferred being garbage-collected.
        d = fn(*args, **kwargs)

        # If the deferred is called already and this Deferred is chained into
        # another, then the callback-running code will do some fancy stuff to
        # steal its result without ever adding a callback.  That spoils our
        # plan, but pausing and later unpausing the Deferred works around this
        # issue.
        if d.called:
            d.pause()
            reactor.callLater(0, d.unpause)

        d.callbacks = CallbacksList(d.callbacks)
        d.callbacks.handled = False
        d.callbacks.creator = traceback.format_stack()[:-1]
        return d
    wrap.func_original = fn
    util.mergeFunctionMetadata(fn, wrap)
    return wrap
