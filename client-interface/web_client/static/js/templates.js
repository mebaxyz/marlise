// SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
// SPDX-License-Identifier: AGPL-3.0-or-later

/*
  This file handles client-side configuration loading, replacing server-side
  template variable injection with API-based config fetching.
*/

// Prevent multiple executions
if (typeof window.MOD_TEMPLATES_LOADED === "undefined") {
  window.MOD_TEMPLATES_LOADED = true;

  /**
   * Configuration properties to request from the webui_gateway config settings endpoint.
   * This object defines the sections and keys needed for the frontend.
   */
  var requiredConfig = {
    device: ["api_key", "host", "port"],
    system: ["version", "build_date"],
    // Add more sections and keys as needed
  };

  /**
   * Config object with keys and values to query from the backend.
   * Based on the old template context from templates.py.
   * Key is the config path, value is the expected data or query parameter.
   */
  var configQueries = {
    "environment.desktop": null,
    //ai generated
    "device.api_key": null,
    "device.host": null,
    "device.port": null,
    "system.version": null,
    "system.build_date": null,
    "system.cloud_url": null,
    "system.cloud_labs_url": null,
    "system.plugins_url": null,
    "system.pedalboards_url": null,
    "system.pedalboards_labs_url": null,
    "system.controlchain_url": null,
    "system.dev_api_class": null,
    "system.bin_compat": null,
    "system.codec_truebypass": null,
    "system.factory_pedalboards": null,
    "system.platform": null,
    "system.addressing_pages": null,
    "system.bufferSize": null,
    "system.sampleRate": null,
    "system.lv2_plugin_dir": null,
    // User data (may need separate endpoints)
    "user.name": null,
    "user.email": null,
    "user.favorites": null,
    "user.preferences": null,
  };

  /**
   * Fetch all config data using the batch endpoint.
   * Uses XMLHttpRequest for compatibility with legacy code.
   */
  function fetchAllConfigAsync(timeoutMs = 2000) {
    // Prepare body with the keys the client expects
    const url = `/api/config/settings/batch`;
    const body = JSON.stringify({ queries: configQueries });

    // Use AbortController to implement a client-side timeout
    const controller = new AbortController();
    const signal = controller.signal;
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body,
      signal: signal,
    })
      .then((resp) => {
        clearTimeout(timer);
        if (!resp.ok) throw new Error(`status ${resp.status}`);
        return resp.json();
      })
      .then((json) => json.results || {})
      .catch((err) => {
        console.warn("Failed to fetch batch config:", err);
        return {};
      });
  }

  /**
   * Populate configQueries with data from the backend using batch endpoint.
   */
  function populateConfigQueries() {
    // Immediately set defaults so UI does not hang waiting for network
    window.SITEURL = "";
    window.CLOUD_LABS_URL = "";
    window.PLUGINS_URL = "";
    window.PEDALBOARDS_URL = "";
    window.PEDALBOARDS_LABS_URL = "";
    window.CONTROLCHAIN_URL = "";
    window.LV2_PLUGIN_DIR = "";
    window.VERSION = "";
    window.BIN_COMPAT = false;
    window.PLATFORM = "";
    window.SAMPLERATE = 48000;
    window.ADDRESSING_PAGES = [];
    window.USING_MOD_DESKTOP = false;
    window.FAVORITES = [];
    window.PREFERENCES = {};
    window.CODEC_TRUEBYPASS = false;

    // Fetch real values asynchronously and update globals when available
    fetchAllConfigAsync(2000).then((results) => {
      Object.keys(results).forEach((key) => {
        if (configQueries.hasOwnProperty(key)) {
          configQueries[key] = results[key];
        }
      });

      // Apply fetched values
      window.SITEURL = configQueries["system.cloud_url"] || window.SITEURL;
    window.CLOUD_LABS_URL = configQueries["system.cloud_labs_url"] || "";
    window.PLUGINS_URL = configQueries["system.plugins_url"] || "";
    window.PEDALBOARDS_URL = configQueries["system.pedalboards_url"] || "";
    window.PEDALBOARDS_LABS_URL =
      configQueries["system.pedalboards_labs_url"] || "";
    window.CONTROLCHAIN_URL = configQueries["system.controlchain_url"] || "";
    window.LV2_PLUGIN_DIR = configQueries["system.lv2_plugin_dir"] || "";
    window.VERSION = configQueries["system.version"] || "";
    window.BIN_COMPAT = configQueries["system.bin_compat"] || "";
    window.PLATFORM = configQueries["system.platform"] || "";
    window.SAMPLERATE = configQueries["system.sampleRate"] || 48000;
    window.ADDRESSING_PAGES = configQueries["system.addressing_pages"] || [];
    window.USING_MOD_DESKTOP = configQueries["environment.desktop"] || false;
    window.FAVORITES = configQueries["user.favorites"] || [];
    window.PREFERENCES = configQueries["user.preferences"] || {};
    window.CODEC_TRUEBYPASS = configQueries["system.codec_truebypass"] || false;

    // Additional variables that may be used in templates
    window.NOTIFICATIONS_ENABLED = true;
    window.DEBUG = true;
    window.CLOUD_TERMS_ACCEPTED =
      (window.PREFERENCES &&
        window.PREFERENCES["cloud-terms-accepted"] === "true") ||
      false;
    window.USING_MOD_DEVICE = !window.USING_MOD_DESKTOP;

    // Show/hide conditional elements based on device type and config
    // Wait for DOM to be ready or use a longer timeout
    setTimeout(function () {
      var desktop_welcome = document.getElementById("desktop-welcome-text");
      var desktop_agree = document.getElementById("desktop-agree-btn");
      var device_terms = document.getElementById("device-terms-text");
      var device_disagree = document.getElementById("device-disagree-btn");
      var device_agree = document.getElementById("device-agree-btn");

      if (window.USING_MOD_DESKTOP) {
        if (desktop_welcome) desktop_welcome.style.display = "block";
        if (desktop_agree) desktop_agree.style.display = "inline-block";
      } else {
        if (device_terms) device_terms.style.display = "block";
        if (device_disagree) device_disagree.style.display = "inline-block";
        if (device_agree) device_agree.style.display = "inline-block";
      }

      // Show factory pedalboards sections if factory pedalboards are available
      if (
        configQueries["system.factory_pedalboards"] &&
        configQueries["system.factory_pedalboards"].length > 0
      ) {
        var showElements = [
          "user-pedalboards-separator",
          "factory-pedalboards-section",
          "factory-banks-info",
          "user-pedalboards-separator-2",
          "factory-pedalboards-section-2",
        ];
        showElements.forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.style.display = "block";
        });
        // Hide the no-factory info
        var noFactoryEl = document.getElementById("no-factory-banks-info");
        if (noFactoryEl) noFactoryEl.style.display = "none";
      } else {
        // Show the no-factory info
        var noFactoryEl = document.getElementById("no-factory-banks-info");
        if (noFactoryEl) noFactoryEl.style.display = "block";
      }
    }, 100); // Increased timeout to ensure DOM is ready
  }

  // Populate config on load
  populateConfigQueries();
} // End of MOD_TEMPLATES_LOADED guard
