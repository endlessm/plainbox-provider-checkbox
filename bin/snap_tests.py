#!/usr/bin/env python3
# Copyright 2015-2019 Canonical Ltd.
# All rights reserved.
#
# Written by:
#    Authors: Jonathan Cave <jonathan.cave@canonical.com>

import os

from guacamole import Command
from checkbox_support.snap_utils.snapd import Snapd

# Requirements for the test snap:
#  - the snap must not be installed at the start of the nested test plan
#  - the snap must be strictly confined (no classic or devmode flags)
#  - there must be different revisions on the stable & edge channels
TEST_SNAP = os.getenv('TEST_SNAP', 'test-snapd-tools')
SNAPD_TASK_TIMEOUT = int(os.getenv('SNAPD_TASK_TIMEOUT', 30))
SNAPD_POLL_INTERVAL = int(os.getenv('SNAPD_POLL_INTERVAL', 1))


class SnapList(Command):

    """snap list sub-command."""

    def invoked(self, ctx):
        """snap list should show the core package is installed."""
        data = Snapd().list()
        for snap in data:
            if snap['name'] in ('core', 'core16', 'core18'):
                print("Found a core snap")
                print(snap['name'], snap['version'], snap['revision'])
                return 0
        return 1


class SnapSearch(Command):

    """snap search sub-command."""

    def invoked(self, ctx):
        """snap search for TEST_SNAP."""
        data = Snapd().find(TEST_SNAP,)
        for snap in data:
            print('ID:', snap['id'])
            print('Name:', snap['name'])
            print('Developer:', snap['developer'])
            return 0
        return 1


class SnapInstall(Command):

    """snap install sub-command."""

    def register_arguments(self, parser):
        """Setup command arguments."""
        parser.add_argument('channel', help='channel to install from')

    def invoked(self, ctx):
        """Test install of test-snapd-tools snap."""
        print('Install {}...'.format(TEST_SNAP))
        s = Snapd(SNAPD_TASK_TIMEOUT, SNAPD_POLL_INTERVAL)
        s.install(TEST_SNAP, ctx.args.channel)
        print('Confirm in snap list...')
        data = s.list()
        for snap in data:
            if snap['name'] == TEST_SNAP:
                return 0
        print(' not in snap list')
        return 1


class SnapRefresh(Command):

    """snap refresh sub-command."""

    def invoked(self, ctx):
        """Test refresh of test-snapd-tools snap."""
        def get_rev():
            data = Snapd().list()
            for snap in data:
                if snap['name'] == TEST_SNAP:
                    return snap['revision']
        print('Get starting revision...')
        start_rev = get_rev()
        print('  revision:', start_rev)
        print('Refresh to edge...')
        s = Snapd(SNAPD_TASK_TIMEOUT, SNAPD_POLL_INTERVAL)
        s.refresh(TEST_SNAP, 'edge')
        print('Get new revision...')
        new_rev = get_rev()
        print('  revision:', new_rev)
        if new_rev == start_rev:
            return 1
        return 0


class SnapRevert(Command):

    """snap revert sub-command."""

    def invoked(self, ctx):
        """Test revert of test-snapd-tools snap."""
        s = Snapd(SNAPD_TASK_TIMEOUT, SNAPD_POLL_INTERVAL)
        print('Get stable channel revision from store...')
        r = s.info(TEST_SNAP)
        stable_rev = r['channels']['latest/stable']['revision']
        print('Get current installed revision...')
        r = s.list(TEST_SNAP)
        installed_rev = r['revision']  # should be edge revision
        print('Reverting snap {}...'.format(TEST_SNAP))
        s.revert(TEST_SNAP)
        print('Get new installed revision...')
        r = s.list(TEST_SNAP)
        rev = r['revision']
        if rev != stable_rev:
            print("Not stable revision number")
            return 1
        if rev == installed_rev:
            print("Identical revision number")
            return 1
        return 0


class SnapReupdate(Command):

    """snap reupdate sub-command."""

    def invoked(self, ctx):
        """Test re-update of test-snapd-tools snap."""
        s = Snapd(SNAPD_TASK_TIMEOUT, SNAPD_POLL_INTERVAL)
        print('Get edge channel revision from store...')
        r = s.info(TEST_SNAP)
        edge_rev = r['channels']['latest/edge']['revision']
        print('Remove edge revision...')
        s.remove(TEST_SNAP, edge_rev)
        print('Refresh to edge channel...')
        s.refresh(TEST_SNAP, 'edge')
        print('Get new installed revision...')
        r = s.list(TEST_SNAP)
        rev = r['revision']
        if rev != edge_rev:
            print("Not edge revision number")
            return 1


class SnapRemove(Command):

    """snap remove sub-command."""

    def invoked(self, ctx):
        """Test remove of test-snapd-tools snap."""
        print('Install {}...'.format(TEST_SNAP))
        s = Snapd(SNAPD_TASK_TIMEOUT, SNAPD_POLL_INTERVAL)
        s.remove(TEST_SNAP)
        print('Check not in snap list')
        data = s.list()
        for snap in data:
            if snap['name'] == TEST_SNAP:
                print(' found in snap list')
                return 1
        return 0


class Snap(Command):

    """Fake snap like command."""

    sub_commands = (
        ('list', SnapList),
        ('search', SnapSearch),
        ('install', SnapInstall),
        ('refresh', SnapRefresh),
        ('revert', SnapRevert),
        ('reupdate', SnapReupdate),
        ('remove', SnapRemove)
    )


if __name__ == '__main__':
    Snap().main()
