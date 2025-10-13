# Changelog

## [Unreleased]

### Added
- modhost-bridge: delegate JACK connect/disconnect commands to mod-host (ensures correct routing of JACK connections).
- PluginInstance now includes `host_instance` (numeric instance assigned by mod-host) so clients/tests can reliably discover JACK port names.
- Bridge: initialize JACK audio subsystem on startup to allow audio operations without an explicit `init_jack` call.
- Integration test: `tests/integration/test_modhost_bridge_full.py` includes a new test that loads two plugins and verifies JACK-level connections using `jack_lsp` inside the runtime container.

### Fixed
- Bridge: ensure numeric instance IDs are used when sending `add <uri> <instance>` commands to mod-host.

### Dev
- Added small debug helper scripts under `tests/` to aid local debugging (consider moving them to `dev/` or removing before merge).

---

(When releasing, move items from "Unreleased" into a new section with the release version and date.)
