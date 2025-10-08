// API Proxy Configuration
// This file redirects all legacy API calls to the new FastAPI client interface

(function() {
    'use strict';

    // Configuration
    var CLIENT_INTERFACE_HOST = window.location.protocol + '//' + window.location.hostname + ':8080';
    var LEGACY_API_PREFIX = '';
    var NEW_API_PREFIX = '/api';

    // API endpoint mappings from legacy to new client interface
    var ENDPOINT_MAPPINGS = {
        // System endpoints
        '/system/info': '/api/system/info',
        '/system/prefs': '/api/system/preferences', 
        '/system/exechange': '/api/system/exechange',
        '/system/cleanup': '/api/system/cleanup',
        
        // Plugin/Effect endpoints
        '/effect/add': '/api/plugins',
        '/effect/remove': '/api/plugins',
        '/effect/get': '/api/plugins/info',
        '/effect/get_non_cached': '/api/plugins/info',
        '/effect/list': '/api/plugins/available',
        '/effect/bulk': '/api/plugins/bulk',
        '/effect/parameter/set': '/api/plugins/parameters',
        '/effect/parameter/address': '/api/plugins/parameters/address',
        '/effect/connect': '/api/plugins/connections',
        '/effect/disconnect': '/api/plugins/connections',
        
        // Plugin presets
        '/effect/preset/load': '/api/plugins/presets/load',
        '/effect/preset/save_new': '/api/plugins/presets',
        '/effect/preset/save_replace': '/api/plugins/presets',
        '/effect/preset/delete': '/api/plugins/presets',
        
        // Plugin resources
        '/effect/image/screenshot.png': '/api/plugins/image/screenshot.png',
        '/effect/image/thumbnail.png': '/api/plugins/image/thumbnail.png', 
        '/effect/file': '/api/plugins/files',
        
        // Pedalboard endpoints
        '/pedalboard/list': '/api/pedalboards',
        '/pedalboard/save': '/api/pedalboards',
        '/pedalboard/load_bundle': '/api/pedalboards/load',
        '/pedalboard/load_remote': '/api/pedalboards/load',
        '/pedalboard/load_web': '/api/pedalboards/load',
        '/pedalboard/info': '/api/pedalboards/info',
        '/pedalboard/remove': '/api/pedalboards',
        '/pedalboard/image/screenshot.png': '/api/pedalboards/image/screenshot.png',
        '/pedalboard/image/thumbnail.png': '/api/pedalboards/image/thumbnail.png',
        '/pedalboard/image/generate': '/api/pedalboards/image/generate',
        '/pedalboard/image/check': '/api/pedalboards/image/check',
        
        // Snapshot endpoints
        '/snapshot/save': '/api/snapshots',
        '/snapshot/saveas': '/api/snapshots',
        '/snapshot/rename': '/api/snapshots',
        '/snapshot/remove': '/api/snapshots',
        '/snapshot/list': '/api/snapshots',
        '/snapshot/name': '/api/snapshots/current',
        '/snapshot/load': '/api/snapshots/load',
        
        // Bank endpoints
        '/banks': '/api/banks',
        '/banks/save': '/api/banks',
        
        // JACK endpoints
        '/jack/get_midi_devices': '/api/jack/midi-devices',
        '/jack/set_midi_devices': '/api/jack/midi-devices',
        
        // Recording endpoints
        '/recording/start': '/api/recording/start',
        '/recording/stop': '/api/recording/stop',
        '/recording/play': '/api/recording/play',
        '/recording/download': '/api/recording/download',
        '/recording/reset': '/api/recording/reset',
        
        // File management
        '/files/list': '/api/files',
        
        // Favorites
        '/favorites/add': '/api/favorites',
        '/favorites/remove': '/api/favorites',
        
        // Configuration
        '/config/set': '/api/config',
        
        // Utilities
        '/ping': '/api/health',
        '/reset': '/api/session/reset',
        '/truebypass': '/api/session/truebypass',
        '/set_buffersize': '/api/session/buffer-size',
        '/reset_xruns': '/api/session/reset-xruns'
    };

    // Function to map legacy URL to new API URL
    function mapApiUrl(url) {
        // Handle parameterized URLs
        for (var legacyPattern in ENDPOINT_MAPPINGS) {
            if (url.startsWith(legacyPattern)) {
                var newEndpoint = ENDPOINT_MAPPINGS[legacyPattern];
                var remainder = url.substring(legacyPattern.length);
                return CLIENT_INTERFACE_HOST + newEndpoint + remainder;
            }
        }
        
        // If no mapping found, proxy to client interface with /api prefix
        if (url.startsWith('/')) {
            return CLIENT_INTERFACE_HOST + NEW_API_PREFIX + url;
        }
        
        return url;
    }

    // Override jQuery AJAX to redirect API calls
    if (window.jQuery && window.jQuery.ajax) {
        var originalAjax = window.jQuery.ajax;
        window.jQuery.ajax = function(options) {
            if (typeof options === 'string') {
                options = { url: options };
            }
            
            if (options && options.url && options.url.startsWith('/')) {
                var originalUrl = options.url;
                options.url = mapApiUrl(originalUrl);
                
                if (window.console && window.console.log) {
                    console.log('API Proxy:', originalUrl, '->', options.url);
                }
            }
            
            return originalAjax.call(this, options);
        };
        
        // Also override jQuery shorthand methods
        ['get', 'post', 'put', 'delete'].forEach(function(method) {
            if (window.jQuery[method]) {
                var originalMethod = window.jQuery[method];
                window.jQuery[method] = function(url, data, success, dataType) {
                    if (typeof url === 'string' && url.startsWith('/')) {
                        url = mapApiUrl(url);
                        if (window.console && window.console.log) {
                            console.log('API Proxy (' + method.toUpperCase() + '):', arguments[0], '->', url);
                        }
                    }
                    return originalMethod.call(this, url, data, success, dataType);
                };
            }
        });
    }

    // Override WebSocket connections
    if (window.WebSocket) {
        var OriginalWebSocket = window.WebSocket;
        window.WebSocket = function(url, protocols) {
            if (url.startsWith('/websocket') || url.startsWith('ws://') && url.includes('/websocket')) {
                url = CLIENT_INTERFACE_HOST.replace('http', 'ws') + '/ws';
                if (window.console && window.console.log) {
                    console.log('WebSocket Proxy:', arguments[0], '->', url);
                }
            }
            return protocols ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
        };
        
        // Copy static properties
        for (var prop in OriginalWebSocket) {
            if (OriginalWebSocket.hasOwnProperty(prop)) {
                window.WebSocket[prop] = OriginalWebSocket[prop];
            }
        }
    }

    // Global configuration access
    window.API_PROXY = {
        CLIENT_INTERFACE_HOST: CLIENT_INTERFACE_HOST,
        mapUrl: mapApiUrl,
        setClientHost: function(host) {
            CLIENT_INTERFACE_HOST = host;
        }
    };

    console.log('API Proxy initialized. All API calls will be redirected to:', CLIENT_INTERFACE_HOST);
})();