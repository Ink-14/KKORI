import { useState, useRef, useEffect } from 'react'
import './checker.css'

type SpellErrorResponse = {
  error_type: string
  error_message: string
  start_index: number
  end_index: number
  rule_id: string
}

type TooltipState = {
  visible: boolean
  text: string
  x: number
  y: number
}

function Checker() {
  const [inputText, setInputText] = useState('')
  const [errors, setErrors] = useState<SpellErrorResponse[]>([])
  const [checked, setChecked] = useState(false)
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, text: '', x: 0, y: 0 })
  const tooltipRef = useRef<HTMLDivElement>(null)

  async function handleCheck() {
    const res = await fetch(`${__API_BASE__}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText }),
    })
    const data: SpellErrorResponse[] = await res.json()
    setErrors(data)
    setChecked(true)
  }

  function handleClear() {
    setInputText('')
    setErrors([])
    setChecked(false)
  }

  function showTooltip(e: React.MouseEvent, text: string) {
    const target = e.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    setTooltip({ visible: true, text, x: rect.left + rect.width / 2, y: rect.top })
  }

  function hideTooltip() {
    setTooltip(prev => ({ ...prev, visible: false }))
  }

  // 툴팁이 화면 밖으로 나가지 않도록 위치 조정
  useEffect(() => {
    if (!tooltip.visible || !tooltipRef.current) return
    const el = tooltipRef.current
    const elRect = el.getBoundingClientRect()
    const vw = window.innerWidth
    const margin = 8

    let left = tooltip.x - elRect.width / 2
    if (left < margin) left = margin
    if (left + elRect.width > vw - margin) left = vw - margin - elRect.width

    let top = tooltip.y - elRect.height - 10
    if (top < margin) top = tooltip.y + 28  // 위 공간 없으면 아래로

    el.style.left = `${left}px`
    el.style.top = `${top}px`
  }, [tooltip])

  function renderHighlighted(text: string, errs: SpellErrorResponse[]) {
    if (!errs.length) return <span>{text}</span>

    const sorted = [...errs].sort((a, b) => a.start_index - b.start_index || a.end_index - b.end_index)
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
          onMouseEnter={(ev) => showTooltip(ev, `[${e.error_type}]\n${e.error_message}`)}
          onMouseLeave={hideTooltip}
        >
          {text.slice(start, end)}
        </span>
      )
      cursor = end
    }

    if (cursor < text.length) parts.push(<span key={cursor}>{text.slice(cursor)}</span>)
    return <>{parts}</>
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
          <div className="checker-btn-group">
            <button className="checker-btn checker-btn--clear" onClick={handleClear} disabled={!inputText}>지우기</button>
            <button className="checker-btn" onClick={handleCheck}>검사하기</button>
          </div>
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

      {tooltip.visible && (
        <div ref={tooltipRef} className="checker-tooltip">
          {tooltip.text}
        </div>
      )}
    </div>
  )
}

export default Checker
