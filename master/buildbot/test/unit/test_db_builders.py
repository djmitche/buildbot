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

from buildbot.db import builders
from buildbot.db import tags
from buildbot.test.fake import fakedb
from buildbot.test.fake import fakemaster
from buildbot.test.util import connector_component
from buildbot.test.util import interfaces
from buildbot.test.util import validation
from twisted.internet import defer
from twisted.trial import unittest


class Tests(interfaces.InterfaceTests):

    # common sample data

    builder_row = [
        fakedb.Builder(id=7, name="some:builder"),
    ]

    # tests

    def test_signature_findBuilderId(self):
        @self.assertArgSpecMatches(self.db.builders.findBuilderId)
        def findBuilderId(self, slug):
            pass

    def test_signature_addBuilderMaster(self):
        @self.assertArgSpecMatches(self.db.builders.addBuilderMaster)
        def addBuilderMaster(self, builderid=None, masterid=None):
            pass

    def test_signature_removeBuilderMaster(self):
        @self.assertArgSpecMatches(self.db.builders.removeBuilderMaster)
        def removeBuilderMaster(self, builderid=None, masterid=None):
            pass

    def test_signature_getBuilder(self):
        @self.assertArgSpecMatches(self.db.builders.getBuilder)
        def getBuilder(self, builderid):
            pass

    def test_signature_getBuilders(self):
        @self.assertArgSpecMatches(self.db.builders.getBuilders)
        def getBuilders(self, masterid=None):
            pass

    def test_signature_updateBuilderInfo(self):
        @self.assertArgSpecMatches(self.db.builders.updateBuilderInfo)
        def updateBuilderInfo(self, builderid, name, description, tags):
            pass

    @defer.inlineCallbacks
    def test_updateBuilderInfo(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder7', slug='b7'),
            fakedb.Builder(id=8, name='some:builder8', slug='b8'),
        ])

        yield self.db.builders.updateBuilderInfo(
            7, u'someb7', u'a descr',
            [u'cat1', u'cat2'])
        yield self.db.builders.updateBuilderInfo(
            8, u'someb8', u'a descr',
            [])
        builderdict7 = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict7)
        builderdict7['tags'].sort()  # order is unspecified
        self.assertEqual(builderdict7,
                         dict(id=7, name=u'someb7', tags=['cat1', 'cat2'],
                              slug=u'b7', masterids=[], description='a descr'))
        builderdict8 = yield self.db.builders.getBuilder(8)
        validation.verifyDbDict(self, 'builderdict', builderdict8)
        self.assertEqual(builderdict8,
                         dict(id=8, name='someb8', tags=[],
                              slug=u'b8', masterids=[], description='a descr'))

    @defer.inlineCallbacks
    def test_findBuilderId_new(self):
        id = yield self.db.builders.findBuilderId(u'some-builder')
        builderdict = yield self.db.builders.getBuilder(id)
        self.assertEqual(builderdict,
                         dict(id=id, name='some-builder', slug='some-builder',
                              tags=[], masterids=[], description=None))

    @defer.inlineCallbacks
    def test_findBuilderId_exists(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder', slug='some'),
        ])
        id = yield self.db.builders.findBuilderId(u'some')
        self.assertEqual(id, 7)

    def test_findBuilderId_not_ident(self):
        self.assertRaises(AssertionError, lambda:
                          self.db.builders.findBuilderId('not an identifier'))

    @defer.inlineCallbacks
    def test_addBuilderMaster(self):
        yield self.insertTestData([
            fakedb.Builder(id=7),
            fakedb.Master(id=9, name='abc'),
            fakedb.Master(id=10, name='def'),
            fakedb.BuilderMaster(builderid=7, masterid=10),
        ])
        yield self.db.builders.addBuilderMaster(builderid=7, masterid=9)
        builderdict = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(builderdict,
                         dict(id=7, name='some:builder', tags=[],
                              slug='some_builder', masterids=[9, 10],
                              description=None))

    @defer.inlineCallbacks
    def test_addBuilderMaster_already_present(self):
        yield self.insertTestData([
            fakedb.Builder(id=7),
            fakedb.Master(id=9, name='abc'),
            fakedb.Master(id=10, name='def'),
            fakedb.BuilderMaster(builderid=7, masterid=9),
        ])
        yield self.db.builders.addBuilderMaster(builderid=7, masterid=9)
        builderdict = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(builderdict,
                         dict(id=7, name='some:builder', slug='some_builder',
                              tags=[], masterids=[9], description=None))

    @defer.inlineCallbacks
    def test_removeBuilderMaster(self):
        yield self.insertTestData([
            fakedb.Builder(id=7),
            fakedb.Master(id=9, name='some:master'),
            fakedb.Master(id=10, name='other:master'),
            fakedb.BuilderMaster(builderid=7, masterid=9),
            fakedb.BuilderMaster(builderid=7, masterid=10),
        ])
        yield self.db.builders.removeBuilderMaster(builderid=7, masterid=9)
        builderdict = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(builderdict,
                         dict(id=7, name='some:builder', tags=[],
                              slug='some_builder', masterids=[10],
                              description=None))

    @defer.inlineCallbacks
    def test_getBuilder_no_masters(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder', slug='some'),
        ])
        builderdict = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(builderdict,
                         dict(id=7, name='some:builder', slug='some', tags=[],
                              masterids=[], description=None))

    @defer.inlineCallbacks
    def test_getBuilder_with_masters(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder'),
            fakedb.Master(id=3, name='m1'),
            fakedb.Master(id=4, name='m2'),
            fakedb.BuilderMaster(builderid=7, masterid=3),
            fakedb.BuilderMaster(builderid=7, masterid=4),
        ])
        builderdict = yield self.db.builders.getBuilder(7)
        validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(builderdict,
                         dict(id=7, name='some:builder', tags=[],
                              slug='some_builder', masterids=[3, 4],
                              description=None))

    @defer.inlineCallbacks
    def test_getBuilder_missing(self):
        builderdict = yield self.db.builders.getBuilder(7)
        self.assertEqual(builderdict, None)

    @defer.inlineCallbacks
    def test_getBuilders(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder', slug='some'),
            fakedb.Builder(id=8, name='other:builder', slug='other'),
            fakedb.Builder(id=9, name='third:builder', slug='third'),
            fakedb.Master(id=3, name='m1'),
            fakedb.Master(id=4, name='m2'),
            fakedb.BuilderMaster(builderid=7, masterid=3),
            fakedb.BuilderMaster(builderid=8, masterid=3),
            fakedb.BuilderMaster(builderid=8, masterid=4),
        ])
        builderlist = yield self.db.builders.getBuilders()
        for builderdict in builderlist:
            validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(sorted(builderlist), sorted([
            dict(id=7, name='some:builder', slug='some', masterids=[3],
                 tags=[], description=None),
            dict(id=8, name='other:builder', slug='other', masterids=[3, 4],
                 tags=[], description=None),
            dict(id=9, name='third:builder', slug='third', masterids=[],
                 tags=[], description=None),
        ]))

    @defer.inlineCallbacks
    def test_getBuilders_masterid(self):
        yield self.insertTestData([
            fakedb.Builder(id=7, name='some:builder', slug='some'),
            fakedb.Builder(id=8, name='other:builder', slug='other'),
            fakedb.Builder(id=9, name='third:builder', slug='third'),
            fakedb.Master(id=3, name='m1'),
            fakedb.Master(id=4, name='m2'),
            fakedb.BuilderMaster(builderid=7, masterid=3),
            fakedb.BuilderMaster(builderid=8, masterid=3),
            fakedb.BuilderMaster(builderid=8, masterid=4),
        ])
        builderlist = yield self.db.builders.getBuilders(masterid=3)
        for builderdict in builderlist:
            validation.verifyDbDict(self, 'builderdict', builderdict)
        self.assertEqual(sorted(builderlist), sorted([
            dict(id=7, name='some:builder', slug='some',
                 masterids=[3], tags=[], description=None),
            dict(id=8, name='other:builder', slug='other',
                 masterids=[3, 4], tags=[], description=None),
        ]))

    @defer.inlineCallbacks
    def test_getBuilders_empty(self):
        builderlist = yield self.db.builders.getBuilders()
        self.assertEqual(sorted(builderlist), [])


class RealTests(Tests):

    # tests that only "real" implementations will pass

    pass


class TestFakeDB(unittest.TestCase, Tests):

    def setUp(self):
        self.master = fakemaster.make_master(wantDb=True, testcase=self)
        self.db = self.master.db
        self.db.checkForeignKeys = True
        self.insertTestData = self.db.insertTestData


class TestRealDB(unittest.TestCase,
                 connector_component.ConnectorComponentMixin,
                 RealTests):

    def setUp(self):
        d = self.setUpConnectorComponent(
            table_names=['builders', 'masters', 'builder_masters',
                         'builders_tags', 'tags'])

        @d.addCallback
        def finish_setup(_):
            self.db.builders = builders.BuildersConnectorComponent(self.db)
            self.db.tags = tags.TagsConnectorComponent(self.db)
            self.master = self.db.master
            self.master.db = self.db

        return d

    def tearDown(self):
        return self.tearDownConnectorComponent()
