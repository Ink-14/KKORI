import { useState, useEffect } from 'react'
import { getApiBase } from '../lib/api'
import { WORD_TAGS, DEFAULT_WORD_TAG, type WordTag } from '../constants/wordAdd'
import './wordAdd.css'

type WordEntry = {
  word: string
  tag: WordTag
}

function WordAdd() {
  const [word, setWord] = useState('')
  const [tag, setTag] = useState<WordTag>(DEFAULT_WORD_TAG)
  const [entries, setEntries] = useState<WordEntry[]>([])
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    getApiBase()
      .then(base => fetch(`${base}/words`))
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: WordEntry[]) => setEntries(data))
      .catch(() => {})
  }, [])

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
        body: JSON.stringify({ words: entries }),
      })
      if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
      const saved: WordEntry[] = await fetch(`${base}/words`).then(r => r.json())
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

  return (
    <div className="wordadd-wrap">
      <div className="wordadd-inner">
        <h1>단어 추가</h1>

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
                <span className={`wordadd-badge wordadd-badge--${entry.tag === '고유명사' ? 'proper' : 'common'}`}>
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
