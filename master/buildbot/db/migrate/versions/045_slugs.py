# This file is part of Buildbot. Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import sqlalchemy as sa


def upgrade(migrate_engine):
    metadata = sa.MetaData()
    metadata.bind = migrate_engine

    builders = sa.Table('builders', metadata, autoload=True)
    builders.drop()

    schedulers = sa.Table('schedulers', metadata, autoload=True)
    schedulers.drop()

    changesources = sa.Table('changesources', metadata, autoload=True)
    changesources.drop()

    tags = sa.Table('tags', metadata, autoload=True)
    tags.drop()

    # regenerate metadata
    metadata = sa.MetaData()
    metadata.bind = migrate_engine

    builders = sa.Table(
        'builders', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('slug', sa.String(20), nullable=False),
    )
    builders.create()

    idx = sa.Index('builder_slug', builders.c.slug, unique=True)
    idx.create(migrate_engine)

    schedulers = sa.Table(
        'schedulers', metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
    )
    schedulers.create()

    idx = sa.Index('scheduler_name', schedulers.c.name, unique=True)
    idx.create(migrate_engine)

    changesources = sa.Table(
        'changesources', metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False),
    )
    changesources.create()

    idx = sa.Index('changesource_name', changesources.c.name, unique=True)
    idx.create()

    tags = sa.Table(
        'tags', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
    )
    tags.create()

    idx = sa.Index('tag_name', tags.c.name, unique=True)
    idx.create()
