# Integration Test Plan

This document lists integration tests, the RPCs they exercise, expected success criteria, and status. Keep this file updated when adding tests or new public RPCs that need coverage.

Format:
- Test name: short description
- Files: test path(s)
- RPCs exercised: list of bridge RPCs exercised
- Acceptance: what the test validates
- Status: not-started | in-progress | covered


1) Plugin presets
- Test name: Plugin Presets
- Files: `tests/integration/test_plugin_presets.py`
- RPCs exercised: `get_plugin_presets`, `load_preset`, `save_preset`, `validate_preset`, `get_plugin_info`, `set_parameter`, `get_parameter`
- Acceptance: preset list returns expected structure; loading a preset applies parameters to instance; saving a preset stores it and appears in subsequent `get_plugin_presets`.
- Status: not-started

2) Plugin GUI and metadata
- Test name: Plugin Metadata
- Files: `tests/integration/test_plugin_metadata.py`
- RPCs exercised: `get_plugin_gui`, `get_plugin_essentials`, `get_plugin_info`
- Acceptance: metadata contains URI, parameter ports, and stable response for unknown instance_id.
- Status: not-started

3) Bundle operations
- Test name: Plugin Bundles
- Files: `tests/integration/test_bundles.py`
- RPCs exercised: `is_bundle_loaded`, `add_bundle`, `remove_bundle`, `list_bundle_plugins`
- Acceptance: adding/removing bundles updates plugin availability list.
- Status: not-started

4) Plugin search & rescan
- Test name: Plugin Search & Rescan
- Files: `tests/integration/test_plugin_search_rescan.py`
- RPCs exercised: `search_plugins`, `rescan_plugins`, `get_available_plugins`
- Acceptance: searching returns expected URIs; rescan refreshes listing.
- Status: not-started

5) Parameter edge-cases
- Test name: Parameter Edgecases
- Files: `tests/integration/test_parameters_edgecases.py`
- RPCs exercised: `get_parameter`, `set_parameter`
- Acceptance: invalid parameter queries return well-formed errors; out-of-range set attempts handled gracefully.
- Status: not-started

6) MIDI/audio-specific routing
- Test name: MIDI Audio Ports
- Files: `tests/integration/test_midi_audio_ports.py`
- RPCs exercised: `connect_jack_midi_output_ports`, `connect_jack_ports`, `disconnect_jack_ports`, `disconnect_all_jack_ports`
- Acceptance: MIDI connections show in `jack_lsp -c`; bridge returns success.
- Status: not-started

7) Audio queries and transport
- Test name: Audio Queries & Transport
- Files: `tests/integration/test_audio_queries.py`
- RPCs exercised: `get_jack_buffer_size`, `set_jack_buffer_size`, `get_jack_sample_rate`, `get_jack_hardware_ports`, `get_jack_port_alias`, `reset_xruns`, transport controls
- Acceptance: queries return sane values; set operations succeed and transport changes are visible.
- Status: not-started

8) Disconnect / cleanup robustness
- Test name: Disconnect Cleanup
- Files: `tests/integration/test_disconnect_cleanup.py`
- RPCs exercised: `disconnect_all_jack_ports`, `disconnect_jack_ports`, plugin load/remove
- Acceptance: after cleanup no plugin-jack connections remain.
- Status: not-started

9) Health and error scenarios
- Test name: Health and Failure Modes
- Files: `tests/integration/test_health_and_errors.py`
- RPCs exercised: health endpoints, any RPCs used to simulate failure modes
- Acceptance: bridge reports 'unhealthy' when mod-host unreachable; RPCs return clear errors when inputs invalid.
- Status: not-started

--

Keep this list updated and reference it in PRs that add or modify tests.
