import React, { useState } from 'react'
import axios from 'axios'
import '../styles/components/Pedalboard.css'

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
      // If API returns instance info, prefer that (instance_id, x, y)
      const instance = (resp && resp.data) ? resp.data : null
      const instanceId = instance?.instance_id || instance?.id || `local_${Date.now()}`
      const finalX = typeof instance?.x === 'number' ? instance.x : x
      const finalY = typeof instance?.y === 'number' ? instance.y : y

      setInstances((s) => [...s, { instance_id: instanceId, uri: plugin.uri, x: finalX, y: finalY }])
    } catch (err) {
      console.error('Failed to add plugin', err)
      alert('Failed to add plugin. Check backend logs.')
    }
  }

  return (
    <div className="mod-pedalboard-view">
      <div className="pedalboard-container" id="pedalboard">
        <div className="pedalboard-background">
          <canvas 
            className="pedalboard-canvas"
            onDragOver={onDragOver} 
            onDrop={onDrop}
          />
          
          {instances.length === 0 && (
            <div className="pedalboard-empty">
              <div className="pedalboard-message">
                Drag plugins from the library below to create your pedalboard
              </div>
            </div>
          )}
          
          {instances.map((ins) => (
            <div 
              key={ins.instance_id} 
              className="plugin-pedal" 
              style={{ 
                position: 'absolute', 
                left: ins.x, 
                top: ins.y,
                transform: 'translate(-50%, -50%)'
              }}
            >
              <div className="pedal-content">
                <div className="pedal-image">
                  <img src="/static/img/default-pedal.png" alt="" />
                </div>
                <div className="pedal-info">
                  <div className="pedal-title">{ins.uri.split('/').pop() || ins.uri}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
