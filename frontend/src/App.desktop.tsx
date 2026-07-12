import { useState } from 'react'
import Checker from './pages/checker'
import FileChecker from './pages/fileChecker'
import WordAdd from './pages/wordAdd'
import Settings from './pages/settings'
import Info from './pages/info'
import './App.desktop.css'

type Tab = 'checker' | 'fileChecker' | 'wordAdd' | 'settings' | 'info'

const tabs: { id: Tab; label: string }[] = [
  { id: 'checker', label: '맞춤법 검사기' },
  { id: 'fileChecker', label: '파일 검사' },
  { id: 'wordAdd', label: '단어 추가' },
  { id: 'settings', label: '설정' },
  { id: 'info', label: '도움말' },
]

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('checker')

  return (
    <div className="desktop-layout">
      <nav className="desktop-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`desktop-tab${activeTab === tab.id ? ' desktop-tab--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main className="desktop-content">
        {tabs.map(tab => (
          <div key={tab.id} style={{ display: activeTab === tab.id ? 'contents' : 'none' }}>
            {tab.id === 'checker' && <Checker />}
            {tab.id === 'fileChecker' && <FileChecker />}
            {tab.id === 'wordAdd' && <WordAdd />}
            {tab.id === 'settings' && <Settings />}
            {tab.id === 'info' && <Info />}
          </div>
        ))}
      </main>
    </div>
  )
}

export default App
