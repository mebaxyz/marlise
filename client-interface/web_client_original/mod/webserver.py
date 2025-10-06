#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import re
import sys
import time
from base64 import b64encode
from tornado import gen, web, websocket
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.escape import url_escape, xhtml_escape
from tornado.ioloop import IOLoop
from tornado.template import Loader

from mod.settings import (DESKTOP, LOG, HTML_DIR, DEVICE_WEBSERVER_PORT,
                          CLOUD_HTTP_ADDRESS, CLOUD_LABS_HTTP_ADDRESS,
                          PLUGINS_HTTP_ADDRESS, PEDALBOARDS_HTTP_ADDRESS, CONTROLCHAIN_HTTP_ADDRESS,
                          LV2_PLUGIN_DIR, IMAGE_VERSION,
                          DEFAULT_ICON_TEMPLATE, DEFAULT_SETTINGS_TEMPLATE,
                          DEFAULT_PEDALBOARD, UNTITLED_PEDALBOARD_NAME,
                          FAVORITES_JSON_FILE, PREFERENCES_JSON_FILE, USER_ID_JSON_FILE,
                          PEDALBOARDS_LABS_HTTP_ADDRESS, DEV_API, DEVICE_KEY)

# Minimal utility functions
def safe_json_load(path, objtype):
    if not os.path.exists(path):
        return objtype()
    try:
        with open(path, 'r') as fh:
            data = json.load(fh)
    except:
        return objtype()
    if not isinstance(data, objtype):
        return objtype()
    return data

def mod_squeeze(text):
    return text.replace("\\", "\\\\").replace("'", "\\'")

def check_environment():
    """Minimal environment check - just ensure we can start the webserver"""
    return True

# Environment variable to configure backend
BACKEND_URL = os.environ.get('MOD_PROXY_BACKEND', 'http://127.0.0.1:8080')
BACKEND_WS_URL = os.environ.get('MOD_PROXY_BACKEND_WS', 'ws://127.0.0.1:8080')

class TimelessRequestHandler(web.RequestHandler):
    def compute_etag(self):
        return None

    def set_default_headers(self):
        self._headers.pop("Date", None)

    def should_return_304(self):
        return False

class TimelessStaticFileHandler(web.StaticFileHandler):
    def compute_etag(self):
        return None

    def set_default_headers(self):
        self._headers.pop("Date", None)
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.set_header("Expires", "Mon, 31 Dec 2035 12:00:00 gmt")

    def should_return_304(self):
        return False

    def get_cache_time(self, path, modified, mime_type):
        return 0

    def get_modified_time(self):
        return None

class TemplateHandler(TimelessRequestHandler):
    @gen.coroutine
    def get(self, path):
        # Caching strategy.
        # 1. If we don't have a version parameter, redirect
        curVersion = self.get_version()
        try:
            version = url_escape(self.get_argument('v'))
        except web.MissingArgumentError:
            uri  = self.request.uri
            uri += '&' if self.request.query else '?'
            uri += 'v=%s' % curVersion
            self.redirect(uri)
            return
        # 2. Make sure version is correct
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

        try:
            context = yield gen.Task(getattr(self, section))
        except AttributeError:
            context = {}
        self.write(loader.load(path).generate(**context))

    def get_version(self):
        if IMAGE_VERSION is not None and len(IMAGE_VERSION) > 1:
            # strip initial 'v' from version if present
            version = IMAGE_VERSION[1:] if IMAGE_VERSION[0] == "v" else IMAGE_VERSION
            return url_escape(version)
        return str(int(time.time()))

    @gen.coroutine
    def index(self):
        user_id = safe_json_load(USER_ID_JSON_FILE, dict)

        with open(DEFAULT_ICON_TEMPLATE, 'r') as fh:
            default_icon_template = mod_squeeze(fh.read())

        with open(DEFAULT_SETTINGS_TEMPLATE, 'r') as fh:
            default_settings_template = mod_squeeze(fh.read())

        # Get current session state, favorites, and preferences from backend API
        try:
            client = AsyncHTTPClient()
            
            # Get session state
            req = HTTPRequest(BACKEND_URL + "/api/session/state", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            session_data = json.loads(resp.body.decode('utf-8'))
            
            pbname = session_data.get('pedalboard_name', '')
            prname = session_data.get('snapshot_name', '')
            bundlepath = session_data.get('pedalboard_path', '')
            pedalboard_size = session_data.get('pedalboard_size', {'width': 800, 'height': 600})
            hardware_profile = session_data.get('hardware_profile', [])
            
            # Get favorites
            req = HTTPRequest(BACKEND_URL + "/api/user/favorites", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            favorites_data = json.loads(resp.body.decode('utf-8'))
            favorites = favorites_data.get('favorites', [])
            
            # Get preferences  
            req = HTTPRequest(BACKEND_URL + "/api/user/preferences", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            preferences_data = json.loads(resp.body.decode('utf-8'))
            preferences = preferences_data.get('preferences', {})
            
            # Get hardware info and audio settings
            req = HTTPRequest(BACKEND_URL + "/api/system/hardware", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            hwdesc = json.loads(resp.body.decode('utf-8'))
            
            req = HTTPRequest(BACKEND_URL + "/api/audio/settings", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            audio_settings = json.loads(resp.body.decode('utf-8'))
            
        except Exception as e:
            print(f"Failed to get data from backend: {e}")
            # Fallback to defaults
            pbname = ''
            prname = ''
            bundlepath = ''
            pedalboard_size = {'width': 800, 'height': 600}
            hardware_profile = []
            favorites = []
            preferences = {}
            hwdesc = {}
            audio_settings = {'bufferSize': 256, 'sampleRate': 48000}

        fullpbname = pbname or UNTITLED_PEDALBOARD_NAME
        if prname:
            fullpbname += " - " + prname

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
            'hardware_profile': b64encode(json.dumps(hardware_profile).encode("utf-8")),
            'version': self.get_argument('v'),
            'bin_compat': hwdesc.get('bin-compat', "Unknown"),
            'codec_truebypass': 'true' if hwdesc.get('codec_truebypass', False) else 'false',
            'factory_pedalboards': hwdesc.get('factory_pedalboards', False),
            'platform': hwdesc.get('platform', "Unknown"),
            'addressing_pages': int(hwdesc.get('addressing_pages', 0)),
            'lv2_plugin_dir': mod_squeeze(LV2_PLUGIN_DIR),
            'bundlepath': mod_squeeze(bundlepath),
            'title':  mod_squeeze(pbname),
            'size': json.dumps(pedalboard_size),
            'fulltitle':  xhtml_escape(fullpbname),
            'titleblend': '' if pbname else 'blend',
            'dev_api_class': 'dev_api' if DEV_API else '',
            'using_desktop': 'true' if DESKTOP else 'false',
            'using_mod': 'true' if DEVICE_KEY and hwdesc.get('platform', None) is not None else 'false',
            'user_name': mod_squeeze(user_id.get("name", "")),
            'user_email': mod_squeeze(user_id.get("email", "")),
            'favorites': json.dumps(favorites),
            'preferences': json.dumps(preferences),
            'bufferSize': audio_settings.get('bufferSize', 256),
            'sampleRate': audio_settings.get('sampleRate', 48000),
        }
        return context

    @gen.coroutine
    def pedalboard(self):
        bundlepath = self.get_argument('bundlepath')

        with open(DEFAULT_ICON_TEMPLATE, 'r') as fh:
            default_icon_template = mod_squeeze(fh.read())

        with open(DEFAULT_SETTINGS_TEMPLATE, 'r') as fh:
            default_settings_template = mod_squeeze(fh.read())

        # Get pedalboard info from backend API
        try:
            client = AsyncHTTPClient()
            encoded_bundlepath = url_escape(bundlepath)
            req = HTTPRequest(BACKEND_URL + f"/api/pedalboard/info?bundlepath={encoded_bundlepath}", 
                             method="GET", request_timeout=10)
            resp = yield client.fetch(req)
            pedalboard = json.loads(resp.body.decode('utf-8'))
            
        except Exception as e:
            print(f"Failed to get pedalboard info from backend: {e}")
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

    @gen.coroutine
    def allguis(self):
        # Get all available plugin GUIs from backend API
        try:
            client = AsyncHTTPClient()
            req = HTTPRequest(BACKEND_URL + "/api/plugins/guis", method="GET", request_timeout=10)
            resp = yield client.fetch(req)
            plugins_data = json.loads(resp.body.decode('utf-8'))
            
        except Exception as e:
            print(f"Failed to get plugin GUIs from backend: {e}")
            plugins_data = {}

        context = {
            'version': self.get_argument('v'),
            'plugins': json.dumps(plugins_data),
        }
        return context

    @gen.coroutine
    def settings(self):
        # Get hardware info, preferences, and audio settings from backend API
        try:
            client = AsyncHTTPClient()
            
            # Get hardware descriptor
            req = HTTPRequest(BACKEND_URL + "/api/system/hardware", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            hwdesc = json.loads(resp.body.decode('utf-8'))
            
            # Get preferences  
            req = HTTPRequest(BACKEND_URL + "/api/user/preferences", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            preferences_data = json.loads(resp.body.decode('utf-8'))
            prefs = preferences_data.get('preferences', {})
            
            # Get audio settings
            req = HTTPRequest(BACKEND_URL + "/api/audio/settings", method="GET", request_timeout=5)
            resp = yield client.fetch(req)
            audio_settings = json.loads(resp.body.decode('utf-8'))
            
        except Exception as e:
            print(f"Failed to get settings data from backend: {e}")
            hwdesc = {}
            prefs = {}
            audio_settings = {'bufferSize': 256, 'sampleRate': 48000}

        context = {
            'cloud_url': CLOUD_HTTP_ADDRESS,
            'controlchain_url': CONTROLCHAIN_HTTP_ADDRESS,
            'version': self.get_argument('v'),
            'hmi_eeprom': 'true' if hwdesc.get('hmi_eeprom', False) else 'false',
            'preferences': json.dumps(prefs),
            'bufferSize': audio_settings.get('bufferSize', 256),
            'sampleRate': audio_settings.get('sampleRate', 48000),
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
            if not re.match(r'^[a-z_]+\.html$', template):
                continue
            with open(os.path.join(basedir, template), 'r') as fh:
                contents = fh.read()
            self.write("TEMPLATES['%s'] = '%s';\n\n"
                       % (template[:-5],
                          mod_squeeze(contents)
                          )
                       )
        self.finish()

    def set_default_headers(self):
        TimelessRequestHandler.set_default_headers(self)
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.set_header("Expires", "Mon, 31 Dec 2035 12:00:00 gmt")

class ProxyHandler(TimelessRequestHandler):
    """Proxy HTTP requests to a backend service."""

    HOP_BY_HOP_HEADERS = set([
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade'
    ])

    @gen.coroutine
    def _proxy(self):
        backend = BACKEND_URL
        url = backend.rstrip('/') + self.request.uri

        # Forward most headers but strip hop-by-hop headers and host
        headers = {}
        for k, v in self.request.headers.items():
            if k.lower() in self.HOP_BY_HOP_HEADERS or k.lower() == 'host':
                continue
            headers[k] = v

        body = self.request.body if self.request.body else None

        client = AsyncHTTPClient()
        req = HTTPRequest(url, method=self.request.method, headers=headers, body=body,
                          follow_redirects=False, request_timeout=60)
        try:
            resp = yield client.fetch(req, raise_error=False)
        except Exception as e:
            self.set_status(502)
            self.write({'ok': False, 'error': str(e)})
            return

        # Copy response status and headers
        self.set_status(resp.code)
        for k, v in resp.headers.items():
            if k.lower() in self.HOP_BY_HOP_HEADERS or k.lower() in ('content-encoding',):
                continue
            if k.lower() == 'content-length':
                continue
            self.set_header(k, v)

        if resp.body:
            try:
                self.write(resp.body)
            except Exception:
                try:
                    self.write(resp.body.decode('utf-8', errors='ignore'))
                except Exception:
                    pass

        self.finish()

    def get(self, path=''):
        return self._proxy()

    def post(self, path=''):
        return self._proxy()

    def put(self, path=''):
        return self._proxy()

    def delete(self, path=''):
        return self._proxy()

    def patch(self, path=''):
        return self._proxy()

    def options(self, path=''):
        return self._proxy()

class WebSocketProxy(websocket.WebSocketHandler):
    """WebSocket proxy that forwards messages to the new backend."""
    
    def initialize(self, backend_path=""):
        self.backend_path = backend_path
        self.backend_ws = None
    
    def check_origin(self, origin):
        return True
    
    @gen.coroutine
    def open(self):
        """Connect to backend WebSocket when client connects."""
        backend_ws_url = BACKEND_WS_URL.rstrip('/') + self.backend_path
        
        try:
            from tornado.websocket import websocket_connect
            self.backend_ws = yield websocket_connect(backend_ws_url)
            if self.backend_ws:
                IOLoop.current().spawn_callback(self._listen_backend)
        except Exception as e:
            print(f"Failed to connect to backend WebSocket {backend_ws_url}: {e}")
            self.close()
            return
    
    @gen.coroutine
    def _listen_backend(self):
        """Listen for messages from backend and forward to client."""
        try:
            while True:
                message = yield self.backend_ws.read_message()
                if message is None:
                    break
                self.write_message(message)
        except Exception as e:
            print(f"Backend WebSocket error: {e}")
        finally:
            if not self._closed:
                self.close()
    
    def on_message(self, message):
        """Forward message from client to backend."""
        if self.backend_ws and not self.backend_ws.protocol.closed:
            self.backend_ws.write_message(message)
    
    def on_close(self):
        """Close backend connection when client disconnects."""
        if self.backend_ws and not self.backend_ws.protocol.closed:
            self.backend_ws.close()

# Application configuration
settings = {'log_function': lambda handler: None} if not LOG else {}

application = web.Application([
        # Template handlers (keep original templating functionality)
        (r"/(index.html)?$", TemplateHandler),
        (r"/([a-z]+\.html)$", TemplateHandler), 
        (r"/(allguis|sdk|settings)$", TemplateHandler),
        (r"/load_template/([a-z_]+\.html)$", TemplateLoader),
        (r"/js/templates.js$", BulkTemplateLoader),

        # WebSocket proxies - forward to external API
        (r"/websocket/?$", WebSocketProxy, {"backend_path": "/websocket"}),
        (r"/rpbsocket/?$", WebSocketProxy, {"backend_path": "/rpbsocket"}), 
        (r"/rplsocket/?$", WebSocketProxy, {"backend_path": "/rplsocket"}),
        (r"/ws/?$", WebSocketProxy, {"backend_path": "/ws"}),

        # API proxies - forward all API endpoints to external API
        (r"/api/(.*)", ProxyHandler),
        (r"/system/(.*)", ProxyHandler),
        (r"/effect/(.*)", ProxyHandler),
        (r"/pedalboard/(.*)", ProxyHandler),
        (r"/snapshot/(.*)", ProxyHandler),
        (r"/banks?(.*)", ProxyHandler),
        (r"/controlchain/(.*)", ProxyHandler),
        (r"/update/(.*)", ProxyHandler),
        (r"/package/(.*)", ProxyHandler),
        (r"/recording/(.*)", ProxyHandler),
        (r"/auth/(.*)", ProxyHandler),
        (r"/tokens/(.*)", ProxyHandler),
        (r"/files/(.*)", ProxyHandler),
        (r"/reset/?", ProxyHandler),
        (r"/sdk/(.*)", ProxyHandler),
        (r"/jack/(.*)", ProxyHandler),
        (r"/favorites/(.*)", ProxyHandler),
        (r"/config/(.*)", ProxyHandler),
        (r"/ping/?", ProxyHandler),
        (r"/hello/?", ProxyHandler),
        (r"/truebypass/(.*)", ProxyHandler),
        (r"/set_buffersize/(.*)", ProxyHandler),
        (r"/reset_xruns/?", ProxyHandler),
        (r"/switch_cpu_freq/?", ProxyHandler),
        (r"/save_user_id/?", ProxyHandler),
        (r"/resources/(.*)", ProxyHandler),

        # Static file handler (must be last)
        (r"/(.*)", TimelessStaticFileHandler, {"path": HTML_DIR}),
    ],
        debug = bool(LOG >= 2), **settings)

def prepare():
    """Minimal preparation - just check environment"""
    check_environment()
    application.listen(DEVICE_WEBSERVER_PORT, address=("127.0.0.1" if DESKTOP else "0.0.0.0"))

def start():
    IOLoop.instance().start()

def stop():
    IOLoop.instance().stop()

def run():
    prepare()
    start()

if __name__ == "__main__":
    run()