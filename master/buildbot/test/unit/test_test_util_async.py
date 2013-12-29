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

from buildbot import util
from buildbot.test.util import async
from buildbot.test.util import logging
from twisted.internet import defer
from twisted.trial import unittest
import gc


class MustHandleDeferred(logging.LoggingMixin, unittest.TestCase):

    def setUp(self):
        self.setUpLogging()

    @async.mustHandleDeferred
    def asyncMethod(self):
        return util.asyncSleep(0)

    @async.mustHandleDeferred
    def asyncMethodImmediate(self):
        return defer.succeed(None)

    @defer.inlineCallbacks
    def test_unhandled(self):
        self.asyncMethod()  # unhandled Deferred
        gc.collect()
        yield util.asyncSleep(0)
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 1)
        self.assertLogged('self.asyncMethod\(\)  # unhandled Deferred')

    @defer.inlineCallbacks
    def test_unhandled_immediate(self):
        self.asyncMethodImmediate()  # unhandled Deferred
        gc.collect()
        yield util.asyncSleep(0)
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 1)
        self.assertLogged('self.asyncMethodImmediate\(\)  # unhandled Deferred')

    @defer.inlineCallbacks
    def test_handled(self):
        d = self.asyncMethod()
        d.addCallback(lambda _: None)
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

    @defer.inlineCallbacks
    def test_handledImmediate(self):
        d = self.asyncMethodImmediate()
        d.addCallback(lambda _: None)
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

    @defer.inlineCallbacks
    def test_chained(self):
        d = defer.Deferred()
        d.addCallback(lambda _: self.asyncMethod())
        d.callback(None)
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

    @defer.inlineCallbacks
    def test_chainedImmediate(self):
        d = defer.Deferred()
        d.addCallback(lambda _: self.asyncMethodImmediate())
        d.callback(None)
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

    @defer.inlineCallbacks
    def test_chainedToImmediate(self):
        d = defer.succeed(None)
        d.addCallback(lambda _: self.asyncMethod())
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

    @defer.inlineCallbacks
    def test_chainedImmediateToImmediate(self):
        d = defer.succeed(None)
        d.addCallback(lambda _: self.asyncMethodImmediate())
        yield d
        gc.collect()
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 0)

