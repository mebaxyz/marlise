import React, { useEffect, useState } from 'react'
import axios from 'axios'
import PluginList from './components/PluginList'
import Pedalboard from './components/Pedalboard'

export default function App() {
  const [healthy, setHealthy] = useState<boolean | null>(null)
  const [healthMsg, setHealthMsg] = useState<string>('')

  useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        const resp = await axios.get('/api/session/health')
        if (!mounted) return
        // Accept either {ok:true} or 200
        if (resp.status === 200 && (resp.data == null || resp.data.ok === true || resp.data.status === 'ok')) {
          setHealthy(true)
          setHealthMsg('')
        } else {
          setHealthy(false)
          setHealthMsg(JSON.stringify(resp.data || resp.status))
        }
      } catch (err: any) {
        if (!mounted) return
        setHealthy(false)
        setHealthMsg(err?.message || String(err))
      }
    }

    check()
    const id = setInterval(check, 5000)
    return () => {
      mounted = false
      clearInterval(id)
    }
  }, [])

  return (
    <div className="app">
      {healthy === false && (
        <div className="health-banner">Application not healthy: {healthMsg}</div>
      )}
      {healthy === true && (
        <div className="health-banner ok">Connected to backend</div>
      )}
      <h1>Marlise v2</h1>
      <div className="container">
        <PluginList />
        <Pedalboard />
      </div>
    </div>
  )
}
