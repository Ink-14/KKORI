import { useState } from 'react'
import './checker.css'

type SpellErrorResponse = {
  error_type: string
  error_message: string
  start_index: number
  end_index: number
  rule_id: string
}

function renderHighlighted(text: string, errors: SpellErrorResponse[]) {
  if (!errors.length) return <span>{text}</span>

  const sorted = [...errors].sort((a, b) => a.start_index - b.start_index || a.end_index - b.end_index)
  const parts: React.ReactNode[] = []
  let cursor = 0

  for (const e of sorted) {
    const start = e.start_index
    const end = e.end_index
    if (start < cursor) continue
    if (start >= text.length) break

    if (cursor < start) parts.push(<span key={cursor}>{text.slice(cursor, start)}</span>)

    parts.push(
      <span
        key={start}
        className="checker-error-word"
        data-tooltip={`[${e.error_type}]\n${e.error_message}`}
      >
        {text.slice(start, end)}
      </span>
    )
    cursor = end
  }

  if (cursor < text.length) parts.push(<span key={cursor}>{text.slice(cursor)}</span>)
  return <>{parts}</>
}

function Checker() {
  const [inputText, setInputText] = useState('')
  const [errors, setErrors] = useState<SpellErrorResponse[]>([])
  const [checked, setChecked] = useState(false)

  async function handleCheck() {
    const res = await fetch('/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText }),
    })
    const data: SpellErrorResponse[] = await res.json()
    setErrors(data)
    setChecked(true)
  }

  return (
    <div className="checker-wrap">
      <div className="checker-inner">
        <h1>맞춤법 검사기</h1>

        <textarea
          className="checker-textarea"
          placeholder="검사할 텍스트를 입력하세요..."
          value={inputText}
          onChange={(e) => { setInputText(e.target.value); setChecked(false) }}
        />

        <div className="checker-btn-row">
          {checked && (
            errors.length === 0
              ? <span className="checker-no-error">✓ 맞춤법 오류가 없습니다.</span>
              : <span className="checker-error-summary">총 {errors.length}개의 오류가 발견되었습니다.</span>
          )}
          <button className="checker-btn" onClick={handleCheck}>검사하기</button>
        </div>

        {checked && inputText && (
          <div className="checker-result">
            <div className="checker-preview">
              {renderHighlighted(inputText, errors)}
            </div>
            {errors.length > 0 && (
              <ul className="checker-error-list">
                {errors.map((e, i) => (
                  <li key={i} className="checker-error-item">
                    <span className="checker-error-badge">{e.error_type}</span>
                    <span className="checker-error-msg">{e.error_message}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Checker
