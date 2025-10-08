#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

# Simplified webserver for serving templates only
# All API calls are proxied to the new FastAPI client interface

import json
import logging
import os
import re
import time
from base64 import b64encode
from tornado import gen, web
from tornado.escape import url_escape, xhtml_escape
from tornado.template import Loader
from tornado.ioloop import IOLoop

from mod.profile import Profile
from mod.settings import (DESKTOP, LOG, DEV_API,
                          HTML_DIR, DEVICE_KEY, DEVICE_WEBSERVER_PORT,
                          CLOUD_HTTP_ADDRESS, CLOUD_LABS_HTTP_ADDRESS,
                          PLUGINS_HTTP_ADDRESS, PEDALBOARDS_HTTP_ADDRESS, CONTROLCHAIN_HTTP_ADDRESS,
                          DEFAULT_ICON_TEMPLATE, DEFAULT_SETTINGS_TEMPLATE,
                          DEFAULT_PEDALBOARD, UNTITLED_PEDALBOARD_NAME, IMAGE_VERSION,
                          PREFERENCES_JSON_FILE, USER_ID_JSON_FILE, FAVORITES_JSON_FILE,
                          LV2_PLUGIN_DIR, PEDALBOARDS_LABS_HTTP_ADDRESS)

from mod import (
    check_environment, safe_json_load,
    get_hardware_descriptor, os_sync,
)
from mod.session import SESSION
from modtools.utils import (
    init as lv2_init, cleanup as lv2_cleanup,
    get_pedalboard_info, get_jack_buffer_size, get_jack_sample_rate,
)

# Global webserver state
class GlobalWebServerState(object):
    __slots__ = ['favorites']

gState = GlobalWebServerState()
gState.favorites = []

def mod_squeeze(text):
    from tornado.escape import squeeze
    return squeeze(text.replace("\\", "\\\\").replace("'", "\\'"))

# Base classes for templating
class TimelessRequestHandler(web.RequestHandler):
    def compute_etag(self):
        return None

    def set_default_headers(self):
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")

class TimelessStaticFileHandler(web.StaticFileHandler):
    def compute_etag(self):
        return None

    def set_default_headers(self):
        web.StaticFileHandler.set_default_headers(self)
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")

# Template serving (the only server functionality we need to keep)
class TemplateHandler(TimelessRequestHandler):
    @gen.coroutine
    def get(self, path):
        # Caching strategy
        curVersion = self.get_version()
        try:
            version = url_escape(self.get_argument('v'))
        except web.MissingArgumentError:
            uri  = self.request.uri
            uri += '&' if self.request.query else '?'
            uri += 'v=%s' % curVersion
            self.redirect(uri)
            return
            
        if IMAGE_VERSION is not None and version != curVersion:
            uri = self.request.uri.replace('v=%s' % version, 'v=%s' % curVersion)
            self.redirect(uri)
            return

        if not path:
            path = 'index.html'
        elif path == 'sdk':
            self.redirect(self.request.full_url().replace("/sdk", ":9000"), True)
            return
        elif path == 'allguis':
            uri = '/allguis.html?v=%s' % curVersion
            self.redirect(uri, True)
            return
        elif path == 'settings':
            uri = '/settings.html?v=%s' % curVersion
            self.redirect(uri, True)
            return
        elif not os.path.exists(os.path.join(HTML_DIR, path)):
            uri = '/?v=%s' % curVersion
            self.redirect(uri)
            return

        loader = Loader(HTML_DIR)
        section = path.split('.',1)[0]

        if section == 'index':
            yield gen.Task(SESSION.wait_for_hardware_if_needed)

        try:
            context = getattr(self, section)()
        except AttributeError:
            context = {}
        self.write(loader.load(path).generate(**context))

    def get_version(self):
        if IMAGE_VERSION is not None and len(IMAGE_VERSION) > 1:
            version = IMAGE_VERSION[1:] if IMAGE_VERSION[0] == "v" else IMAGE_VERSION
            return url_escape(version)
        return str(int(time.time()))

    def index(self):
        user_id = safe_json_load(USER_ID_JSON_FILE, dict)

        with open(DEFAULT_ICON_TEMPLATE, 'r') as fh:
            default_icon_template = mod_squeeze(fh.read())

        with open(DEFAULT_SETTINGS_TEMPLATE, 'r') as fh:
            default_settings_template = mod_squeeze(fh.read())

        pbname = SESSION.host.pedalboard_name
        prname = SESSION.host.snapshot_name()

        fullpbname = pbname or UNTITLED_PEDALBOARD_NAME
        if prname:
            fullpbname += " - " + prname

        hwdesc = get_hardware_descriptor()

        context = {
            'default_icon_template': default_icon_template,
            'default_settings_template': default_settings_template,
            'default_pedalboard': mod_squeeze(DEFAULT_PEDALBOARD),
            'cloud_url': CLOUD_HTTP_ADDRESS,
            'cloud_labs_url': CLOUD_LABS_HTTP_ADDRESS,
            'plugins_url': PLUGINS_HTTP_ADDRESS,
            'pedalboards_url': PEDALBOARDS_HTTP_ADDRESS,
            'pedalboards_labs_url': PEDALBOARDS_LABS_HTTP_ADDRESS,
            'controlchain_url': CONTROLCHAIN_HTTP_ADDRESS,
            'hardware_profile': b64encode(json.dumps(SESSION.get_hardware_actuators()).encode("utf-8")),
            'version': self.get_argument('v'),
            'bin_compat': hwdesc.get('bin-compat', "Unknown"),
            'codec_truebypass': 'true' if hwdesc.get('codec_truebypass', False) else 'false',
            'factory_pedalboards': hwdesc.get('factory_pedalboards', False),
            'platform': hwdesc.get('platform', "Unknown"),
            'addressing_pages': int(hwdesc.get('addressing_pages', 0)),
            'lv2_plugin_dir': mod_squeeze(LV2_PLUGIN_DIR),
            'bundlepath': mod_squeeze(SESSION.host.pedalboard_path),
            'title':  mod_squeeze(pbname),
            'size': json.dumps(SESSION.host.pedalboard_size),
            'fulltitle':  xhtml_escape(fullpbname),
            'titleblend': '' if SESSION.host.pedalboard_name else 'blend',
            'dev_api_class': 'dev_api' if DEV_API else '',
            'using_desktop': 'true' if DESKTOP else 'false',
            'using_mod': 'true' if DEVICE_KEY and hwdesc.get('platform', None) is not None else 'false',
            'user_name': mod_squeeze(user_id.get("name", "")),
            'user_email': mod_squeeze(user_id.get("email", "")),
            'favorites': json.dumps(gState.favorites),
            'preferences': json.dumps(SESSION.prefs.prefs),
            'bufferSize': get_jack_buffer_size(),
            'sampleRate': get_jack_sample_rate(),
        }
        return context

    def pedalboard(self):
        bundlepath = self.get_argument('bundlepath')

        with open(DEFAULT_ICON_TEMPLATE, 'r') as fh:
            default_icon_template = mod_squeeze(fh.read())

        with open(DEFAULT_SETTINGS_TEMPLATE, 'r') as fh:
            default_settings_template = mod_squeeze(fh.read())

        try:
            pedalboard = get_pedalboard_info(bundlepath)
        except:
            print("ERROR: get_pedalboard_info failed")
            pedalboard = {
                'height': 0,
                'width': 0,
                'title': "",
                'connections': [],
                'plugins': [],
                'hardware': {},
            }

        context = {
            'default_icon_template': default_icon_template,
            'default_settings_template': default_settings_template,
            'pedalboard': b64encode(json.dumps(pedalboard).encode("utf-8"))
        }
        return context

    def allguis(self):
        return {'version': self.get_argument('v')}

    def settings(self):
        hwdesc = get_hardware_descriptor()
        prefs = safe_json_load(PREFERENCES_JSON_FILE, dict)

        context = {
            'cloud_url': CLOUD_HTTP_ADDRESS,
            'controlchain_url': CONTROLCHAIN_HTTP_ADDRESS,
            'version': self.get_argument('v'),
            'hmi_eeprom': 'true' if hwdesc.get('hmi_eeprom', False) else 'false',
            'preferences': json.dumps(prefs),
            'bufferSize': get_jack_buffer_size(),
            'sampleRate': get_jack_sample_rate(),
        }
        return context

class TemplateLoader(TimelessRequestHandler):
    def get(self, path):
        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        with open(os.path.join(HTML_DIR, 'include', path), 'r') as fh:
            self.write(fh.read())
        self.finish()

class BulkTemplateLoader(TimelessRequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/javascript; charset=UTF-8")
        basedir = os.path.join(HTML_DIR, 'include')
        for template in os.listdir(basedir):
            if not re.match('^[a-z_]+\.html$', template):
                continue
            with open(os.path.join(basedir, template), 'r') as fh:
                contents = fh.read()
            self.write("TEMPLATES['%s'] = '%s';\n\n"
                       % (template[:-5], mod_squeeze(contents)))
        self.finish()

    def set_default_headers(self):
        TimelessRequestHandler.set_default_headers(self)
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.set_header("Expires", "Mon, 31 Dec 2035 12:00:00 gmt")

# Simple application with only templating support
def create_application():
    settings = {'log_function': lambda handler: None} if not LOG else {}
    
    return web.Application([
        # Template serving (only functionality we keep)
        (r"/(index.html)?$", TemplateHandler),
        (r"/([a-z]+\.html)$", TemplateHandler),
        (r"/(allguis|sdk|settings)$", TemplateHandler),
        (r"/load_template/([a-z_]+\.html)$", TemplateLoader),
        (r"/js/templates.js$", BulkTemplateLoader),
        
        # Static file serving (CSS, JS, images, etc.)
        (r"/(.*)", TimelessStaticFileHandler, {"path": HTML_DIR}),
    ], debug=bool(LOG >= 2), **settings)

def prepare():
    """Initialize the template server"""
    check_environment()
    lv2_init()
    
    # Load favorites for template context
    gState.favorites = safe_json_load(FAVORITES_JSON_FILE, list)
    
    return True

def run():
    """Start the template server"""
    if not prepare():
        print("ERROR: Failed to prepare template server")
        return False
        
    application = create_application()
    application.listen(DEVICE_WEBSERVER_PORT)
    
    print("Template server running on port %d" % DEVICE_WEBSERVER_PORT)
    print("All API calls will be proxied to the FastAPI client interface")
    
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("Template server stopped")
        lv2_cleanup()
        return True

if __name__ == '__main__':
    run()