import { useState, useEffect } from 'react'
import { getApiBase } from '../lib/api'
import { WORD_TAGS, DEFAULT_WORD_TAG, WORD_TAG_BADGE, type WordTag } from '../constants/wordAdd'
import './wordAdd.css'

type WordEntry = {
  word: string
  tag: WordTag
}

function WordAdd() {
  const [scope, setScope] = useState<string>('global')
  const [projectNames, setProjectNames] = useState<string[]>([])
  const [entries, setEntries] = useState<WordEntry[]>([])
  const [word, setWord] = useState('')
  const [tag, setTag] = useState<WordTag>(DEFAULT_WORD_TAG)
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [newProjectName, setNewProjectName] = useState('')
  const [showNewInput, setShowNewInput] = useState(false)

  useEffect(() => {
    async function init() {
      const base = await getApiBase()
      const projectData: { names: string[]; active: string | null } = await fetch(`${base}/projects`).then(r => r.json())
      const initialScope = projectData.active ?? 'global'
      setProjectNames(projectData.names)
      setScope(initialScope)
      const words: WordEntry[] = await fetch(`${base}/words?scope=${encodeURIComponent(initialScope)}`).then(r => r.json())
      setEntries(words)
    }
    init().catch(() => {})
  }, [])

  async function handleScopeChange(newScope: string) {
    try {
      const base = await getApiBase()
      await fetch(`${base}/activate-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: newScope === 'global' ? null : newScope }),
      })
      const words: WordEntry[] = await fetch(`${base}/words?scope=${encodeURIComponent(newScope)}`).then(r => r.json())
      setScope(newScope)
      setEntries(words)
      setStatus('idle')
    } catch {}
  }

  async function handleCreateProject() {
    const name = newProjectName.trim()
    if (!name) return
    try {
      const base = await getApiBase()
      const res = await fetch(`${base}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      })
      if (!res.ok) {
        const data = await res.json()
        setErrorMsg(data.detail ?? '단어장 생성 실패')
        setStatus('error')
        return
      }
      setProjectNames(prev => [...prev, name])
      setNewProjectName('')
      setShowNewInput(false)
      await handleScopeChange(name)
    } catch {}
  }

  async function handleDeleteProject() {
    if (scope === 'global') return
    try {
      const base = await getApiBase()
      await fetch(`${base}/projects/${encodeURIComponent(scope)}`, { method: 'DELETE' })
      setProjectNames(prev => prev.filter(n => n !== scope))
      await handleScopeChange('global')
    } catch {}
  }

  function handleAdd() {
    const trimmed = word.trim()
    if (!trimmed) return
    if (entries.some(e => e.word === trimmed && e.tag === tag)) return
    setEntries(prev => [...prev, { word: trimmed, tag }])
    setWord('')
    setStatus('idle')
  }

  function handleRemove(index: number) {
    setEntries(prev => prev.filter((_, i) => i !== index))
  }

  async function handleSave() {
    setStatus('loading')
    setErrorMsg('')
    try {
      const base = await getApiBase()
      const res = await fetch(`${base}/add-words`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ words: entries, scope }),
      })
      if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
      const saved: WordEntry[] = await fetch(`${base}/words?scope=${encodeURIComponent(scope)}`).then(r => r.json())
      setEntries(saved)
      setStatus('success')
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : '알 수 없는 오류')
      setStatus('error')
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleAdd()
  }

  function handleNewProjectKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleCreateProject()
    if (e.key === 'Escape') { setShowNewInput(false); setNewProjectName('') }
  }

  return (
    <div className="wordadd-wrap">
      <div className="wordadd-inner">

        <div className="wordadd-project-row">
          <span className="wordadd-project-label">단어장</span>
          <select
            className="wordadd-select wordadd-project-select"
            value={scope}
            onChange={e => handleScopeChange(e.target.value)}
          >
            <option value="global">공통</option>
            {projectNames.map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>

          {showNewInput ? (
            <>
              <input
                className="wordadd-input wordadd-project-input"
                value={newProjectName}
                onChange={e => setNewProjectName(e.target.value)}
                onKeyDown={handleNewProjectKeyDown}
                placeholder="단어장 이름"
                autoFocus
              />
              <button
                className="wordadd-btn wordadd-btn--add"
                onClick={handleCreateProject}
                disabled={!newProjectName.trim()}
                type="button"
              >
                확인
              </button>
              <button
                className="wordadd-btn wordadd-btn--ghost"
                onClick={() => { setShowNewInput(false); setNewProjectName('') }}
                type="button"
              >
                취소
              </button>
            </>
          ) : (
            <button
              className="wordadd-btn wordadd-btn--ghost"
              onClick={() => setShowNewInput(true)}
              type="button"
            >
              + 새 단어장
            </button>
          )}

          {scope !== 'global' && !showNewInput && (
            <button
              className="wordadd-btn wordadd-btn--danger"
              onClick={handleDeleteProject}
              type="button"
            >
              삭제
            </button>
          )}
        </div>

        <div className="wordadd-input-row">
          <input
            className="wordadd-input"
            type="text"
            placeholder="추가할 단어를 입력하세요"
            value={word}
            onChange={e => { setWord(e.target.value); setStatus('idle') }}
            onKeyDown={handleKeyDown}
          />
          <select
            className="wordadd-select"
            value={tag}
            onChange={e => setTag(e.target.value as WordTag)}
          >
            {WORD_TAGS.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button
            className="wordadd-btn wordadd-btn--add"
            onClick={handleAdd}
            disabled={!word.trim()}
            type="button"
          >
            추가
          </button>
        </div>

        {entries.length > 0 && (
          <ul className="wordadd-list">
            {entries.map((entry, i) => (
              <li key={i} className="wordadd-list-item">
                <span className="wordadd-word">{entry.word}</span>
                <span className={`wordadd-badge wordadd-badge--${WORD_TAG_BADGE[entry.tag]}`}>
                  {entry.tag}
                </span>
                <button
                  className="wordadd-remove-btn"
                  onClick={() => handleRemove(i)}
                  type="button"
                  aria-label="삭제"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}

        {entries.length === 0 && (
          <p className="wordadd-empty">추가할 단어를 입력 후 '추가' 버튼을 누르세요.</p>
        )}

        <div className="wordadd-footer">
          {status === 'success' && (
            <span className="wordadd-status wordadd-status--success">✓ 저장되었습니다.</span>
          )}
          {status === 'error' && (
            <span className="wordadd-status wordadd-status--error">{errorMsg}</span>
          )}
          <button
            className="wordadd-btn wordadd-btn--save"
            onClick={handleSave}
            disabled={status === 'loading'}
            type="button"
          >
            {status === 'loading' ? '저장 중...' : `저장 (${entries.length}개)`}
          </button>
        </div>
      </div>
    </div>
  )
}

export default WordAdd
