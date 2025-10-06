import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './Settings.css'

interface SettingsData {
  audio: {
    device: string
    sampleRate: number
    bufferSize: number
    xruns: number
  }
  ui: {
    theme: string
    language: string
    showTooltips: boolean
    autoSave: boolean
  }
  system: {
    version: string
    platform: string
    cpu: string
    memory: string
  }
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData>({
    audio: {
      device: 'default',
      sampleRate: 48000,
      bufferSize: 128,
      xruns: 0
    },
    ui: {
      theme: 'dark',
      language: 'en',
      showTooltips: true,
      autoSave: true
    },
    system: {
      version: '2.0.0',
      platform: 'Linux',
      cpu: 'Unknown',
      memory: 'Unknown'
    }
  })

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      // In a real implementation, this would load from the API
      // For now, we'll use mock data
      const mockSettings: SettingsData = {
        audio: {
          device: 'PipeWire',
          sampleRate: 48000,
          bufferSize: 128,
          xruns: 0
        },
        ui: {
          theme: 'dark',
          language: 'en',
          showTooltips: true,
          autoSave: true
        },
        system: {
          version: '2.0.0-dev',
          platform: 'Linux',
          cpu: 'Intel(R) Core(TM) i7-8750H CPU @ 2.20GHz',
          memory: '16 GB'
        }
      }
      setSettings(mockSettings)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateSetting = (category: keyof SettingsData, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
  }

  const saveSettings = async () => {
    try {
      // In a real implementation, this would save to the API
      console.log('Saving settings:', settings)
      // Show success message
      alert('Settings saved successfully!')
    } catch (error) {
      console.error('Failed to save settings:', error)
      alert('Failed to save settings')
    }
  }

  const resetToDefaults = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      loadSettings()
    }
  }

  if (loading) {
    return (
      <div className="settings">
        <div className="box">
          <div className="settings-content">
            <div className="loading">
              <div className="mod-loading"></div>
              <p>Loading settings...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="settings">
      <div className="box">
        <header>
          <h1>Settings</h1>
        </header>

        <div className="settings-content">
          {/* Audio Settings */}
          <div className="settings-section">
            <h2>Audio</h2>

            <div className="setting-group">
              <div className="setting-item">
                <div className="setting-info">
                  <label>Audio Device</label>
                  <p className="description">Select the audio device to use</p>
                </div>
                <div className="setting-control select-control">
                  <select
                    value={settings.audio.device}
                    onChange={(e) => updateSetting('audio', 'device', e.target.value)}
                  >
                    <option value="default">Default</option>
                    <option value="PipeWire">PipeWire</option>
                    <option value="JACK">JACK</option>
                    <option value="ALSA">ALSA</option>
                  </select>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label>Sample Rate</label>
                  <p className="description">Audio sample rate in Hz</p>
                </div>
                <div className="setting-control select-control">
                  <select
                    value={settings.audio.sampleRate}
                    onChange={(e) => updateSetting('audio', 'sampleRate', parseInt(e.target.value))}
                  >
                    <option value="44100">44100 Hz</option>
                    <option value="48000">48000 Hz</option>
                    <option value="96000">96000 Hz</option>
                  </select>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label>Buffer Size</label>
                  <p className="description">Audio buffer size in frames</p>
                </div>
                <div className="setting-control select-control">
                  <select
                    value={settings.audio.bufferSize}
                    onChange={(e) => updateSetting('audio', 'bufferSize', parseInt(e.target.value))}
                  >
                    <option value="64">64 frames</option>
                    <option value="128">128 frames</option>
                    <option value="256">256 frames</option>
                    <option value="512">512 frames</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="audio-device-info">
              <h3>Current Audio Status</h3>
              <p><strong>Device:</strong> {settings.audio.device}</p>
              <p><strong>Sample Rate:</strong> {settings.audio.sampleRate} Hz</p>
              <p><strong>Buffer Size:</strong> {settings.audio.bufferSize} frames</p>
              <p><strong>Xruns:</strong> {settings.audio.xruns}</p>
            </div>
          </div>

          {/* UI Settings */}
          <div className="settings-section">
            <h2>User Interface</h2>

            <div className="setting-group">
              <div className="setting-item">
                <div className="setting-info">
                  <label>Theme</label>
                  <p className="description">Choose the application theme</p>
                </div>
                <div className="setting-control select-control">
                  <select
                    value={settings.ui.theme}
                    onChange={(e) => updateSetting('ui', 'theme', e.target.value)}
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                  </select>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label>Language</label>
                  <p className="description">Select the interface language</p>
                </div>
                <div className="setting-control select-control">
                  <select
                    value={settings.ui.language}
                    onChange={(e) => updateSetting('ui', 'language', e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label>Show Tooltips</label>
                  <p className="description">Display help tooltips on hover</p>
                </div>
                <div className="setting-control checkbox-control">
                  <input
                    type="checkbox"
                    checked={settings.ui.showTooltips}
                    onChange={(e) => updateSetting('ui', 'showTooltips', e.target.checked)}
                  />
                  <span>Enabled</span>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label>Auto Save</label>
                  <p className="description">Automatically save changes</p>
                </div>
                <div className="setting-control checkbox-control">
                  <input
                    type="checkbox"
                    checked={settings.ui.autoSave}
                    onChange={(e) => updateSetting('ui', 'autoSave', e.target.checked)}
                  />
                  <span>Enabled</span>
                </div>
              </div>
            </div>
          </div>

          {/* System Information */}
          <div className="settings-section">
            <h2>System Information</h2>

            <div className="system-info">
              <h3>System Details</h3>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Version:</span>
                  <span className="info-value">{settings.system.version}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Platform:</span>
                  <span className="info-value">{settings.system.platform}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">CPU:</span>
                  <span className="info-value">{settings.system.cpu}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Memory:</span>
                  <span className="info-value">{settings.system.memory}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="settings-section">
            <div className="button-group">
              <button className="btn" onClick={saveSettings}>
                Save Settings
              </button>
              <button className="btn secondary" onClick={loadSettings}>
                Reload Settings
              </button>
              <button className="btn danger" onClick={resetToDefaults}>
                Reset to Defaults
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}