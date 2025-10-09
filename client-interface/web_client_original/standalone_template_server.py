#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Standalone template server with integrated API proxy for Marlise"""

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

# Configuration constants
HTML_DIR = os.path.dirname(os.path.abspath(__file__)) + "/html"
DEVICE_WEBSERVER_PORT = 8888
LOG = 1

# Proxy target configuration (env overrides useful for docker-compose)
PROXY_HOST = os.environ.get('API_PROXY_HOST') or os.environ.get('FASTAPI_HOST') or 'localhost'
try:
    PROXY_PORT = int(os.environ.get('API_PROXY_PORT') or os.environ.get('FASTAPI_PORT') or 8080)
except Exception:
    PROXY_PORT = 8080

# Minimal mock objects for template rendering
class MockPreferences:
    def __init__(self):
        self.prefs = {}

class MockHost:
    def __init__(self):
        self.pedalboard_name = "Untitled Pedalboard"
        self.pedalboard_path = "/tmp/default.pedalboard" 
        self.pedalboard_size = [0, 0]
    
    def snapshot_name(self):
        return "Default"

class MockSession:
    def __init__(self):
        self.prefs = MockPreferences()
        self.host = MockHost()
    
    def wait_for_hardware_if_needed(self, callback=None):
        if callback:
            callback(True)
        return True
    
    def get_hardware_actuators(self):
        return []

SESSION = MockSession()

def mod_squeeze(text):
    """Simple text escaping for templates"""
    return text.replace("\\", "\\\\").replace("'", "\\'")

def safe_json_load(path, default_type):
    """Safely load JSON file or return default"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default_type()

def get_jack_buffer_size():
    return 256

def get_jack_sample_rate(): 
    return 48000

def get_hardware_descriptor():
    return {}

# Global state
gState = type('obj', (object,), {'favorites': []})()

# Base handler classes
class TimelessRequestHandler(web.RequestHandler):
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
# Template serving handlers

class TemplateHandler(TimelessRequestHandler):
    @gen.coroutine
    def get(self, path):
        # Simple versioning
        try:
            version = url_escape(self.get_argument('v'))
        except web.MissingArgumentError:
            uri = self.request.uri
            uri += '&' if self.request.query else '?'
            uri += 'v=%d' % int(time.time())
            self.redirect(uri)
            return

        # Route to appropriate template
        if path is None:
            path = ''

        if path in ('', 'index.html'):
            context = self.index()
        elif path in ('pedalboard', 'pedalboard.html'):
            context = self.pedalboard()
        elif path in ('settings', 'settings.html'):
            context = self.settings()
        elif path in ('allguis',):
            context = self.allguis()
        else:
            # Default template
            context = {}

        # Add common template variables
        context.update({
            'version': version,
            'using_desktop': False,
            'using_mod': True,
            'favorites': json.dumps(gState.favorites),
            'sampleRate': get_jack_sample_rate(),
            'bufferSize': get_jack_buffer_size(),
            'codec_truebypass': True,
            'hardware_profile': b64encode(json.dumps([]).encode("utf-8")),
            'preferences': json.dumps({}),
            'addressing_pages': json.dumps([])
        })

        # Render template
        template_path = path if path.endswith('.html') else f"{path}.html"
        template_file = os.path.join(HTML_DIR, template_path)
        
        try:
            loader = Loader(HTML_DIR)
            template = loader.load(template_path)
            html = template.generate(**context)
            self.write(html)
        except Exception as e:
            logging.error(f"Template error: {e}")
            self.write_error(500)

    def get_version(self):
        return int(time.time())

    def index(self):
        return {
            'titleblend': '',
            'bundlepath': '',
            'size': json.dumps([0, 0])
        }

    def pedalboard(self):
        pedalboard = {
            'title': SESSION.host.pedalboard_name,
            'connections': [],
            'plugins': [],
            'hardware': {'audio_ins': 2, 'audio_outs': 2, 'midi_ins': 1, 'midi_outs': 1}
        }
        
        return {
            'default_icon_template': '',
            'default_settings_template': '',
            'pedalboard': b64encode(json.dumps(pedalboard).encode("utf-8"))
        }

    def allguis(self):
        return {'version': self.get_argument('v')}

    def settings(self):
        return {
            'cloud_url': '',
            'controlchain_url': '',
            'version': self.get_argument('v'),
            'hmi_eeprom': 'false',
            'preferences': json.dumps({}),
            'bufferSize': get_jack_buffer_size(),
            'sampleRate': get_jack_sample_rate(),
        }

class TemplateLoader(TimelessRequestHandler):
    def get(self, path):
        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        try:
            with open(os.path.join(HTML_DIR, 'include', path), 'r') as fh:
                self.write(fh.read())
        except FileNotFoundError:
            self.write_error(404)

class BulkTemplateLoader(TimelessRequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/javascript; charset=UTF-8")
        basedir = os.path.join(HTML_DIR, 'include')
        
        if not os.path.exists(basedir):
            self.write("// No templates directory found\n")
            return
            
        for template in os.listdir(basedir):
            if not re.match(r'^[a-z_]+\.html$', template):
                continue
            try:
                with open(os.path.join(basedir, template), 'r') as fh:
                    contents = fh.read()
                self.write("TEMPLATES['%s'] = '%s';\n\n"
                           % (template[:-5], mod_squeeze(contents)))
            except Exception:
                continue

    def set_default_headers(self):
        TimelessRequestHandler.set_default_headers(self)
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.set_header("Expires", "Mon, 31 Dec 2035 12:00:00 gmt")

# =============================================================================
# Main Application

def create_application():
    # Ensure tornado's write_error can safely check settings.get('serve_traceback')
    settings = {'log_function': lambda handler: None, 'serve_traceback': False} if not LOG else {'serve_traceback': False}
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

def run():
    """Start the template server with integrated proxy"""
    application = create_application()
    actual_port = None
    try:
        application.listen(DEVICE_WEBSERVER_PORT)
        actual_port = DEVICE_WEBSERVER_PORT
    except Exception:
        fallback = int(os.environ.get('DEV_TEMPLATE_PORT', 8888))
        try:
            application.listen(fallback)
            actual_port = fallback
            print(f"Warning: bound to fallback port {fallback}")
        except Exception:
            from tornado import httpserver, netutil
            sockets = netutil.bind_sockets(0)
            server = httpserver.HTTPServer(application)
            server.add_sockets(sockets)
            actual_port = sockets[0].getsockname()[1]

    print("🚀 Marlise Template Server running on port %d" % actual_port)
    print(f"📡 API proxy active - forwarding calls to FastAPI on {PROXY_HOST}:{PROXY_PORT}")
    print(f"🌐 WebSocket proxy active - forwarding /websocket to /ws on {PROXY_HOST}:{PROXY_PORT}")
    print("📄 Serving templates and static files from %s" % HTML_DIR)
    
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("\n🛑 Template server stopped")
        return True

if __name__ == '__main__':
    run()