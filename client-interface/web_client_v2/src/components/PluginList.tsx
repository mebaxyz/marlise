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
    axios.get('/api/plugins/available').then((resp) => {
      setPlugins(resp.data || [])
    })
  }, [])

  return (
    <div className="plugin-list">
      <h2>Available plugins</h2>
      <div className="list">
        {plugins.map((p) => (
          <div key={p.uri} className="plugin-card" draggable>
            <img src={p.thumbnail_href || '/static/img/default-plugin.png'} alt="" />
            <div className="meta">
              <div className="label">{p.label || p.uri}</div>
              <div className="author">{p.author?.name}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
