import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './BankLibrary.css'

interface Pedalboard {
  id: string
  title: string
  plugins: number
  modified: string
}

interface Bank {
  id: string
  title: string
  description?: string
  pedalboards: Pedalboard[]
  created: string
  modified: string
}

interface BankLibraryProps {
  onBankSelect?: (bank: Bank) => void
  onPedalboardSelect?: (pedalboard: Pedalboard, bankId: string) => void
}

export default function BankLibrary({ onBankSelect, onPedalboardSelect }: BankLibraryProps) {
  const [banks, setBanks] = useState<Bank[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedBankId, setSelectedBankId] = useState<string | null>(null)
  const [newBank, setNewBank] = useState({
    title: '',
    description: ''
  })

  useEffect(() => {
    loadBanks()
  }, [])

  const loadBanks = async () => {
    try {
      setLoading(true)
      // In a real implementation, this would call the API
      // For now, we'll show placeholder data
      const mockBanks: Bank[] = [
        {
          id: '1',
          title: 'My Banks',
          description: 'Personal pedalboard collection',
          created: '2024-01-01',
          modified: '2024-01-15',
          pedalboards: [
            {
              id: 'pb1',
              title: 'Clean Tone',
              plugins: 3,
              modified: '2024-01-15'
            },
            {
              id: 'pb2',
              title: 'Rock Rig',
              plugins: 5,
              modified: '2024-01-14'
            }
          ]
        },
        {
          id: '2',
          title: 'Factory Banks',
          description: 'Pre-installed pedalboards',
          created: '2024-01-01',
          modified: '2024-01-01',
          pedalboards: [
            {
              id: 'pb3',
              title: 'Studio Reverb',
              plugins: 2,
              modified: '2024-01-01'
            },
            {
              id: 'pb4',
              title: 'Bass Amp',
              plugins: 4,
              modified: '2024-01-01'
            }
          ]
        }
      ]
      setBanks(mockBanks)
    } catch (error) {
      console.error('Failed to load banks:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredBanks = banks.filter(bank =>
    bank.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (bank.description && bank.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const handleCreateBank = async () => {
    if (!newBank.title.trim()) return

    try {
      // In a real implementation, this would call the API
      const newBankData: Bank = {
        id: Date.now().toString(),
        title: newBank.title,
        description: newBank.description,
        pedalboards: [],
        created: new Date().toISOString().split('T')[0],
        modified: new Date().toISOString().split('T')[0]
      }

      setBanks(prev => [...prev, newBankData])
      setNewBank({ title: '', description: '' })
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create bank:', error)
    }
  }

  const handleBankSelect = (bank: Bank) => {
    setSelectedBankId(bank.id)
    onBankSelect?.(bank)
  }

  const handlePedalboardSelect = (pedalboard: Pedalboard, bankId: string) => {
    onPedalboardSelect?.(pedalboard, bankId)
  }

  return (
    <div className="bank-library">
      <div className="box">
        <header>
          <h1 className="bottom top">
            Banks Library
          </h1>
          <div className="form-group">
            <input
              id="searchBank"
              className="form-control"
              maxLength={20}
              placeholder="Filter by keyword(s)"
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoComplete="off"
            />
          </div>
          <div className="bank-actions">
            <button
              className="bank-action-btn secondary"
              onClick={() => setShowCreateModal(true)}
            >
              New Bank
            </button>
          </div>
        </header>

        <div className="banks">
          {loading ? (
            <div className="loading">
              <div className="mod-loading"></div>
              <p>Loading banks...</p>
            </div>
          ) : filteredBanks.length === 0 ? (
            <div className="empty-state">
              <h3>No banks found</h3>
              <p>Create your first bank to organize your pedalboards.</p>
              <button
                className="create-first-btn"
                onClick={() => setShowCreateModal(true)}
              >
                Create Bank
              </button>
            </div>
          ) : (
            filteredBanks.map(bank => (
              <div
                key={bank.id}
                className={`bank-item ${selectedBankId === bank.id ? 'selected' : ''}`}
                onClick={() => handleBankSelect(bank)}
              >
                <div className="bank-header">
                  <h3>{bank.title}</h3>
                  <div className="bank-meta">
                    <div className="bank-stats">
                      <span className="bank-stat">
                        📁 {bank.pedalboards.length} pedalboard{bank.pedalboards.length !== 1 ? 's' : ''}
                      </span>
                      <span className="bank-stat">
                        📅 Modified {bank.modified}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bank-content">
                  {bank.description && (
                    <p style={{ margin: '0 0 15px 0', color: 'var(--mod-text-secondary)', fontSize: '14px' }}>
                      {bank.description}
                    </p>
                  )}
                  <div className="pedalboards-grid">
                    {bank.pedalboards.map(pedalboard => (
                      <div
                        key={pedalboard.id}
                        className="pedalboard-mini"
                        onClick={(e) => {
                          e.stopPropagation()
                          handlePedalboardSelect(pedalboard, bank.id)
                        }}
                      >
                        <h4>{pedalboard.title}</h4>
                        <div className="pedalboard-plugins">
                          {pedalboard.plugins} plugin{pedalboard.plugins !== 1 ? 's' : ''}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create Bank Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Bank</h2>
            <div className="form-group">
              <label htmlFor="bankTitle" style={{ display: 'block', marginBottom: '5px', color: 'var(--mod-text-primary)' }}>
                Bank Title *
              </label>
              <input
                id="bankTitle"
                className="form-control"
                type="text"
                placeholder="Enter bank name"
                value={newBank.title}
                onChange={(e) => setNewBank(prev => ({ ...prev, title: e.target.value }))}
                autoFocus
              />
            </div>
            <div className="form-group">
              <label htmlFor="bankDescription" style={{ display: 'block', marginBottom: '5px', color: 'var(--mod-text-primary)' }}>
                Description (optional)
              </label>
              <textarea
                id="bankDescription"
                className="form-control"
                placeholder="Enter bank description"
                value={newBank.description}
                onChange={(e) => setNewBank(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                style={{ resize: 'vertical', minHeight: '80px' }}
              />
            </div>
            <div className="modal-actions">
              <button
                className="cancel-btn"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>
              <button
                className="create-btn"
                onClick={handleCreateBank}
                disabled={!newBank.title.trim()}
              >
                Create Bank
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}