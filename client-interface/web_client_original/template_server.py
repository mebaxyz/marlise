#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

# Template server with integrated API proxy to FastAPI client interface
# Serves templates + static files AND proxies API calls to localhost:8080

import json
import logging
import os
import re
import time
from base64 import b64encode
from tornado import gen, web, httpclient, websocket
from tornado.escape import url_escape, xhtml_escape
from tornado.template import Loader
from tornado.ioloop import IOLoop
from tornado.httputil import HTTPHeaders
from urllib.parse import urlencode, urlparse

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
try:
    from mod.session import SESSION
except ImportError:
    # Use mock session for template-only mode
    from mod.session_mock import SESSION
try:
    from modtools.utils import (
        init as lv2_init, cleanup as lv2_cleanup,
        get_pedalboard_info, get_jack_buffer_size, get_jack_sample_rate,
    )
except Exception:
    # Running in template-only or dev environment without native libs.
    # Provide lightweight fallbacks so pages render without LV2/native deps.
    def lv2_init():
        return None

    def lv2_cleanup():
        return None

    def get_pedalboard_info(bundlepath):
        return {
            'height': 0,
            'width': 0,
            'title': '',
            'connections': [],
            'plugins': [],
            'hardware': {},
        }

    def get_jack_buffer_size():
        return 256

    def get_jack_sample_rate():
        return 48000

# Global webserver state
class GlobalWebServerState(object):
    __slots__ = ['favorites']

gState = GlobalWebServerState()
gState.favorites = []

# Allow configuring the FastAPI target for the integrated proxy via environment
# variables. This makes the template server usable inside docker-compose where
# the FastAPI service may be reachable at a different hostname.
PROXY_HOST = os.environ.get('API_PROXY_HOST') or os.environ.get('FASTAPI_HOST') or os.environ.get('CLIENT_INTERFACE_ZMQ_HOST') or 'localhost'
try:
    PROXY_PORT = int(os.environ.get('API_PROXY_PORT') or os.environ.get('FASTAPI_PORT') or os.environ.get('CLIENT_INTERFACE_ZMQ_PORT') or 8080)
except Exception:
    PROXY_PORT = 8080

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

# =============================================================================
# API Proxy Handler

class ApiProxyHandler(TimelessRequestHandler):
    """Proxy handler to forward API calls to FastAPI client interface"""
    
    def initialize(self, proxy_host="localhost", proxy_port=8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.http_client = httpclient.AsyncHTTPClient()
    
    @gen.coroutine
    def proxy_request(self, method):
        # Build target URL
        path = self.request.path
        if path.startswith('/api/'):
            # Keep /api/ prefix for FastAPI routes
            target_path = path
        else:
            # Add /api/ prefix if missing
            target_path = '/api' + path
        
        target_url = f"http://{self.proxy_host}:{self.proxy_port}{target_path}"
        
        if self.request.query:
            target_url += f"?{self.request.query}"
        
        # Prepare headers (exclude problematic headers)
        headers = HTTPHeaders()
        for name, value in self.request.headers.get_all():
            if name.lower() not in ('host', 'content-length', 'connection'):
                headers.add(name, value)
        
        # Forward request to FastAPI
        try:
            response = yield self.http_client.fetch(
                target_url,
                method=method,
                headers=headers,
                body=self.request.body if self.request.body else None,
                allow_nonstandard_methods=True,
                raise_error=False,
                follow_redirects=False
            )
            
            # Forward response
            self.set_status(response.code)
            
            # Forward response headers (exclude problematic ones)
            for name, value in response.headers.get_all():
                if name.lower() not in ('server', 'date', 'content-encoding', 'transfer-encoding', 'connection'):
                    self.set_header(name, value)
            
            if response.body:
                self.write(response.body)
            
        except Exception as e:
            logging.error(f"Proxy error for {target_url}: {e}")
            self.set_status(502)
            self.write({"error": "Proxy error", "message": str(e)})
    
    @gen.coroutine  
    def get(self):
        yield self.proxy_request('GET')
    
    @gen.coroutine
    def post(self):
        yield self.proxy_request('POST')
    
    @gen.coroutine  
    def put(self):
        yield self.proxy_request('PUT')
    
    @gen.coroutine
    def patch(self):
        yield self.proxy_request('PATCH')
    
    @gen.coroutine
    def delete(self):
        yield self.proxy_request('DELETE')

# =============================================================================
# WebSocket Proxy Handler

class WebSocketProxyHandler(websocket.WebSocketHandler):
    """Proxy WebSocket connections to FastAPI WebSocket endpoint"""
    
    def initialize(self, proxy_host="localhost", proxy_port=8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_ws = None
    
    @gen.coroutine
    def open(self):
        # Connect to FastAPI WebSocket
        try:
            from tornado.websocket import websocket_connect
            proxy_url = f"ws://{self.proxy_host}:{self.proxy_port}/ws"
            self.proxy_ws = yield websocket_connect(proxy_url)
            
            # Forward messages from proxy to client
            IOLoop.current().spawn_callback(self._proxy_message_loop)
            
        except Exception as e:
            logging.error(f"WebSocket proxy connection error: {e}")
            self.close()
    
    @gen.coroutine
    def _proxy_message_loop(self):
        """Continuously read messages from proxy WebSocket and forward to client"""
        while self.proxy_ws:
            try:
                message = yield self.proxy_ws.read_message()
                if message is None:
                    break
                self.write_message(message)
            except Exception as e:
                logging.error(f"WebSocket proxy message error: {e}")
                break
    
    def on_message(self, message):
        """Forward message from client to FastAPI WebSocket"""
        if self.proxy_ws:
            self.proxy_ws.write_message(message)
    
    def on_close(self):
        """Clean up proxy connection"""
        if self.proxy_ws:
            self.proxy_ws.close()
            self.proxy_ws = None

# =============================================================================
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
            if not re.match(r'^[a-z_]+\.html$', template):
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

# Application with templating support and API proxy
def create_application():
    settings = {'log_function': lambda handler: None} if not LOG else {}

    # Inject proxy host/port into the handler initialize kwargs so they don't
    # rely on hard-coded defaults. This lets the environment drive where the
    # proxy forwards requests (useful in docker-compose).
    proxy_kwargs = dict(proxy_host=PROXY_HOST, proxy_port=PROXY_PORT)

    return web.Application([
        # WebSocket proxy (must come first to avoid conflicts)
        (r"/websocket/?", WebSocketProxyHandler, proxy_kwargs),

        # API proxy for all /api/* routes
        (r"/api/.*", ApiProxyHandler, proxy_kwargs),

        # Legacy API routes (proxy to FastAPI with /api/ prefix)
        (r"/(effect|pedalboard|snapshot|bank|login|logout|reset|system|hardware|jack|session|preferences|user|plugins|plugin|bundle|pedalboards|controllers|download|upload|ping)/?.*", ApiProxyHandler, proxy_kwargs),

        # Template serving (main functionality)
        (r"/(index.html)?$", TemplateHandler),
        (r"/([a-z]+\.html)$", TemplateHandler),
        (r"/(allguis|sdk|settings)$", TemplateHandler),
        (r"/load_template/([a-z_]+\.html)$", TemplateLoader),
        (r"/js/templates.js$", BulkTemplateLoader),
        
        # Static file serving (CSS, JS, images, etc.) - must be last
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
    bind_port = DEVICE_WEBSERVER_PORT
    actual_port = None
    # List of fallback ports to try before using an ephemeral port
    fallbacks = [int(os.environ.get('DEV_TEMPLATE_PORT', 8888)), 8000, 5173]
    try:
        application.listen(bind_port)
        actual_port = bind_port
    except Exception as exc_main:
        # Try fallbacks
        for fallback in fallbacks:
            try:
                application.listen(fallback)
                actual_port = fallback
                print(f"Warning: could not bind to port {bind_port} ({exc_main}); bound to fallback {fallback}")
                break
            except Exception:
                continue

    if actual_port is None:
        # Last resort: bind to an ephemeral port and retrieve the assigned port
        try:
            from tornado import httpserver, netutil
            sockets = netutil.bind_sockets(0)
            server = httpserver.HTTPServer(application)
            server.add_sockets(sockets)
            actual_port = sockets[0].getsockname()[1]
            print(f"Info: bound to ephemeral port {actual_port}")
        except Exception as e:
            print(f"Failed to bind to any port: {e}")
            raise

    print("🚀 Marlise Template Server running on port %d" % actual_port)
    print(f"📡 API proxy active - forwarding calls to FastAPI on {PROXY_HOST}:{PROXY_PORT}")
    print(f"🌐 WebSocket proxy active - forwarding /websocket to /ws on {PROXY_HOST}:{PROXY_PORT}")
    print("📄 Serving templates and static files from %s" % HTML_DIR)
    
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("Template server stopped")
        lv2_cleanup()
        return True

if __name__ == '__main__':
    run()