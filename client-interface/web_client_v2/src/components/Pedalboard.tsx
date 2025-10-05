import React, { useState } from 'react'
import axios from 'axios'

interface Instance {
  instance_id: string
  uri: string
  x: number
  y: number
}

export default function Pedalboard() {
  const [instances, setInstances] = useState<Instance[]>([])

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    try {
      const data = e.dataTransfer.getData('application/json')
      if (!data) return
      const plugin = JSON.parse(data)
      // compute drop coordinates relative to board
      const board = (e.currentTarget as HTMLElement)
      const rect = board.getBoundingClientRect()
      const x = Math.round(e.clientX - rect.left)
      const y = Math.round(e.clientY - rect.top)

      const resp = await axios.post('/api/plugins', { uri: plugin.uri, x, y })
      // If API returns instance info, add it; else use fallback id
      const instance = resp.data || { instance_id: `local_${Date.now()}`, uri: plugin.uri, x, y }
      setInstances((s) => [...s, { instance_id: instance.instance_id || instance.id || `local_${Date.now()}`, uri: plugin.uri, x, y }])
    } catch (err) {
      console.error('Failed to add plugin', err)
      alert('Failed to add plugin. Check backend logs.')
    }
  }

  return (
    <div className="pedalboard" id="pedalboard">
      <h2>Pedalboard</h2>
      <div className="board" onDragOver={onDragOver} onDrop={onDrop}>
        {instances.length === 0 && <div className="placeholder">Drop plugins here</div>}
        {instances.map((ins) => (
          <div key={ins.instance_id} className="plugin-instance" style={{ position: 'absolute', left: ins.x, top: ins.y }}>
            {ins.uri}
          </div>
        ))}
      </div>
    </div>
  )
}
