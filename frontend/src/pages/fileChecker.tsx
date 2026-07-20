import { useEffect, useRef, useState } from 'react'
import { getApiBase } from '../lib/api'
import './fileChecker.css'
import type { SpellErrorResponse } from '../types/spell'
import ScrollToTopButton from '../components/ScrollToTopButton'

type TooltipState = {
  visible: boolean
  text: string
  x: number
  y: number
}

declare global {
  interface Window {
    pywebview: {
      api: {
        open_file_dialog: () => Promise<string | null>
      }
    }
    onFileDropped?: (path: string) => void
  }
}

type SegmentResult = {
  metadata: string
  text: string
  errors: SpellErrorResponse[]
}

type SheetInfo = {
  name: string
  columns: string[]
  has_header: boolean
}

type ExcelConfig = {
  sheet_name: string
  text_col: string
  metadata_col: string | null
  has_header: boolean
}

type CsvConfig = {
  text_col: string
  metadata_col: string | null
  encoding: string
}

const SUPPORTED_EXTENSIONS = ['.srt', '.txt', '.xlsx', '.csv']

const CSV_ENCODINGS = [
  { value: 'utf-8', label: 'UTF-8' },
  { value: 'utf-8-sig', label: 'UTF-8 (BOM)' },
  { value: 'cp949', label: 'CP949 (한글 윈도우)' },
]

function FileChecker() {
  const [filePath, setFilePath] = useState<string | null>(null)
  const [segments, setSegments] = useState<SegmentResult[]>([])
  const [checked, setChecked] = useState(false)
  const [loading, setLoading] = useState(false)

  const [sheets, setSheets] = useState<SheetInfo[]>([])
  const [excelConfig, setExcelConfig] = useState<ExcelConfig | null>(null)

  const [csvColumns, setCsvColumns] = useState<string[]>([])
  const [csvConfig, setCsvConfig] = useState<CsvConfig | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)

  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, text: '', x: 0, y: 0 })
  const tooltipRef = useRef<HTMLDivElement>(null)

  const isExcel = filePath?.toLowerCase().endsWith('.xlsx') ?? false
  const isCSV = filePath?.toLowerCase().endsWith('.csv') ?? false
  const excelReady = !isExcel || (excelConfig !== null && excelConfig.text_col !== '')
  const csvReady = !isCSV || (csvConfig !== null && csvConfig.text_col !== '')

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
    const groups: SpellErrorResponse[][] = []
    let groupEnd = -Infinity

    for (const e of sorted) {
      const last = groups[groups.length - 1]
      if (last && e.start_index < groupEnd) {
        last.push(e)
      } else {
        groups.push([e])
      }
      groupEnd = Math.max(groupEnd, e.end_index)
    }

    const parts: React.ReactNode[] = []
    let cursor = 0

    for (const group of groups) {
      const start = group[0].start_index
      const end = Math.max(...group.map(e => e.end_index))
      if (start < cursor) continue
      if (start >= text.length) break

      if (cursor < start) parts.push(<span key={cursor}>{text.slice(cursor, start)}</span>)

      const tooltipText = group.map(e => `[${e.error_type}]\n${e.error_message}`).join('\n\n')
      parts.push(
        <span
          key={start}
          className="fc-error-word"
          onMouseEnter={(ev) => showTooltip(ev, tooltipText)}
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

  function handleDevMockFile(ext: string) {
    const mockPaths: Record<string, string> = {
      '.srt': 'C:\\mock\\sample_subtitle.srt',
      '.txt': 'C:\\mock\\sample_text.txt',
      '.xlsx': 'C:\\mock\\sample_data.xlsx',
      '.csv': 'C:\\mock\\sample_data.csv',
    }
    const path = mockPaths[ext]
    setFileError(null)
    setFilePath(path)
    setChecked(false)
    setSegments([])
    setExcelConfig(null)
    setSheets([])
    setCsvConfig(null)
    setCsvColumns([])

    if (ext === '.xlsx') {
      const mockSheets: SheetInfo[] = [
        { name: '시트1', columns: ['제목', '내용', '작성자'], has_header: true },
        { name: '시트2', columns: ['날짜', '텍스트'], has_header: true },
      ]
      setSheets(mockSheets)
      setExcelConfig({ sheet_name: '시트1', text_col: '내용', metadata_col: null, has_header: false })
    } else if (ext === '.csv') {
      const mockColumns = ['제목', '겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트겁나긴텍스트', '날짜']
      setCsvColumns(mockColumns)
      setCsvConfig({ text_col: '본문', metadata_col: null, encoding: 'utf-8' })
    }
  }

  async function loadFile(path: string) {
    const ext = path.toLowerCase().match(/\.[^.]+$/)?.[0] ?? ''
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      setFileError(`지원하지 않는 파일 형식입니다: ${ext || '(확장자 없음)'}`)
      return
    }

    setFileError(null)
    setFilePath(path)
    setChecked(false)
    setSegments([])
    setExcelConfig(null)
    setSheets([])
    setCsvConfig(null)
    setCsvColumns([])

    const base = await getApiBase()

    if (path.toLowerCase().endsWith('.xlsx')) {
      const res = await fetch(`${base}/excel-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        setFileError(err?.detail ?? `파일 정보를 불러오지 못했습니다 (${res.status})`)
        setFilePath(null)
        return
      }
      const data: SheetInfo[] = await res.json()
      setSheets(data)
      if (data.length > 0) {
        setExcelConfig({ sheet_name: data[0].name, text_col: data[0].columns[0] ?? '', metadata_col: null, has_header: data[0].has_header })
      }
    } else if (path.toLowerCase().endsWith('.csv')) {
      const res = await fetch(`${base}/csv-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, encoding: 'utf-8' }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        setFileError(err?.detail ?? `파일 정보를 불러오지 못했습니다 (${res.status})`)
        setFilePath(null)
        return
      }
      const columns: string[] = await res.json()
      setCsvColumns(columns)
      setCsvConfig({ text_col: columns[0] ?? '', metadata_col: null, encoding: 'utf-8' })
    }
  }

  async function handlePickFile() {
    const path = await window.pywebview.api.open_file_dialog()
    if (!path) return
    await loadFile(path)
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }

  useEffect(() => {
    window.onFileDropped = (path: string) => {
      void loadFile(path)
    }
    return () => {
      window.onFileDropped = undefined
    }
  }, [])

  async function handleCsvEncodingChange(encoding: string) {
    if (!filePath || !csvConfig) return
    const updatedConfig = { ...csvConfig, encoding }
    setCsvConfig(updatedConfig)

    const base = await getApiBase()
    const res = await fetch(`${base}/csv-info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, encoding }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      setFileError(err?.detail ?? `CSV 정보를 불러오지 못했습니다 (${res.status})`)
      return
    }
    const columns: string[] = await res.json()
    setCsvColumns(columns)
    setCsvConfig({ ...updatedConfig, text_col: columns[0] ?? '', metadata_col: null })
  }

  async function handleCheck() {
    if (!filePath) return
    setLoading(true)
    setFileError(null)
    try {
      const base = await getApiBase()
      const body: { path: string; excel_config?: ExcelConfig; csv_config?: CsvConfig } = { path: filePath }
      if (isExcel && excelConfig) body.excel_config = excelConfig
      if (isCSV && csvConfig) body.csv_config = csvConfig
      const res = await fetch(`${base}/file-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        setFileError(err?.detail ?? `검사에 실패했습니다 (${res.status})`)
        return
      }
      const data: SegmentResult[] = await res.json()
      setSegments(data)
      setChecked(true)
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setFilePath(null)
    setSegments([])
    setChecked(false)
    setExcelConfig(null)
    setSheets([])
    setCsvConfig(null)
    setCsvColumns([])
    setFileError(null)
  }

  const currentSheetColumns = sheets.find(s => s.name === excelConfig?.sheet_name)?.columns ?? []

  const fileName = filePath ? filePath.split(/[\\/]/).pop() : null
  const errorSegments = segments.filter(s => s.errors.length > 0)
  const totalErrors = errorSegments.reduce((sum, s) => sum + s.errors.length, 0)

  return (
    <div className="fc-wrap" onDragOver={handleDragOver} onDrop={handleDrop}>
      <div className="fc-inner">
        <div className="fc-file-row">
          <button className="fc-pick-btn" onClick={handlePickFile}>
            파일 선택
          </button>
          {fileName && <span className="fc-filename">{fileName}</span>}
        </div>

        {!window.pywebview && (
          <div className="fc-dev-mock">
            <span className="fc-dev-label">DEV</span>
            {SUPPORTED_EXTENSIONS.map(ext => (
              <button key={ext} className="fc-dev-btn" onClick={() => handleDevMockFile(ext)}>
                {ext}
              </button>
            ))}
          </div>
        )}

        {fileError && <div className="fc-file-error">{fileError}</div>}

        {isExcel && excelConfig && (
          <div className="fc-excel-config">
            <div className="fc-excel-config-title">엑셀 설정</div>
            <div className="fc-excel-config-row">
              <label>시트</label>
              <select
                value={excelConfig.sheet_name}
                onChange={e => {
                  const name = e.target.value
                  const sheet = sheets.find(s => s.name === name)
                  const cols = sheet?.columns ?? []
                  setExcelConfig({ sheet_name: name, text_col: cols[0] ?? '', metadata_col: null, has_header: sheet?.has_header ?? true })
                }}
              >
                {sheets.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
              </select>
            </div>
            <div className="fc-excel-config-row">
              <label>검사할 열</label>
              <select
                value={excelConfig.text_col}
                onChange={e => setExcelConfig({ ...excelConfig, text_col: e.target.value })}
              >
                {currentSheetColumns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="fc-excel-config-row">
              <label>정보 열<span className="fc-optional">(선택)</span></label>
              <select
                value={excelConfig.metadata_col ?? ''}
                onChange={e => setExcelConfig({ ...excelConfig, metadata_col: e.target.value || null })}
              >
                <option value="">없음 (행 번호 사용)</option>
                {currentSheetColumns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        )}

        {isCSV && csvConfig && (
          <div className="fc-csv-config">
            <div className="fc-csv-config-title">CSV 설정</div>
            <div className="fc-excel-config-row">
              <label>인코딩</label>
              <select
                value={csvConfig.encoding}
                onChange={e => handleCsvEncodingChange(e.target.value)}
              >
                {CSV_ENCODINGS.map(enc => (
                  <option key={enc.value} value={enc.value}>{enc.label}</option>
                ))}
              </select>
            </div>
            <div className="fc-excel-config-row">
              <label>검사할 열</label>
              <select
                value={csvConfig.text_col}
                onChange={e => setCsvConfig({ ...csvConfig, text_col: e.target.value })}
              >
                {csvColumns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="fc-excel-config-row">
              <label>메타데이터 열<span className="fc-optional">(선택)</span></label>
              <select
                value={csvConfig.metadata_col ?? ''}
                onChange={e => setCsvConfig({ ...csvConfig, metadata_col: e.target.value || null })}
              >
                <option value="">없음 (행 번호 사용)</option>
                {csvColumns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        )}

        <div className="fc-btn-row">
          {checked && (
            totalErrors === 0
              ? <span className="fc-no-error">✓ 맞춤법 오류가 없습니다.</span>
              : <span className="fc-error-summary">총 {totalErrors}개의 오류가 발견되었습니다.</span>
          )}
          <div className="fc-btn-group">
            <button className="fc-btn fc-btn--clear" onClick={handleClear} disabled={!filePath}>지우기</button>
            <button className="fc-btn" onClick={handleCheck} disabled={!filePath || !excelReady || !csvReady || loading}>
              {loading ? '검사 중...' : '검사하기'}
            </button>
          </div>
        </div>

        {!filePath && !checked && (
          <div className="fc-guide">
            <div className="fc-guide-item">
              <span className="fc-guide-icon">📂</span>
              <div>
                <strong>파일 선택</strong>
                <p>파일 선택 버튼을 누르거나 파일을 끌어다 놓으세요.</p>
                <p>지원 확장자: .xlsx, .csv, .txt, .srt</p>
              </div>
            </div>
            <div className="fc-guide-item">
              <span className="fc-guide-icon">🔍</span>
              <div>
                <strong>검사하기</strong>
                <p>버튼을 누르면 파일의 맞춤법을 검사합니다.</p>
              </div>
            </div>
            <div className="fc-guide-item">
              <span className="fc-guide-icon">💡</span>
              <div>
                <strong>오류 확인</strong>
                <p>오류가 있는 텍스트가 표시됩니다.</p>
              </div>
            </div>
          </div>
        )}

        {checked && errorSegments.length === 0 && (
          <div className="fc-clean">✓ 맞춤법 오류가 없습니다.</div>
        )}

        {checked && errorSegments.length > 0 && (
          <div className="fc-results">
            {errorSegments.map((seg, i) => (
              <div key={i} className="fc-segment">
                <div className="fc-segment-meta">{seg.metadata}</div>
                <div className="fc-segment-text">
                  {renderHighlighted(seg.text, seg.errors)}
                </div>
                <ul className="fc-error-list">
                  {seg.errors.map((e, j) => (
                    <li key={j} className="fc-error-item">
                      <span className="fc-error-badge">{e.error_type}</span>
                      <span className="fc-error-msg">{e.error_message}</span>
                      {e.detailed && (
                        <span
                          className="fc-detailed-badge"
                          onMouseEnter={(ev) => showTooltip(ev, e.detailed)}
                          onMouseLeave={hideTooltip}
                        >?</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>

      {tooltip.visible && (
        <div ref={tooltipRef} className="fc-tooltip">
          {tooltip.text}
        </div>
      )}
      <ScrollToTopButton />
    </div>
  )
}

export default FileChecker
