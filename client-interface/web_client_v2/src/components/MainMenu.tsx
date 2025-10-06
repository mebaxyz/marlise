type ViewType = 'pedalboard' | 'pedalboard-library' | 'plugin-list'

interface MainMenuProps {
  currentView: ViewType
  onViewChange: (view: ViewType) => void
}

export default function MainMenu({ currentView, onViewChange }: MainMenuProps) {
  const systemStats = {
    cpu: 45,
    ram: 67,
    xruns: 0
  }

  const menuItems = [
    { id: 'pedalboard' as ViewType, icon: 'pedalboards', label: 'Pedalboard' },
    { id: 'plugin-list' as ViewType, icon: 'plugins', label: 'Plugin Constructor' },
    { id: 'pedalboard-library' as ViewType, icon: 'pedalboards', label: 'Pedalboards Library' },
  ]

  return (
    <div className="main-menu">
      {menuItems.map(item => (
        <div
          key={item.id}
          className={`main-menu-item ${item.icon} ${currentView === item.id ? 'active' : ''}`}
          title={item.label}
          onClick={() => onViewChange(item.id)}
        />
      ))}

      <div className="main-menu-status">
        <div className="status-item cpu">
          CPU {systemStats.cpu}%
        </div>
        <div className="status-item ram">
          RAM {systemStats.ram}%
        </div>
        <div className="status-item midi">
          MIDI
        </div>
      </div>

      <div className="main-menu-settings" title="Settings" />
    </div>
  )
}