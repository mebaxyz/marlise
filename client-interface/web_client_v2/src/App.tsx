import React from 'react'
import PluginList from './components/PluginList'
import Pedalboard from './components/Pedalboard'

export default function App() {
  return (
    <div className="app">
      <h1>Marlise v2</h1>
      <div className="container">
        <PluginList />
        <Pedalboard />
      </div>
    </div>
  )
}
