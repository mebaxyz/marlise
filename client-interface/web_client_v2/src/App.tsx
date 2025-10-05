import React, { useEffect, useState } from 'react'
import axios from 'axios'
import PluginList from './components/PluginList'
import Pedalboard from './components/Pedalboard'

export default function App() {
  // show banner by default until healthcheck confirms OK
  const [healthy, setHealthy] = useState<boolean | null>(false)
  const [healthMsg, setHealthMsg] = useState<string>('Waiting for backend...')

  useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        // short timeout so healthcheck won't block page load
        // Try the lightweight adapter API health first (fast and local)
        let resp = await axios.get('/api/health', { timeout: 1000 }).catch(() => null)
        if (!resp) {
          // fallback to session-level health which may call session_manager over ZMQ
          resp = await axios.get('/api/session/health', { timeout: 2000 })
        }
        if (!mounted) return
        // Accept either {ok:true} or 200
        if (resp && resp.status === 200 && (resp.data == null || resp.data.ok === true || resp.data.status === 'ok')) {
          setHealthy(true)
          setHealthMsg('')
        } else if (resp) {
          setHealthy(false)
          setHealthMsg(JSON.stringify(resp.data ?? resp.status))
        } else {
          setHealthy(false)
          setHealthMsg('no response')
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
