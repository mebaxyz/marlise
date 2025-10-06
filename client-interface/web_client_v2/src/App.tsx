import { useState, useEffect } from 'react'
import axios from 'axios'
import PluginList from './components/PluginList'
import Pedalboard from './components/Pedalboard'
import PedalboardLibrary from './components/PedalboardLibrary'
import BankLibrary from './components/BankLibrary'
import Settings from './components/Settings'
import MainMenu from './components/MainMenu'
import './styles/index.css'

interface HealthData {
  service: string
  status: string
}

type ViewType = 'pedalboard' | 'pedalboard-library' | 'bank' | 'plugin-list' | 'settings'

export default function App() {
  // show banner by default until healthcheck confirms OK
  const [healthy, setHealthy] = useState<boolean | null>(false)
  const [healthMsg, setHealthMsg] = useState<string>('Waiting for backend...')
  const [currentView, setCurrentView] = useState<ViewType>('pedalboard')

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

  const renderCurrentView = () => {
    switch (currentView) {
      case 'pedalboard':
        return (
          <div className="mod-pedalboard-view">
            {/* Main Pedalboard Area */}
            <div className="mod-pedalboard-container">
              <Pedalboard />
            </div>

            {/* Horizontal Plugin Constructor at Bottom */}
            <div className="mod-plugin-constructor">
              <PluginList />
            </div>
          </div>
        )
      case 'pedalboard-library':
        return <PedalboardLibrary />
      case 'bank':
        return <BankLibrary />
      case 'plugin-list':
        return (
          <div className="mod-fullscreen-view">
            <PluginList />
          </div>
        )
      case 'settings':
        return <Settings />
      default:
        return null
    }
  }

  return (
    <div className="mod-layout">
      {/* Health Status Banner */}
      {healthy === false && (
        <div className="mod-health-banner error">
          Application not healthy: {healthMsg}
        </div>
      )}
      {healthy === true && (
        <div className="mod-health-banner">
          🟢 Marlise v2 - Connected to backend
        </div>
      )}
      
      {/* Main Content */}
      <div className="mod-main">
        <div className="mod-content">
          {renderCurrentView()}
        </div>
      </div>
      
      {/* Main Menu */}
      <div className="mod-footer">
        <MainMenu 
          currentView={currentView}
          onViewChange={setCurrentView}
        />
      </div>
    </div>
  )
}
