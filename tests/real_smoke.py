#!/usr/bin/env python3
"""Run against real pinned skills CLI; all writes stay in a temporary home.

Optional SKILLS_REAL_INSTALLER is a JSON argv for an already inspected CLI.
Default downloads skills@1.7.0 into an isolated npm cache.
"""
import json
import os
import unittest
from test_sync import SyncCommands


class RealInstallerSmoke(SyncCommands):
    def setUp(self):
        super().setUp()
        self.env['SKILLS_SYNC_INSTALLER'] = os.environ.get('SKILLS_REAL_INSTALLER', json.dumps(['npx', '--yes', 'skills@1.7.0']))


if __name__ == '__main__':
    suite = unittest.TestSuite([RealInstallerSmoke('test_first_update_new_and_idempotent')])
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
