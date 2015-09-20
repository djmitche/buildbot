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

from buildbot.data import base
from buildbot.data import types
from twisted.internet import defer


class BuilderEndpoint(base.Endpoint):

    isCollection = False
    pathPatterns = """
        /builders/n:builderid
        /masters/n:masterid/builders/n:builderid
    """

    @defer.inlineCallbacks
    def get(self, resultSpec, kwargs):
        builderid = kwargs['builderid']
        bdict = yield self.master.db.builders.getBuilder(builderid)
        if not bdict:
            defer.returnValue(None)
            return
        if 'masterid' in kwargs:
            if kwargs['masterid'] not in bdict['masterids']:
                defer.returnValue(None)
                return
        defer.returnValue(
            dict(builderid=builderid,
                 name=bdict['name'],
                 slug=bdict['slug'],
                 description=bdict['description'],
                 tags=bdict['tags']))


class BuildersEndpoint(base.Endpoint):

    isCollection = True
    rootLinkName = 'builders'
    pathPatterns = """
        /builders
        /masters/n:masterid/builders
    """

    @defer.inlineCallbacks
    def get(self, resultSpec, kwargs):
        bdicts = yield self.master.db.builders.getBuilders(
            masterid=kwargs.get('masterid', None))
        defer.returnValue([
            dict(builderid=bd['id'],
                 name=bd['name'],
                 slug=bd['slug'],
                 description=bd['description'],
                 tags=bd['tags'])
            for bd in bdicts])


class Builder(base.ResourceType):

    name = "builder"
    plural = "builders"
    endpoints = [BuilderEndpoint, BuildersEndpoint]
    keyFields = ['builderid']

    class EntityType(types.Entity):
        builderid = types.Integer()
        name = types.String()
        slug = types.Identifier(20)
        description = types.NoneOk(types.String())
        tags = types.List(of=types.String())
    entityType = EntityType(name)

    def __init__(self, master):
        base.ResourceType.__init__(self, master)

    @base.updateMethod
    def findBuilderId(self, slug):
        return self.master.db.builders.findBuilderId(slug)

    @base.updateMethod
    def updateBuilderInfo(self, builderid, name, description, tags):
        return self.master.db.builders.updateBuilderInfo(
            builderid, name, description, tags)

    @base.updateMethod
    @defer.inlineCallbacks
    def updateBuilderList(self, masterid, builderSlugs):
        # get the "current" list of builders for this master, so we know what
        # changes to make.  Race conditions here aren't a great worry, as this
        # is the only master inserting or deleting these records.
        builders = yield self.master.db.builders.getBuilders(masterid=masterid)

        # figure out what to remove and remove it
        builderSlugs = set(builderSlugs)
        for bldr in builders:
            if bldr['slug'] not in builderSlugs:
                builderid = bldr['id']
                yield self.master.db.builders.removeBuilderMaster(
                    masterid=masterid, builderid=builderid)
                self.master.mq.produce(('builders', str(builderid), 'stopped'),
                                       dict(builderid=builderid, masterid=masterid,
                                            name=bldr['name'], slug=bldr['slug']))
            else:
                builderSlugs.remove(bldr['slug'])

        # now whatever's left in builderSlugs is new
        for slug in builderSlugs:
            builderid = yield self.master.db.builders.findBuilderId(slug)
            yield self.master.db.builders.addBuilderMaster(
                masterid=masterid, builderid=builderid)
            bldr = yield self.master.db.builders.getBuilder(builderid)
            self.master.mq.produce(('builders', str(builderid), 'started'),
                                   dict(builderid=builderid, masterid=masterid,
                                        slug=slug, name=bldr['name']))

    @defer.inlineCallbacks
    def _masterDeactivated(self, masterid):
        # called from the masters rtype to indicate that the given master is
        # deactivated
        yield self.updateBuilderList(masterid, [])
