#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG  
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Minimal session object for template rendering only"""

from mod.settings import PREFERENCES_JSON_FILE, DEFAULT_SNAPSHOT_NAME, UNTITLED_PEDALBOARD_NAME
from mod import safe_json_load

class MockPreferences:
    """Mock preferences object"""
    def __init__(self):
        self.prefs = safe_json_load(PREFERENCES_JSON_FILE, dict)
    
    def get(self, key, default, type_=None, values=None):
        return self.prefs.get(key, default)

class MockHost:
    """Mock host object with minimal properties for templates"""
    def __init__(self):
        self.pedalboard_name = UNTITLED_PEDALBOARD_NAME
        self.pedalboard_path = "/tmp/default.pedalboard" 
        self.pedalboard_size = [0, 0]
    
    def snapshot_name(self):
        return DEFAULT_SNAPSHOT_NAME

class MockSession:
    """Mock session object providing minimal functionality for template rendering"""
    
    def __init__(self):
        self.prefs = MockPreferences()
        self.host = MockHost()
    
    def wait_for_hardware_if_needed(self, callback=None):
        """Mock method - immediately call callback"""
        if callback:
            callback(True)
        return True
    
    def get_hardware_actuators(self):
        """Mock method - return empty actuators list"""
        return []

# Global mock session instance
SESSION = MockSession()