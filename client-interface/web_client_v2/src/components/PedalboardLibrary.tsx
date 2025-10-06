import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './PedalboardLibrary.css'

interface Pedalboard {
  id: string
  title: string
  uri?: string
  thumbnail?: string
  category?: string
  author?: string
}

interface PedalboardLibraryProps {
  onPedalboardSelect?: (pedalboard: Pedalboard) => void
}

export default function PedalboardLibrary({ onPedalboardSelect }: PedalboardLibraryProps) {
  const [pedalboards, setPedalboards] = useState<Pedalboard[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPedalboards()
  }, [])

  const loadPedalboards = async () => {
    try {
      setLoading(true)
      // In a real implementation, this would call the API
      // For now, we'll show placeholder data
      const mockPedalboards: Pedalboard[] = [
        {
          id: '1',
          title: 'Clean Tone',
          author: 'MOD Team',
          category: 'factory',
          thumbnail: '/static/img/default-pedalboard.png'
        },
        {
          id: '2',
          title: 'Rock Rig',
          author: 'User',
          category: 'user',
          thumbnail: '/static/img/default-pedalboard.png'
        }
      ]
      setPedalboards(mockPedalboards)
    } catch (error) {
      console.error('Failed to load pedalboards:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredPedalboards = pedalboards.filter(pb =>
    pb.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (pb.author && pb.author.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const userPedalboards = filteredPedalboards.filter(pb => pb.category === 'user')
  const factoryPedalboards = filteredPedalboards.filter(pb => pb.category === 'factory')

  return (
    <div className="pedalboard-library">
      <div className="box">
        <header>
          <h1 className="bottom top">
            Pedalboards Library
          </h1>
          <div className="form-group">
            <input
              id="searchPedalboard"
              className="form-control"
              maxLength={20}
              placeholder="Filter by keyword(s)"
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoComplete="off"
            />
          </div>
          <a
            href="http://pedalboards.moddevices.com/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              float: 'right',
              color: '#AAA',
              fontSize: '1.1em',
              marginRight: '30px'
            }}
          >
            <img
              style={{
                width: '1.2em',
                height: '1.2em',
                opacity: 0.6,
                verticalAlign: 'middle'
              }}
              src="/static/img/icons/25/language.png"
              alt=""
            />
            <span style={{ verticalAlign: 'middle' }}>
              Browse Online Pedalboards
            </span>
          </a>
          <span className="view-modes">
            <i
              id="view-mode-grid"
              className={`view-mode icon-th-1 ${viewMode === 'grid' ? 'selected' : ''}`}
              onClick={() => setViewMode('grid')}
            ></i>
            <i
              id="view-mode-list"
              className={`view-mode icon-th-list ${viewMode === 'list' ? 'selected' : ''}`}
              onClick={() => setViewMode('list')}
            ></i>
          </span>
        </header>

        <div className="pedalboards">
          {/* User Pedalboards */}
          {userPedalboards.length > 0 && (
            <div className="clearfix">
              <div id="user-pedalboards-separator" style={{ display: userPedalboards.length > 0 ? 'block' : 'none' }}>
                <span className="separator-title">User Pedalboards</span>
                <div className="separator separator-user"></div>
              </div>
              <div className={`js-pedalboards js-user-pedalboards ${viewMode}`}>
                {userPedalboards.map(pedalboard => (
                  <div
                    key={pedalboard.id}
                    className="pedalboard-item"
                    onClick={() => onPedalboardSelect?.(pedalboard)}
                  >
                    <div className="pedalboard-thumbnail">
                      <img src={pedalboard.thumbnail || '/static/img/default-pedalboard.png'} alt={pedalboard.title} />
                    </div>
                    <div className="pedalboard-info">
                      <h3>{pedalboard.title}</h3>
                      {pedalboard.author && <p className="author">by {pedalboard.author}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Factory Pedalboards */}
          {factoryPedalboards.length > 0 && (
            <div id="factory-pedalboards-section" className="clearfix">
              <span className="separator-title">Factory Pedalboards</span>
              <div className="separator separator-factory"></div>
              <div className={`js-pedalboards js-factory-pedalboards ${viewMode}`}>
                {factoryPedalboards.map(pedalboard => (
                  <div
                    key={pedalboard.id}
                    className="pedalboard-item"
                    onClick={() => onPedalboardSelect?.(pedalboard)}
                  >
                    <div className="pedalboard-thumbnail">
                      <img src={pedalboard.thumbnail || '/static/img/default-pedalboard.png'} alt={pedalboard.title} />
                    </div>
                    <div className="pedalboard-info">
                      <h3>{pedalboard.title}</h3>
                      {pedalboard.author && <p className="author">by {pedalboard.author}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="loading">
              <div className="mod-loading"></div>
              <p>Loading pedalboards...</p>
            </div>
          )}

          {!loading && filteredPedalboards.length === 0 && (
            <div className="no-results">
              <p>No pedalboards found matching your search.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}