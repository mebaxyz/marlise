import React, { useEffect, useState } from 'react'
import axios from 'axios'

interface Plugin {
  uri: string
  label: string
  author?: { name?: string }
  thumbnail_href?: string
}

export default function PluginList() {
  const [plugins, setPlugins] = useState<Plugin[]>([])

  useEffect(() => {
    axios
      .get('/api/plugins/available')
      .then((resp) => {
        // Adapter returns { plugins: [...] }
        const plugins = resp.data && resp.data.plugins ? resp.data.plugins : []
        setPlugins(plugins)
      })
      .catch((err) => {
        console.error('Failed to fetch plugins', err)
        setPlugins([])
      })
  }, [])

  const onDragStart = (e: React.DragEvent, plugin: Plugin) => {
    try {
      const payload = JSON.stringify({ uri: plugin.uri, label: plugin.label })
      e.dataTransfer.setData('application/json', payload)
      e.dataTransfer.effectAllowed = 'copy'
    } catch (err) {
      console.error('Failed to set drag data', err)
    }
  }

  return (
    <div className="plugin-list-horizontal">
      <div className="plugin-list-header">
        <div className="plugin-list-categories">
          <ul>
            <li className="selected">All</li>
            <li>Delay</li>
            <li>Distortion</li>
            <li>Filter</li>
            <li>Modulator</li>
            <li>Reverb</li>
          </ul>
        </div>
        
        <div className="plugin-list-controls">
          <div className="plugin-list-settings" title="Plugin Library Settings" />
          <div className="plugin-list-fold" title="Fold Plugin Library" />
        </div>
      </div>
      
      <div className="plugin-list-content">
        <div className="plugin-list-nav left" title="Previous plugins" />
        
        <div className="plugin-list-results">
          <div className="plugin-list-wrapper selected">
            <div className="plugin-list-plugins">
              {plugins.map((p) => (
                <div
                  key={p.uri}
                  className="plugin-card plugin-card-horizontal"
                  draggable
                  onDragStart={(e) => onDragStart(e, p)}
                  title={p.label || p.uri}
                >
                  <div className="plugin-thumb">
                    <img src={p.thumbnail_href || '/static/img/default-plugin.png'} alt="" />
                  </div>
                  <div className="plugin-info">
                    <div className="plugin-title">{p.label || p.uri}</div>
                    <div className="plugin-author">{p.author?.name || 'Unknown'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="plugin-list-nav right" title="Next plugins" />
      </div>
    </div>
  )
}
