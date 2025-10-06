#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Streamlined Tornado webserver for MOD Audio - Templating and Proxy Only

This version keeps only:
- Static file serving
- Template rendering (index.html, settings.html, etc.)
- HTTP and WebSocket proxying to the new backend
All other API endpoints are proxied to the new client API.
"""

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
from tornado.websocket import websocket_connect

try:
    from signal import signal, SIGUSR1, SIGUSR2
    haveSignal = True
except ImportError:
    haveSignal = False

from mod.settings import (DESKTOP, LOG, HTML_DIR, DEVICE_WEBSERVER_PORT,
                          CLOUD_HTTP_ADDRESS, CLOUD_LABS_HTTP_ADDRESS,
                          PLUGINS_HTTP_ADDRESS, PEDALBOARDS_HTTP_ADDRESS, CONTROLCHAIN_HTTP_ADDRESS,
                          LV2_PLUGIN_DIR, IMAGE_VERSION,
                          DEFAULT_ICON_TEMPLATE, DEFAULT_SETTINGS_TEMPLATE,
                          DEFAULT_PEDALBOARD, UNTITLED_PEDALBOARD_NAME,
                          FAVORITES_JSON_FILE, PREFERENCES_JSON_FILE, USER_ID_JSON_FILE,
                          PEDALBOARDS_LABS_HTTP_ADDRESS)

from mod import (
    safe_json_load,
    get_hardware_descriptor,
)
from mod.session import SESSION

# Environment variable to configure backend
BACKEND_URL = os.environ.get('MOD_PROXY_BACKEND', 'http://127.0.0.1:8080')
BACKEND_WS_URL = os.environ.get('MOD_PROXY_BACKEND_WS', 'ws://127.0.0.1:8080')

def mod_squeeze(s):
    """Helper to remove newlines and extra whitespace from templates."""
    return re.sub(r'\s+', ' ', s.strip())

class TimelessRequestHandler(web.RequestHandler):
    """Base handler with proper caching headers."""
    
    def set_default_headers(self):
        # Allow CORS for all origins in development
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        # Prevent caching by default
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")

class TimelessStaticFileHandler(web.StaticFileHandler):
    """Static file handler with proper headers."""
    
    def set_default_headers(self):
        TimelessRequestHandler.set_default_headers(self)

class ProxyHandler(TimelessRequestHandler):
    """HTTP proxy handler that forwards requests to the new backend."""
    
    HOP_BY_HOP_HEADERS = {
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade'
    }
    
    @gen.coroutine
    def _proxy_request(self):
        """Forward HTTP request to backend."""
        backend_url = BACKEND_URL.rstrip('/') + self.request.uri
        
        # Prepare headers
        headers = {}
        for name, value in self.request.headers.items():
            if name.lower() not in self.HOP_BY_HOP_HEADERS and name.lower() != 'host':
                headers[name] = value
        
        # Prepare body
        body = self.request.body if self.request.body else None
        
        # Create request
        req = HTTPRequest(
            backend_url,
            method=self.request.method,
            headers=headers,
            body=body,
            follow_redirects=False,
            request_timeout=30
        )
        
        client = AsyncHTTPClient()
        try:
            response = yield client.fetch(req, raise_error=False)
            
            # Set response status
            self.set_status(response.code)
            
            # Copy response headers (skip problematic ones)
            for name, value in response.headers.items():
                if (name.lower() not in self.HOP_BY_HOP_HEADERS and 
                    name.lower() not in {'content-encoding', 'content-length'}):
                    self.set_header(name, value)
            
            # Write response body
            if response.body:
                self.write(response.body)
                
        except Exception as e:
            self.set_status(502)
            self.write({'error': 'Backend unavailable', 'details': str(e)})
        
        self.finish()
    
    def get(self, path=''):
        return self._proxy_request()
    
    def post(self, path=''):
        return self._proxy_request()
    
    def put(self, path=''):
        return self._proxy_request()
    
    def delete(self, path=''):
        return self._proxy_request()
    
    def patch(self, path=''):
        return self._proxy_request()
    
    def options(self, path=''):
        return self._proxy_request()

class WebSocketProxy(websocket.WebSocketHandler):
    """WebSocket proxy that forwards messages to the new backend."""
    
    def initialize(self, backend_path=""):
        self.backend_path = backend_path
        self.backend_ws = None
    
    def check_origin(self, origin):
        # Allow all origins in development
        return True
    
    @gen.coroutine
    def open(self):
        """Connect to backend WebSocket when client connects."""
        backend_ws_url = BACKEND_WS_URL.rstrip('/') + self.backend_path
        
        try:
            self.backend_ws = yield websocket_connect(backend_ws_url)
            self.backend_ws.on_message = self._on_backend_message
        except Exception as e:
            print(f"Failed to connect to backend WebSocket {backend_ws_url}: {e}")
            self.close()
            return
    
    def on_message(self, message):
        """Forward message from client to backend."""
        if self.backend_ws:
            self.backend_ws.write_message(message)
    
    def _on_backend_message(self, message):
        """Forward message from backend to client."""
        if message is not None:
            self.write_message(message)
    
    def on_close(self):
        """Close backend connection when client disconnects."""
        if self.backend_ws:
            self.backend_ws.close()

class TemplateHandler(TimelessRequestHandler):
    """Handler for rendering HTML templates."""
    
    @gen.coroutine
    def get(self, path):
        # Caching strategy - redirect if no version parameter
        curVersion = self.get_version()
        try:
            version = url_escape(self.get_argument('v'))
        except web.MissingArgumentError:
            uri = self.request.uri
            uri += '&' if self.request.query else '?'
            uri += 'v=%s' % curVersion
            self.redirect(uri)
            return
        
        # Make sure version is correct
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
        section = path.split('.', 1)[0]
        
        if section == 'index':
            yield gen.Task(SESSION.wait_for_hardware_if_needed)
        
        try:
            context = getattr(self, section)()
        except AttributeError:
            context = {}
        
        self.write(loader.load(path).generate(**context))
    
    def get_version(self):
        """Get current version for cache busting."""
        if IMAGE_VERSION is not None and len(IMAGE_VERSION) > 1:
            # strip initial 'v' from version if present
            version = IMAGE_VERSION[1:] if IMAGE_VERSION[0] == "v" else IMAGE_VERSION
            return url_escape(version)
        return str(int(time.time()))
    
    def index(self):
        """Context for index.html template."""
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
        
        # Load favorites and preferences
        favorites = safe_json_load(FAVORITES_JSON_FILE, list)
        preferences = safe_json_load(PREFERENCES_JSON_FILE, dict)
        
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
            'title': mod_squeeze(pbname),
            'size': json.dumps(SESSION.host.pedalboard_size),
            'fulltitle': xhtml_escape(fullpbname),
            'titleblend': '' if SESSION.host.pedalboard_name else 'blend',
            'dev_api_class': 'dev_api' if False else '',  # Simplified, no DEV_API
            'using_desktop': 'true' if DESKTOP else 'false',
            'using_mod': 'true' if hwdesc.get('platform', None) is not None else 'false',
            'user_name': mod_squeeze(user_id.get("name", "")),
            'user_email': mod_squeeze(user_id.get("email", "")),
            'favorites': json.dumps(favorites),
            'preferences': json.dumps(preferences),
            'bufferSize': 128,  # Default, will be updated by backend
            'sampleRate': 48000,  # Default, will be updated by backend
        }
        return context
    
    def settings(self):
        """Context for settings.html template."""
        hwdesc = get_hardware_descriptor()
        prefs = safe_json_load(PREFERENCES_JSON_FILE, dict)
        
        context = {
            'cloud_url': CLOUD_HTTP_ADDRESS,
            'controlchain_url': CONTROLCHAIN_HTTP_ADDRESS,
            'version': self.get_argument('v'),
            'hmi_eeprom': 'true' if hwdesc.get('hmi_eeprom', False) else 'false',
            'preferences': json.dumps(prefs),
            'bufferSize': 128,  # Default
            'sampleRate': 48000,  # Default
        }
        return context
    
    def allguis(self):
        """Context for allguis.html template."""
        context = {
            'version': self.get_argument('v'),
        }
        return context

class TemplateLoader(TimelessRequestHandler):
    """Handler for loading template fragments."""
    
    def get(self, path):
        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        with open(os.path.join(HTML_DIR, 'include', path), 'r') as fh:
            self.write(fh.read())
        self.finish()

class BulkTemplateLoader(TimelessRequestHandler):
    """Handler for bulk loading templates into JavaScript."""
    
    def get(self):
        self.set_header("Content-Type", "text/javascript; charset=UTF-8")
        # Cache for a long time
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.set_header("Expires", "Mon, 31 Dec 2035 12:00:00 GMT")
        
        basedir = os.path.join(HTML_DIR, 'include')
        for template in os.listdir(basedir):
            if not re.match(r'^[a-z_]+\.html$', template):
                continue
            with open(os.path.join(basedir, template), 'r') as fh:
                contents = fh.read()
            self.write("TEMPLATES['%s'] = '%s';\n\n"
                       % (template[:-5], mod_squeeze(contents)))
        self.finish()

# Create the Tornado application
application = web.Application([
    # Template handlers (must be before proxy to avoid conflicts)
    (r"/(index\.html)?$", TemplateHandler),
    (r"/([a-z]+\.html)$", TemplateHandler),
    (r"/(allguis|sdk|settings)$", TemplateHandler),
    (r"/load_template/([a-z_]+\.html)$", TemplateLoader),
    (r"/js/templates\.js$", BulkTemplateLoader),
    
    # WebSocket proxies
    (r"/websocket/?$", WebSocketProxy, {"backend_path": "/websocket"}),
    (r"/ws/?$", WebSocketProxy, {"backend_path": "/ws"}),
    
    # HTTP API proxies (catch-all patterns for API endpoints)
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
], debug=(LOG >= 2))

def signal_recv(sig, _=0):
    """Signal handler (simplified)."""
    print(f"Received signal {sig}, ignoring (proxied backend handles)")

def prepare(isModApp=False):
    """Prepare the webserver."""
    print("Starting streamlined MOD webserver (templating + proxy only)")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Backend WebSocket URL: {BACKEND_WS_URL}")
    print(f"Templates directory: {HTML_DIR}")
    
    if haveSignal and not isModApp:
        signal(SIGUSR1, signal_recv)
        signal(SIGUSR2, signal_recv)
    
    # Start listening
    application.listen(DEVICE_WEBSERVER_PORT, address=("127.0.0.1" if DESKTOP else "0.0.0.0"))
    print(f"Listening on port {DEVICE_WEBSERVER_PORT}")

def start():
    """Start the IOLoop."""
    IOLoop.instance().start()

def stop():
    """Stop the IOLoop."""
    IOLoop.instance().stop()

def run():
    """Prepare and start the webserver."""
    prepare()
    start()

if __name__ == "__main__":
    run()