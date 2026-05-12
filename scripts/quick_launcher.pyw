import gzip
import importlib
import os
import pickle
import re
import sys
import threading
from datetime import datetime

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# __file__ 절대경로 보장
_script = os.path.abspath(__file__)
_project = os.path.normpath(os.path.join(os.path.dirname(_script), ".."))
_parent = os.path.dirname(_project)
_venv_site = os.path.join(_project, "venv", "Lib", "site-packages")
os.chdir(_project)
_scripts = os.path.dirname(_script)
sys.path.insert(0, _parent)
sys.path.insert(1, _venv_site)
sys.path.insert(2, _scripts)

import webview

from korean_spell_checker.tokenizations.ko_tokenizer import KoTokenizer
from korean_spell_checker.models.interface import Tag
from korean_spell_checker.engines.spell_checker import SpellChecker
from korean_spell_checker.engines.raw_searcher import RawStringSearcher
import korean_spell_checker.configs.spell_checker_config_meaning as _spell_meaning_cfg
import korean_spell_checker.configs.spell_checker_config_spacing as _spell_spacing_cfg
import korean_spell_checker.configs.spell_checker_config_specific as _spell_specific_cfg
import korean_spell_checker.configs.spell_checker_config_spelling as _spell_spelling_cfg
import korean_spell_checker.configs.spell_checker_config_warning as _spell_warning_cfg
import korean_spell_checker.configs.spell_checker_config as _spell_cfg
import korean_spell_checker.configs.raw_string_searcher_config as _raw_cfg
from korean_spell_checker.reporters.html_reporter import highlight_text, get_error_type_name
from korean_spell_checker.utils.file_io import read_txt_file, get_all_file_paths
from bktree import BKTree
from jamo import h2j

TAG_REPLACE_REGEX = re.compile(r"\<[^>]+\>")

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  :root {
    --bg: #f1f5f9;
    --surface: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --muted: #64748b;
    --subtle: #94a3b8;
    --accent: #4f46e5;
    --accent-dark: #4338ca;
    --accent-bg: rgba(79,70,229,0.07);
    --danger: #ef4444;
    --danger-dark: #dc2626;
    --danger-bg: rgba(239,68,68,0.07);
    --warning: #f59e0b;
    --warning-dark: #d97706;
    --warning-bg: rgba(245,158,11,0.09);
    --success: #10b981;
    --r-sm: 5px;
    --r: 8px;
    --r-lg: 12px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.07);
    --shadow: 0 3px 10px rgba(0,0,0,0.09), 0 1px 3px rgba(0,0,0,0.05);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Malgun Gothic', system-ui, -apple-system, sans-serif;
    font-size: 14px;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }

  /* ── 탭 헤더 ── */
  .tab-header {
    display: flex;
    background: #1e293b;
    padding: 0 16px;
    position: sticky;
    top: 0;
    z-index: 100;
    gap: 2px;
  }
  .tab-btn {
    padding: 11px 18px;
    border: none;
    background: transparent;
    color: rgba(255,255,255,0.5);
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
    letter-spacing: 0.01em;
  }
  .tab-btn:hover { color: rgba(255,255,255,0.85); }
  .tab-btn.active { color: #fff; border-bottom-color: #818cf8; }

  /* ── 탭 컨텐츠 ── */
  .tab-pane { display: none; padding: 18px 16px; }
  .tab-pane.active { display: block; }

  /* ── 공통 컴포넌트 ── */
  h2 { margin-bottom: 14px; font-size: 15px; font-weight: 600; color: var(--text); }
  textarea {
    width: 100%; height: 80px; padding: 10px 12px;
    border: 1px solid var(--border); border-radius: var(--r);
    resize: vertical; font-family: inherit; font-size: 14px;
    background: var(--surface); color: var(--text);
    outline: none; transition: border-color 0.15s, box-shadow 0.15s;
  }
  textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12);
  }
  .toolbar {
    display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap;
  }
  button {
    padding: 7px 15px; border: none; border-radius: var(--r-sm);
    cursor: pointer; font-size: 13px; font-family: inherit; font-weight: 500;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
  }
  button:active:not(:disabled) { transform: translateY(1px); }
  button:disabled { opacity: 0.42; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: #fff; box-shadow: 0 1px 3px rgba(79,70,229,0.3); }
  .btn-primary:not(:disabled):hover { background: var(--accent-dark); box-shadow: 0 2px 8px rgba(79,70,229,0.35); }
  .btn-danger  { background: var(--danger); color: #fff; box-shadow: 0 1px 3px rgba(239,68,68,0.3); }
  .btn-danger:not(:disabled):hover  { background: var(--danger-dark); box-shadow: 0 2px 8px rgba(239,68,68,0.35); }
  .btn-warning { background: var(--warning); color: #fff; box-shadow: 0 1px 3px rgba(245,158,11,0.3); }
  .btn-warning:not(:disabled):hover { background: var(--warning-dark); box-shadow: 0 2px 8px rgba(245,158,11,0.35); }
  .btn-success { background: var(--success); color: #fff; box-shadow: 0 1px 3px rgba(16,185,129,0.3); }
  .btn-success:not(:disabled):hover { background: #059669; box-shadow: 0 2px 8px rgba(16,185,129,0.35); }
  label {
    display: flex; align-items: center; gap: 6px;
    cursor: pointer; user-select: none; font-size: 13px; color: var(--muted);
  }
  label input[type="checkbox"] { width: 15px; height: 15px; accent-color: var(--accent); cursor: pointer; }
  select {
    padding: 5px 8px; border: 1px solid var(--border); border-radius: var(--r-sm);
    font-family: inherit; font-size: 13px; background: var(--surface); color: var(--text);
    cursor: pointer; outline: none;
  }
  select:focus { border-color: var(--accent); }
  select:disabled { opacity: 0.5; cursor: not-allowed; }
  .status { margin-top: 8px; font-size: 12px; color: var(--muted); min-height: 16px; }
  .result-area { margin-top: 14px; }

  /* ── 토크나이저 테이블 ── */
  table.token-table {
    width: 100%; border-collapse: collapse; background: var(--surface);
    border-radius: var(--r); overflow: hidden; box-shadow: var(--shadow);
  }
  table.token-table th {
    background: #1e293b; color: rgba(255,255,255,0.85);
    padding: 9px 12px; text-align: left; font-size: 12px;
    font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase;
  }
  table.token-table td { padding: 7px 12px; border-bottom: 1px solid var(--border); font-size: 13px; }
  table.token-table tr:last-child td { border-bottom: none; }
  table.token-table tr:hover td { background: var(--accent-bg); }
  .tag   { font-weight: 600; color: var(--accent); }
  .spaced { color: var(--danger); font-size: 11px; font-weight: 500; }

  /* ── 맞춤법 검사: 하이라이트 미리보기 ── */
  .spell-preview {
    margin-top: 12px; padding: 12px 14px; background: var(--surface);
    border: 1px solid var(--border); border-radius: var(--r); min-height: 52px;
    white-space: pre-wrap; word-break: break-word; line-height: 1.8;
    font-size: 14px; font-family: inherit; box-shadow: var(--shadow-sm);
  }
  .spell-preview:empty::before {
    content: '검사 결과가 여기에 표시됩니다.';
    color: var(--subtle);
  }
  .error-highlight {
    position: relative;
    text-decoration: underline;
    text-decoration-color: #ef4444;
    text-decoration-style: wavy;
    text-decoration-thickness: 1.5px;
    color: #dc2626;
    font-weight: 600;
    background: rgba(239,68,68,0.09);
    border-radius: 3px;
    cursor: help;
    padding: 0 1px;
  }
  .error-highlight::before {
    content: attr(data-error-msg);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 10px;
    background: #1e293b;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: var(--r);
    box-shadow: var(--shadow);
    white-space: pre-wrap;
    word-wrap: break-word;
    min-width: 200px;
    max-width: 320px;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.6;
    opacity: 0; visibility: hidden;
    transition: opacity 0.15s, visibility 0.15s;
    z-index: 9999; pointer-events: none;
  }
  .error-highlight::after {
    content: '';
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 4px;
    border: 5px solid transparent;
    border-top-color: #1e293b;
    opacity: 0; visibility: hidden;
    transition: opacity 0.15s, visibility 0.15s;
    z-index: 9999; pointer-events: none;
  }
  .error-highlight:hover::before,
  .error-highlight:hover::after { opacity: 1; visibility: visible; }

  /* ── 맞춤법 검사: 에러 목록 테이블 ── */
  table.error-table {
    width: 100%; border-collapse: collapse; background: var(--surface);
    border-radius: var(--r); overflow: hidden;
    box-shadow: var(--shadow-sm); margin-top: 12px;
  }
  table.error-table th {
    background: var(--danger); color: #fff; padding: 8px 12px;
    text-align: left; font-size: 12px; font-weight: 500; letter-spacing: 0.03em;
  }
  table.error-table td {
    padding: 7px 12px; border-bottom: 1px solid var(--border);
    font-size: 12px; vertical-align: top;
  }
  table.error-table tr:last-child td { border-bottom: none; }
  table.error-table tr:hover td { background: var(--danger-bg); }
  .err-type { font-weight: 600; color: var(--danger); white-space: nowrap; }
  .err-path { font-size: 11px; color: var(--subtle); margin-top: 3px; font-family: monospace; }
  .no-errors { color: var(--success); font-size: 13px; font-weight: 500; margin-top: 10px; }

  /* ── 사전 검색 ── */
  .dict-sticky-search {
    position: sticky;
    top: 40px;
    background: var(--bg);
    margin: 0 -16px;
    padding: 0 16px 10px;
    z-index: 50;
  }
  .dict-search-row { display: flex; gap: 8px; }
  .dict-regex-label { margin-top: 7px; }
  .dict-input {
    flex: 1; padding: 8px 12px; border: 1px solid var(--border);
    border-radius: var(--r-sm); font-size: 14px; font-family: inherit;
    background: var(--surface); color: var(--text);
    outline: none; transition: border-color 0.15s, box-shadow 0.15s;
  }
  .dict-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12);
  }
  .dict-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r); margin-top: 10px; overflow: hidden;
    box-shadow: var(--shadow-sm); transition: box-shadow 0.15s;
  }
  .dict-card:hover { box-shadow: var(--shadow); }
  .dict-card-header {
    display: flex; align-items: baseline; gap: 8px;
    padding: 10px 14px; background: var(--accent-bg); border-bottom: 1px solid var(--border);
  }
  .dict-word { font-size: 16px; font-weight: 700; color: var(--text); }
  .dict-pos-badge {
    font-size: 11px; padding: 2px 8px; border-radius: 999px;
    background: var(--accent); color: #fff; white-space: nowrap; font-weight: 500;
  }
  .dict-card-body { padding: 12px 14px; }
  .dict-sense {
    margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
  }
  .dict-sense:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
  .dict-sense-num { font-size: 12px; color: var(--subtle); margin-right: 4px; }
  .dict-definition { font-size: 13px; color: var(--text); line-height: 1.6; }
  .dict-examples { margin-top: 5px; padding-left: 12px; }
  .dict-example { font-size: 12px; color: var(--muted); line-height: 1.6; }
  .dict-example::before { content: '• '; color: var(--subtle); }
  .dict-source { font-size: 11px; color: var(--subtle); font-style: italic; margin-left: 4px; }
  .dict-no-result { color: var(--muted); font-size: 13px; margin-top: 12px; }
  .dict-not-loaded { color: var(--danger); font-size: 13px; margin-top: 12px; }

  /* ── 유사어 제안 ── */
  .dict-suggestion-box {
    margin-top: 12px; padding: 12px 14px; background: var(--warning-bg);
    border: 1px solid rgba(245,158,11,0.25); border-radius: var(--r);
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  }
  .dict-suggestion-label {
    font-size: 13px; color: var(--warning-dark); font-weight: 600; white-space: nowrap;
  }
  .dict-suggestion-chip {
    padding: 4px 12px; border: 1px solid rgba(245,158,11,0.4); border-radius: 999px;
    background: var(--surface); color: var(--text); font-size: 13px; cursor: pointer;
    font-family: inherit; font-weight: 500; transition: background 0.12s, border-color 0.12s;
  }
  .dict-suggestion-chip:hover { background: var(--warning-bg); border-color: var(--warning); }

  /* ── 폴더 읽기 ── */
  .folder-config-row {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 10px;
  }
  .folder-progress-box {
    margin-top: 10px; padding: 10px 14px; background: var(--accent-bg);
    border: 1px solid rgba(79,70,229,0.2); border-radius: var(--r);
    font-size: 13px; color: var(--accent-dark);
  }
  .label-counter {
    font-size: 13px; color: var(--muted); margin-bottom: 8px; font-weight: 500;
  }
  .label-counter strong { color: var(--accent); font-size: 15px; }
  table.folder-result-table th {
    cursor: pointer;
    user-select: none;
    position: relative;
    transition: background 0.15s;
  }
  table.folder-result-table th:hover { background: var(--danger-dark); }
  table.folder-result-table th .sort-arrow {
    display: inline-block; margin-left: 4px; opacity: 0.6; font-size: 10px;
  }
  .debug-btn {
    padding: 4px 10px; font-size: 11px;
    background: var(--muted); color: #fff;
    border-radius: var(--r-sm); cursor: pointer;
  }
  .debug-btn:hover:not(:disabled) { background: var(--text); }
  .debug-path-text {
    white-space: pre-line; font-family: monospace;
    font-size: 11px; color: var(--muted); line-height: 1.5;
  }
</style>
</head>
<body>

<div class="tab-header">
  <button class="tab-btn active" onclick="switchTab('tokenizer')">토크나이저</button>
  <button class="tab-btn"        onclick="switchTab('spell')">맞춤법 검사</button>
  <button class="tab-btn"        onclick="switchTab('dict')">사전 검색</button>
  <button class="tab-btn"        onclick="switchTab('folder')">폴더 읽기</button>
</div>

<!-- ════ 토크나이저 탭 ════ -->
<div id="pane-tokenizer" class="tab-pane active">
  <h2>토크나이저 결과 미리보기</h2>
  <textarea id="tkn-input" placeholder="토크나이징할 문장을 입력하세요.&#10;Enter로 검사, Shift+Enter로 줄바꿈"></textarea>
  <div class="toolbar">
    <button id="btn-tokenize" class="btn-primary" onclick="tokenize()">토크나이징</button>
    <button id="btn-tkn-rebuild" class="btn-warning" onclick="rebuildTokenizer()">재빌드</button>
    <label><input type="checkbox" id="detailed" checked> detailed</label>
  </div>
  <div class="status" id="tkn-status"></div>
  <div class="result-area" id="tkn-result"></div>
</div>

<!-- ════ 맞춤법 검사 탭 ════ -->
<div id="pane-spell" class="tab-pane">
  <h2>맞춤법 검사</h2>
  <textarea id="spell-input" placeholder="검사할 문장을 입력하세요.&#10;Enter로 검사, Shift+Enter로 줄바꿈"></textarea>
  <div class="toolbar">
    <button id="btn-spell-check"  class="btn-primary" onclick="runSpellCheck()">검사</button>
    <button id="btn-spell-rebuild" class="btn-warning" onclick="rebuildSpellRules()">규칙 재빌드</button>
    <div class="status" id="spell-status" style="margin-top:0; flex:1;"></div>
  </div>
  <div id="spell-preview" class="spell-preview"></div>
  <div id="spell-errors"></div>
</div>

<!-- ════ 사전 검색 탭 ════ -->
<div id="pane-dict" class="tab-pane">
  <h2>사전 검색</h2>
  <div class="dict-sticky-search">
    <div class="dict-search-row">
      <input id="dict-input" type="text" class="dict-input"
             placeholder="검색어를 입력하세요 (부분 일치 지원)">
      <button class="btn-primary" onclick="dictSearch()">검색</button>
    </div>
    <label class="dict-regex-label">
      <input type="checkbox" id="dict-regex"> 정규식 (Regex)
    </label>
  </div>
  <div class="status" id="dict-status"></div>
  <div id="dict-results"></div>
</div>

<!-- ════ 폴더 읽기 탭 ════ -->
<div id="pane-folder" class="tab-pane">
  <h2>폴더 읽어서 검사</h2>

  <div id="folder-config-area">
    <div class="folder-config-row">
      <label>
        규칙:
        <select id="folder-rule" style="margin-left:6px;">
          <option value="SPELL_CHECK_RULES">기본</option>
          <option value="TEST_SPELL_CHECK_RULES">테스트</option>
        </select>
      </label>
      <label>
        <input type="checkbox" id="folder-labeling" onchange="onLabelingToggle()">
        라벨링 모드 (ML_LABELINGS, RawString 미적용)
      </label>
    </div>
    <button id="btn-folder-start" class="btn-primary" onclick="startFolderCheck()">
      폴더 선택 후 시작
    </button>
    <div class="status" id="folder-status"></div>
  </div>

<div id="folder-labeling-area" style="display:none; margin-top:16px;">
    <div class="label-counter">
      <strong><span id="label-idx">0</span></strong> / <span id="label-total">0</span>
    </div>
    <div id="label-rule-id" style="font-size:12px; color:var(--muted); font-family:monospace; margin-bottom:6px;"></div>
    <div id="label-content" class="spell-preview"></div>
    <div class="toolbar">
      <button class="btn-warning" onclick="goBackLabel()" id="btn-label-back" disabled>뒤로 가기 (↑)</button>
      <button class="btn-success" onclick="submitLabel('0')">0: 정상/패스 (←)</button>
      <button class="btn-danger" onclick="submitLabel('1')">1: 오류/교정 (→)</button>
      <button class="btn-primary" onclick="submitLabel('SKIP')">건너뛰기 (↓)</button>
      <button class="btn-danger" onclick="abortLabeling()" style="margin-left:auto;">중단</button>
    </div>
  </div>

  <div id="folder-results-area" style="margin-top:14px;"></div>
</div>

<script>
/* ── 탭 전환 ── */
function switchTab(name) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('pane-' + name).classList.add('active');
  event.currentTarget.classList.add('active');
}

/* ════ 토크나이저 ════ */
function setTknLoading(on) {
  document.getElementById('btn-tokenize').disabled   = on;
  document.getElementById('btn-tkn-rebuild').disabled = on;
}
function setTknStatus(msg) {
  document.getElementById('tkn-status').textContent = msg;
}

function tokenize() {
  const text = document.getElementById('tkn-input').value.trim();
  if (!text) return;
  const detailed = document.getElementById('detailed').checked;
  setTknLoading(true);
  setTknStatus('토크나이징 중…');
  document.getElementById('tkn-result').innerHTML = '';

  pywebview.api.tokenize(text).then(result => {
    setTknLoading(false);
    if (result.error) { setTknStatus('오류: ' + result.error); return; }
    setTknStatus('완료 (' + result.tokens.length + '개 토큰)');
    renderTokenTable(result.tokens, detailed);
  });
}

function rebuildTokenizer() {
  setTknLoading(true);
  setTknStatus('토크나이저 재빌드 중…');
  document.getElementById('tkn-result').innerHTML = '';

  pywebview.api.rebuild_tokenizer().then(result => {
    setTknLoading(false);
    if (result.error) setTknStatus('오류: ' + result.error);
    else setTknStatus('재빌드 완료!');
  });
}

function renderTokenTable(tokens, detailed) {
  if (!tokens.length) {
    document.getElementById('tkn-result').innerHTML =
      '<div style="color:#888;margin-top:8px;">결과 없음</div>';
    return;
  }
  let headers, rows;
  if (detailed) {
    headers = ['#', 'form', 'tag', 'raw_form', 'lemma', 'word_position', 'spaced'];
    rows = tokens.map(t => [
      t.i, t.form, t.tag, t.raw_form, t.lemma, t.word_position,
      t.spaced ? '<span class="spaced">공백 있음</span>' : ''
    ]);
  } else {
    headers = ['#', 'form (base_form)', 'tag'];
    rows = tokens.map(t => [t.i, t.form + ' (' + t.base_form + ')', t.tag]);
  }
  const th = headers.map(h => '<th>' + h + '</th>').join('');
  const tbody = rows.map(cells => {
    const tds = cells.map((c, i) =>
      i === 2 ? '<td class="tag">' + c + '</td>' : '<td>' + c + '</td>'
    ).join('');
    return '<tr>' + tds + '</tr>';
  }).join('');
  document.getElementById('tkn-result').innerHTML =
    '<table class="token-table"><thead><tr>' + th + '</tr></thead><tbody>' + tbody + '</tbody></table>';
}

document.getElementById('tkn-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); tokenize(); }
});

/* ════ 맞춤법 검사 ════ */
function setSpellLoading(on) {
  document.getElementById('btn-spell-check').disabled  = on;
  document.getElementById('btn-spell-rebuild').disabled = on;
  document.getElementById('spell-input').disabled      = on;
}
function setSpellStatus(msg) {
  document.getElementById('spell-status').textContent = msg;
}

document.getElementById('spell-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runSpellCheck(); }
});

function runSpellCheck() {
  const text = document.getElementById('spell-input').value;
  if (!text.trim()) return;
  setSpellLoading(true);
  setSpellStatus('검사 중…');
  document.getElementById('spell-preview').innerHTML = '';
  document.getElementById('spell-errors').innerHTML  = '';

  pywebview.api.spell_check(text).then(result => {
    setSpellLoading(false);
    if (result.error) { setSpellStatus('오류: ' + result.error); return; }
    const cnt = result.errors.length;
    setSpellStatus(cnt > 0 ? '오류 ' + cnt + '건 발견' : '오류 없음');
    renderSpellResult(result);
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderSpellResult(result) {
  document.getElementById('spell-preview').innerHTML = result.highlighted;

  const errDiv = document.getElementById('spell-errors');
  if (!result.errors.length) {
    errDiv.innerHTML = '<div class="no-errors">오류가 없습니다.</div>';
    return;
  }
  const th = '<tr><th>#</th><th>Type</th><th>Message</th></tr>';
  const tbody = result.errors.map((e, i) => {
    const path = e.debug_path
      ? '<div class="err-path">' + escapeHtml(e.debug_path) + '</div>' : '';
    return '<tr>'
      + '<td>' + (i + 1) + '</td>'
      + '<td class="err-type">' + e.type + '</td>'
      + '<td>' + e.msg + path + '</td>'
      + '</tr>';
  }).join('');
  errDiv.innerHTML =
    '<table class="error-table"><thead>' + th + '</thead><tbody>' + tbody + '</tbody></table>';
}

/* ════ 사전 검색 ════ */
document.getElementById('dict-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') dictSearch();
});

document.getElementById('dict-regex').addEventListener('change', function() {
  const input = document.getElementById('dict-input');
  input.placeholder = this.checked
    ? '정규표현식을 입력하세요 (예: ^가나.*다$)'
    : '검색어를 입력하세요 (부분 일치 지원)';
});

function dictSearch() {
  const query = document.getElementById('dict-input').value.trim();
  if (!query) return;
  const useRegex = document.getElementById('dict-regex').checked;
  document.getElementById('dict-status').textContent = '검색 중…';
  document.getElementById('dict-results').innerHTML = '';

  pywebview.api.dict_search(query, useRegex).then(result => {
    if (result.error) {
      document.getElementById('dict-status').textContent = '';
      document.getElementById('dict-results').innerHTML =
        '<div class="dict-not-loaded">' + escapeHtml(result.error) + '</div>';
      return;
    }
    const items = result.items;
    document.getElementById('dict-status').textContent =
      items.length ? items.length + '건 (최대 100건)' : '';
    if (!items.length) {
      const sugg = result.suggestions;
      if (sugg && sugg.length) {
        document.getElementById('dict-results').innerHTML = renderSuggestions(sugg);
      } else {
        document.getElementById('dict-results').innerHTML =
          '<div class="dict-no-result">검색 결과가 없습니다.</div>';
      }
      return;
    }
    document.getElementById('dict-results').innerHTML = items.map(renderDictCard).join('');
  });
}

function renderDictCard(item) {
  const posBadges = item.pos_senses
    .filter(ps => ps.pos)
    .map(ps => '<span class="dict-pos-badge">' + escapeHtml(ps.pos) + '</span>')
    .join(' ');

  let sensesHtml = '';
  item.pos_senses.forEach(ps => {
    ps.senses.forEach((s, idx) => {
      const num = ps.senses.length > 1
        ? '<span class="dict-sense-num">' + (idx + 1) + '.</span>' : '';
      const examplesHtml = s.examples.map(ex => {
        const src = ex.source
          ? ' <span class="dict-source">(' + escapeHtml(ex.source) + ')</span>' : '';
        return '<div class="dict-example">'
          + escapeHtml(ex.example) + src + '</div>';
      }).join('');
      sensesHtml +=
        '<div class="dict-sense">'
        + '<div class="dict-definition">' + num + escapeHtml(s.definition) + '</div>'
        + (examplesHtml ? '<div class="dict-examples">' + examplesHtml + '</div>' : '')
        + '</div>';
    });
  });

  return '<div class="dict-card">'
    + '<div class="dict-card-header">'
    + '<span class="dict-word">' + escapeHtml(item.word) + '</span>'
    + posBadges
    + '</div>'
    + '<div class="dict-card-body">' + (sensesHtml || '') + '</div>'
    + '</div>';
}

let _dictSuggestions = [];

function renderSuggestions(suggestions) {
  _dictSuggestions = suggestions;
  const chips = suggestions.map((s, i) =>
    '<button class="dict-suggestion-chip" onclick="dictSearchFor(' + i + ')">'
    + escapeHtml(s.word) + '</button>'
  ).join('');
  return '<div class="dict-suggestion-box">'
    + '<span class="dict-suggestion-label">이것을 찾으셨나요?</span>'
    + chips
    + '</div>';
}

function dictSearchFor(idx) {
  const s = _dictSuggestions[idx];
  if (!s) return;
  document.getElementById('dict-input').value = s.word_plain;
  document.getElementById('dict-regex').checked = false;
  dictSearch();
}

function rebuildSpellRules() {
  setSpellLoading(true);
  setSpellStatus('규칙 재빌드 중… (잠시 기다려 주세요)');
  document.getElementById('spell-preview').innerHTML = '';
  document.getElementById('spell-errors').innerHTML  = '';

  pywebview.api.rebuild_spell_checker().then(result => {
    setSpellLoading(false);
    if (result.error) setSpellStatus('오류: ' + result.error);
    else setSpellStatus('재빌드 완료!');
  });
}

/* ════ 폴더 읽기 ════ */
function onLabelingToggle() {
  const mode = document.getElementById('folder-labeling').checked;
  document.getElementById('folder-rule').disabled = mode;
}

function setFolderBlocking(on) {
  document.getElementById('btn-folder-start').disabled = on;
  document.getElementById('folder-labeling').disabled = on;
  if (on) {
    document.getElementById('folder-rule').disabled = true;
  } else {
    document.getElementById('folder-rule').disabled =
      document.getElementById('folder-labeling').checked;
  }
}

function setFolderStatus(msg) {
  document.getElementById('folder-status').textContent = msg;
}

async function startFolderCheck() {
  const labelingMode = document.getElementById('folder-labeling').checked;
  const ruleName = labelingMode
    ? 'ML_LABELINGS'
    : document.getElementById('folder-rule').value;

  setFolderBlocking(true);
  setFolderStatus('폴더 선택…');
  document.getElementById('folder-results-area').innerHTML = '';
  document.getElementById('folder-labeling-area').style.display = 'none';

  const folderRes = await pywebview.api.pick_folder();
  if (folderRes.cancelled || folderRes.error) {
    setFolderBlocking(false);
    setFolderStatus(folderRes.error ? '오류: ' + folderRes.error : '취소됨');
    return;
  }

  let savePath = null;
  if (labelingMode) {
    setFolderStatus('TSV 저장 위치 선택…');
    const saveRes = await pywebview.api.pick_save_file();
    if (saveRes.cancelled || saveRes.error) {
      setFolderBlocking(false);
      setFolderStatus(saveRes.error ? '오류: ' + saveRes.error : '취소됨');
      return;
    }
    savePath = saveRes.path;
  }

  setFolderStatus('처리 시작…');
  const startRes = await pywebview.api.start_folder_check(
    folderRes.folder, ruleName, labelingMode, savePath
  );
  if (startRes.error) {
    setFolderBlocking(false);
    setFolderStatus('오류: ' + startRes.error);
    return;
  }
  pollFolderProgress();
}

async function pollFolderProgress() {
  const p = await pywebview.api.get_folder_progress();
  if (p.error) {
    setFolderStatus('오류: ' + p.error);
    setFolderBlocking(false);
    return;
  }
  const cur = p.current_file ? ' (' + p.current_file + ')' : '';
  const found = p.labeling_mode ? p.label_queue_count : p.results_count;
  setFolderStatus(
    `처리 중… ${p.progress}/${p.total}${cur} — 발견 ${found}건`
  );

  if (p.running) {
    setTimeout(pollFolderProgress, 250);
    return;
  }

  if (p.stage === 'labeling') {
    setFolderStatus(`라벨링 시작 (총 ${p.label_queue_count}건)`);
    document.getElementById('folder-labeling-area').style.display = 'block';
    loadNextLabel();
  } else {
    const r = await pywebview.api.get_folder_results();
    renderFolderResults(r.results);
    setFolderStatus(`완료 — ${r.results.length}건 발견`);
    setFolderBlocking(false);
  }
}

async function loadNextLabel() {
  const item = await pywebview.api.get_next_label_item();
  if (item.done) {
    document.getElementById('folder-labeling-area').style.display = 'none';
    setFolderStatus(`라벨링 완료 (${item.total}건)`);
    setFolderBlocking(false);
    return;
  }
  document.getElementById('label-idx').textContent = item.idx;
  document.getElementById('label-total').textContent = item.total;
  document.getElementById('label-rule-id').textContent = '[' + (item.rule_id || '-') + ']';
  document.getElementById('label-content').innerHTML = item.highlighted;
  
  const backBtn = document.getElementById('btn-label-back');
  if (backBtn) backBtn.disabled = (item.idx <= 1);
}

async function submitLabel(label) {
  const res = await pywebview.api.submit_label(label);
  if (res.error) {
    setFolderStatus('저장 오류: ' + res.error);
    return;
  }
  loadNextLabel();
}

async function goBackLabel() {
  const res = await pywebview.api.go_back_label();
  if (res.error) {
    setFolderStatus('뒤로 가기 오류: ' + res.error);
    return;
  }
  loadNextLabel();
}

async function abortLabeling() {
  await pywebview.api.abort_labeling();
  document.getElementById('folder-labeling-area').style.display = 'none';
  setFolderStatus('라벨링 중단됨');
  setFolderBlocking(false);
}

function renderFolderResults(results) {
  const area = document.getElementById('folder-results-area');
  if (!results.length) {
    area.innerHTML = '<div class="no-errors">오류가 없습니다.</div>';
    return;
  }
  const cols = ['#', 'File', 'Error Type', 'Original Text (Detected)', 'Msg', 'Debug'];
  const widths = ['4%', '12%', '12%', '35%', '30%', '7%'];

  const colgroup = '<colgroup>'
    + widths.map(w => '<col style="width:' + w + ';">').join('')
    + '</colgroup>';

  const th = '<tr>'
    + cols.map((c, i) =>
        '<th onclick="sortFolderTable(' + i + ')">'
        + escapeHtml(c) + '<span class="sort-arrow"></span></th>'
      ).join('')
    + '</tr>';

  const tbody = results.map((r, i) => {
    return '<tr>'
      + '<td>' + (i + 1) + '</td>'
      + '<td style="word-break:break-all;">' + escapeHtml(r.file) + '</td>'
      + '<td class="err-type" style="white-space:pre-line;">' + escapeHtml(r.error_type) + '</td>'
      + '<td style="white-space:pre-wrap; line-height:1.7;">' + r.highlighted + '</td>'
      + '<td style="white-space:pre-line; word-break:break-word;">' + escapeHtml(r.msg) + '</td>'
      + '<td data-debug-idx="' + i + '">'
      +   '<button class="debug-btn" onclick="loadDebugPath(this, ' + i + ')">보기</button>'
      + '</td>'
      + '</tr>';
  }).join('');

  area.innerHTML =
    '<table class="error-table folder-result-table" style="table-layout:fixed; width:100%;">'
    + colgroup
    + '<thead>' + th + '</thead><tbody>' + tbody + '</tbody></table>';
}

function sortFolderTable(n) {
  const table = document.querySelector('.folder-result-table');
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);

  const prevCol = table.dataset.sortCol;
  const prevDir = table.dataset.sortDir || 'asc';
  const dir = (String(prevCol) === String(n) && prevDir === 'asc') ? 'desc' : 'asc';

  rows.sort((a, b) => {
    let av = a.cells[n].innerText || a.cells[n].textContent;
    let bv = b.cells[n].innerText || b.cells[n].textContent;
    if (n === 0) {
      av = parseInt(av) || 0;
      bv = parseInt(bv) || 0;
      return dir === 'asc' ? av - bv : bv - av;
    }
    const cmp = av.localeCompare(bv);
    return dir === 'asc' ? cmp : -cmp;
  });

  const frag = document.createDocumentFragment();
  rows.forEach(r => frag.appendChild(r));
  tbody.appendChild(frag);

  table.dataset.sortCol = n;
  table.dataset.sortDir = dir;

  // 화살표 갱신
  table.querySelectorAll('th .sort-arrow').forEach((s, i) => {
    s.textContent = (i === n) ? (dir === 'asc' ? '▲' : '▼') : '';
  });
}

async function loadDebugPath(btn, idx) {
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '…';
  const r = await pywebview.api.get_debug_path(idx);
  const td = btn.parentElement;
  if (r.error) {
    td.innerHTML = '<span style="color:#ef4444; font-size:11px;">'
      + escapeHtml(r.error) + '</span>';
    return;
  }
  td.innerHTML = '<div class="debug-path-text">'
    + escapeHtml(r.debug_path || '(없음)') + '</div>';
}

/* ── 라벨링 단축키 (방향키) 설정 ── */
document.addEventListener('keydown', function(e) {
  const labelingArea = document.getElementById('folder-labeling-area');
  
  // 라벨링 탭이 켜져 있고, 다른 입력창(검색창 등)에 커서가 없을 때만 작동
  if (labelingArea.style.display === 'block' && 
      document.activeElement.tagName !== 'INPUT' && 
      document.activeElement.tagName !== 'TEXTAREA') {
      
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      submitLabel('0'); // 0: 정상 (왼쪽 방향키)
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      submitLabel('1'); // 1: 오류 (오른쪽 방향키)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      submitLabel('SKIP'); // 건너뛰기 (아래 방향키)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const backBtn = document.getElementById('btn-label-back');
      if (!backBtn.disabled) goBackLabel(); // 뒤로 가기 (위 방향키)
    }
  }
});
</script>
</body>
</html>
"""


_dict_pkl = os.path.join(_project, "dictionary", "dict.pkl")


class Api:
    def __init__(self):
        self._tkn: KoTokenizer | None = None
        self._spell: SpellChecker | None = None
        self._raw: RawStringSearcher | None = None
        self._ready = False
        self._dict_data: list | None = None
        self._dict_loaded = False
        self._bktree: BKTree | None = None
        self._word_index: dict[str, dict] = {}
        # 폴더 읽기
        self._window = None
        self._folder_state: dict | None = None
        self._folder_debug_spell: SpellChecker | None = None
        self._folder_debug_rule_name: str | None = None

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    def _ensure_ready(self) -> dict | None:
        if not self._ready:
            return {"error": "초기화 중입니다. 잠시 후 다시 시도해주세요."}
        return None

    def _reload_spell_modules(self):
        importlib.reload(_spell_meaning_cfg)
        importlib.reload(_spell_spacing_cfg)
        importlib.reload(_spell_specific_cfg)
        importlib.reload(_spell_spelling_cfg)
        importlib.reload(_spell_warning_cfg)
        importlib.reload(_spell_cfg)

    def _build_spell_checkers(self):
        """기본(SPELL_CHECK_RULES) + RawString을 self에 세팅."""
        self._reload_spell_modules()
        importlib.reload(_raw_cfg)
        self._spell = SpellChecker(True)
        self._raw = RawStringSearcher()
        self._spell.add_rule_from_list(_spell_cfg.SPELL_CHECK_RULES)
        self._raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)

    # ── 토크나이저 API ──────────────────────────────────────────

    def tokenize(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        try:
            raw = self._tkn.tokenize(text)
            if not raw:
                return {"tokens": []}
            tokens = []
            for i, token in enumerate(raw):
                spaced = i > 0 and (token.start - raw[i - 1].end > 0)
                tokens.append({
                    "i": i,
                    "form": token.form,
                    "tag": f"{Tag(token.tag).name}({token.tag})",
                    "base_form": getattr(token, "base_form", token.form),
                    "raw_form": getattr(token, "raw_form", ""),
                    "lemma": getattr(token, "lemma", ""),
                    "word_position": getattr(token, "word_position", ""),
                    "spaced": spaced,
                })
            return {"tokens": tokens}
        except Exception as e:
            return {"error": str(e)}

    def rebuild_tokenizer(self) -> dict:
        if err := self._ensure_ready():
            return err
        try:
            self._tkn = KoTokenizer.reset()
            self._tkn.tokenize("")
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    # ── 사전 검색 API ───────────────────────────────────────────

    def _load_dict(self) -> str | None:
        if self._dict_loaded:
            return None
        self._dict_loaded = True
        if not os.path.exists(_dict_pkl):
            return (f"사전 파일이 없습니다: {_dict_pkl}\n"
                    "build_dict_pickle.py를 실행해 먼저 생성해 주세요.")
        try:
            with gzip.open(_dict_pkl, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, list):
                self._dict_data = data
            else:
                self._dict_data = data['entries']
                self._bktree = data.get('bktree')
            for entry in self._dict_data:
                wp = entry['word_plain']
                if wp not in self._word_index:
                    self._word_index[wp] = entry
        except Exception as e:
            self._dict_data = None
            return f"사전 파일 로드 오류: {e}"
        return None

    def _match_score(self, query: str, word: str) -> float:
        word_norm = re.sub(r'[0-9]', '', word) or word
        if word_norm == query:
            return 1.0
        if word_norm.startswith(query):
            return 0.8 + len(query) / len(word_norm) * 0.2
        return len(query) / len(word_norm)

    def _fuzzy_suggest(self, query: str) -> list[dict]:
        if not self._bktree:
            return []
        jlen = len(h2j(query))
        threshold = 1 if jlen <= 3 else (2 if jlen <= 7 else 3)
        candidates = self._bktree.search(query, threshold)
        seen_raw: set[str] = set()
        seen_clean: set[str] = set()
        results: list[dict] = []
        for _, word in candidates:
            if word in seen_raw:
                continue
            seen_raw.add(word)
            entry = self._word_index.get(word)
            if not entry:
                continue
            clean_word = re.sub(r'[0-9^\-\s]', '', entry['word'])
            clean_plain = re.sub(r'[0-9^\-\s]', '', entry['word_plain'])
            if not clean_plain or clean_plain in seen_clean:
                continue
            seen_clean.add(clean_plain)
            results.append({**entry, 'word': clean_word, 'word_plain': clean_plain})
            if len(results) >= 5:
                break
        return results

    def dict_search(self, query: str, use_regex: bool = False) -> dict:
        if err := self._load_dict():
            return {"error": err}
        if not query or not self._dict_data:
            return {"items": []}
        if use_regex:
            try:
                pattern = re.compile(query)
                matched = [e for e in self._dict_data if pattern.search(e['word_plain'])]
            except re.error as ex:
                return {"error": f"정규식 오류: {ex}"}
            return {"items": matched[:100]}
        plain_query = re.sub(r'[-^]', '', query)
        matched = [e for e in self._dict_data if plain_query in e['word_plain']]
        if matched:
            matched.sort(key=lambda e: self._match_score(plain_query, e['word_plain']), reverse=True)
            return {"items": matched[:100]}
        suggestions = self._fuzzy_suggest(plain_query)
        return {"items": [], "suggestions": suggestions}

    # ── 맞춤법 검사 API ─────────────────────────────────────────

    def spell_check(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        if not text:
            return {"highlighted": "", "errors": []}
        try:
            errors = list(self._raw.search(text))
            errors.extend(self._spell.check(self._tkn.tokenize(text)))

            highlighted = highlight_text(text, errors)
            error_list = [
                {
                    "type": get_error_type_name(e),
                    "msg": e.error_message,
                    "start": e.start_index,
                    "end": e.end_index,
                    "rule_id": e.rule_id,
                    "debug_path": e.debug_path or "",
                }
                for e in errors
            ]
            return {"highlighted": highlighted, "errors": error_list}
        except Exception as e:
            return {"error": str(e)}

    def rebuild_spell_checker(self) -> dict:
        if err := self._ensure_ready():
            return err
        self._ready = False
        try:
            self._build_spell_checkers()
            self._ready = True
            return {"ok": True}
        except Exception as e:
            self._ready = True
            return {"error": str(e)}

    # ── 폴더 읽기 API ───────────────────────────────────────────

    def pick_folder(self) -> dict:
        if not self._window:
            return {"error": "window not ready"}
        try:
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        except Exception as e:
            return {"error": str(e)}
        if not result:
            return {"cancelled": True}
        return {"folder": result[0]}

    def pick_save_file(self) -> dict:
        tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self._window:
            return {"error": "window not ready"}
        try:
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=f"labels_{tstamp}.tsv",
                file_types=("TSV files (*.tsv)", "All files (*.*)")
            )
        except Exception as e:
            return {"error": str(e)}
        if not result:
            return {"cancelled": True}
        path = result if isinstance(result, str) else result[0]
        return {"path": path}

    def _collect_paragraphs(self, file_path) -> list[str]:
        df = read_txt_file(file_path)
        paragraphs: list[str] = []
        for row_text in df["text"]:
            row_text = str(row_text)
            row_text = row_text.replace("<br>", "\n")
            row_text = row_text.replace("\\n", "\n")
            row_text = row_text.replace("\u00A0", " ")
            row_text = TAG_REPLACE_REGEX.sub("", row_text)
            for paragraph in row_text.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    paragraphs.append(paragraph)
        return paragraphs

    def _build_folder_spell_checker(self, rule_name: str, debug: bool = False) -> SpellChecker:
      """폴더 읽기 전용: 선택된 규칙으로 reload + 새 SpellChecker 생성."""
      self._reload_spell_modules()
      rules = getattr(_spell_cfg, rule_name, None)
      if rules is None:
          raise RuntimeError(f"규칙 '{rule_name}'을 찾을 수 없습니다.")
      sc = SpellChecker(debug)
      sc.add_rule_from_list(rules)
      return sc

    def start_folder_check(self, folder: str, rule_name: str,
                           labeling_mode: bool, save_path: str | None) -> dict:
        if err := self._ensure_ready():
            return err
        if self._folder_state and self._folder_state.get("running"):
            return {"error": "이미 진행 중입니다."}
        if labeling_mode and not save_path:
            return {"error": "라벨링 모드에서는 저장 경로가 필요합니다."}

        self._folder_state = {
            "running": True,
            "aborted": False,
            "stage": "scanning",
            "progress": 0,
            "total": 0,
            "current_file": "",
            "results": [],
            "label_queue": [],
            "label_idx": 0,
            "save_path": save_path,
            "labeling_mode": labeling_mode,
            "rule_name": rule_name,
            "error": None,
            "history": [], # 뒤로 가기를 위한 히스토리
            "labeled_data": [], # 메모리에 라벨링 결과를 쌓아둘 리스트 추가
        }
        t = threading.Thread(
            target=self._run_folder_check,
            args=(folder, rule_name, labeling_mode),
            daemon=True
        )
        t.start()
        return {"ok": True}
    
    def _save_labeled_data(self) -> dict:
        """메모리에 모인 라벨링 데이터를 파일에 한 번에 덮어쓰기(w 모드)로 저장합니다."""
        state = self._folder_state
        if not state or not state.get("save_path"):
            return {"error": "저장 경로가 없습니다."}
        
        labeled_data = state.get("labeled_data", [])
        if not labeled_data:
            return {"ok": True} # 저장할 데이터가 없으면 그냥 넘어감

        try:
            with open(state["save_path"], "w", encoding="utf-8") as f:
                f.write("label\trule_id\ttext\tstart\tend\n")
                f.writelines(labeled_data)
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def _run_folder_check(self, folder: str, rule_name: str, labeling_mode: bool):
        state = self._folder_state
        self._folder_debug_spell = None
        self._folder_debug_rule_name = None
        try:
            files = get_all_file_paths(folder, "txt")
            state["total"] = len(files)
            state["stage"] = "checking"

            spell = self._build_folder_spell_checker(rule_name, debug=False)
            raw = None
            if not labeling_mode:
                importlib.reload(_raw_cfg)
                raw = RawStringSearcher()
                raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)

            seen_paragraphs = set()

            for fi, file in enumerate(files):
                if state["aborted"]:
                    break
                state["progress"] = fi
                state["current_file"] = file.stem if hasattr(file, "stem") else str(file)

                try:
                    paragraphs = self._collect_paragraphs(file)
                except Exception as e:
                    # 파일 하나 실패해도 계속 진행
                    state["error"] = f"{state['current_file']}: {e}"
                    continue
                if not paragraphs:
                    continue

                all_tokens = self._tkn.tokenize(paragraphs)

                for paragraph, tokens in zip(paragraphs, all_tokens):
                    if state["aborted"]:
                        break
                    
                    # 중복 문장 필터링
                    if paragraph in seen_paragraphs:
                        continue
                    seen_paragraphs.add(paragraph)

                    errors = list(spell.check(tokens))
                    if raw is not None:
                        errors.extend(raw.search(paragraph))

                    if not errors:
                        continue

                    if labeling_mode:
                      # 오류 1개당 1개의 라벨링 항목으로 쪼개기
                      for e in errors:
                          # UI에는 현재 타겟 에러만 하이라이트
                          highlighted = highlight_text(paragraph, [e])
                          
                          start = e.start_index
                          end = e.end_index
                          
                          state["label_queue"].append({
                              "paragraph": paragraph,
                              "highlighted": highlighted,
                              "start": start,
                              "end": end,
                              "rule_id": e.rule_id if e.rule_id else "-",
                          })
                    else:
                        highlighted = highlight_text(paragraph, errors)
                        error_types = "\n".join({get_error_type_name(e) for e in errors})
                        msg = "\n".join(e.error_message for e in errors)
                        debug_path = "\n".join((e.debug_path or "") for e in errors)
                        state["results"].append({
                            "file": state["current_file"],
                            "paragraph": paragraph,
                            "error_type": error_types,
                            "highlighted": highlighted,
                            "msg": msg,
                        })

            state["progress"] = state["total"]
            if labeling_mode and state["label_queue"] and not state["aborted"]:
                state["stage"] = "labeling"
            else:
                state["stage"] = "done"
        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "done"
        finally:
            state["running"] = False

    def get_folder_progress(self) -> dict:
        state = self._folder_state
        if not state:
            return {"running": False, "stage": "idle",
                    "progress": 0, "total": 0,
                    "current_file": "", "error": None,
                    "results_count": 0, "label_queue_count": 0,
                    "labeling_mode": False}
        return {
            "running": state["running"],
            "stage": state["stage"],
            "progress": state["progress"],
            "total": state["total"],
            "current_file": state["current_file"],
            "error": state["error"],
            "results_count": len(state["results"]),
            "label_queue_count": len(state["label_queue"]),
            "labeling_mode": state["labeling_mode"],
        }

    def get_folder_results(self) -> dict:
        state = self._folder_state
        if not state:
            return {"results": []}
        return {"results": state["results"]}

    def get_next_label_item(self) -> dict:
        state = self._folder_state
        if not state:
            return {"done": True, "idx": 0, "total": 0}
        idx = state["label_idx"]
        queue = state["label_queue"]
        total = len(queue)
        if idx >= total or state["aborted"]:
            return {"done": True, "idx": idx, "total": total}
        item = queue[idx]
        return {
            "done": False,
            "idx": idx + 1,
            "total": total,
            "highlighted": item["highlighted"],
            "rule_id": item.get("rule_id", "-"),
        }

    def submit_label(self, label: str) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        idx = state["label_idx"]
        queue = state["label_queue"]
        if idx >= len(queue):
            return {"done": True}

        if label != "SKIP":
            item = queue[idx]
            text = (item["paragraph"]
                    .replace("\t", " ")
                    .replace("\n", " ")
                    .replace("\r", " "))
            rule_id = item.get("rule_id") or "-"
            start = item["start"]
            end = item["end"]

            state["labeled_data"].append(f"{label}\t{rule_id}\t{text}\t{start}\t{end}\n")

        state["history"].append({"idx": idx, "action": label})
        state["label_idx"] = idx + 1

        if state["label_idx"] >= len(queue):
            save_res = self._save_labeled_data()
            if save_res.get("error"):
                return {"error": f"저장 실패: {save_res['error']}"}
            return {"done": True}

        return {"ok": True, "remaining": len(queue) - state["label_idx"]}

    def go_back_label(self) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        
        history = state.get("history", [])
        if not history:
            return {"error": "이전 항목이 없습니다."}
        
        last_action = history.pop()
        prev_idx = last_action["idx"]
        action = last_action["action"]
        
        if action != "SKIP" and state.get("labeled_data"):
            state["labeled_data"].pop()
        
        state["label_idx"] = prev_idx
        return {"ok": True}

    def abort_labeling(self) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}

        labeled_data = state.get("labeled_data", [])
        if labeled_data and self._window:
            do_save = self._window.create_confirmation_dialog(
                "저장 확인",
                f"지금까지 작업한 {len(labeled_data)}건의 라벨링 결과를 저장하시겠습니까?\n(기존 파일은 덮어쓰기됩니다)"
            )
            if do_save:
                save_res = self._save_labeled_data()
                if save_res.get("error"):
                    return {"error": f"저장 실패: {save_res['error']}"}

        state["aborted"] = True
        if state["stage"] == "labeling":
            state["stage"] = "done"
        return {"ok": True}
    
    def get_debug_path(self, result_idx: int) -> dict:
      if err := self._ensure_ready():
          return err
      state = self._folder_state
      if not state:
          return {"error": "상태 없음"}
      results = state["results"]
      if result_idx < 0 or result_idx >= len(results):
          return {"error": "잘못된 인덱스"}

      item = results[result_idx]
      paragraph = item.get("paragraph")
      rule_name = state.get("rule_name")
      if not paragraph or not rule_name:
          return {"error": "재검사 정보 없음"}

      # 캐시된 debug 인스턴스 사용 (rule_name 바뀌면 재빌드)
      if (self._folder_debug_spell is None
              or self._folder_debug_rule_name != rule_name):
          try:
              self._folder_debug_spell = self._build_folder_spell_checker(
                  rule_name
              )
              self._folder_debug_rule_name = rule_name
          except Exception as e:
              return {"error": f"debug 빌드 실패: {e}"}

      try:
          tokens = self._tkn.tokenize(paragraph)
          errors = list(self._folder_debug_spell.check(tokens))
          debug_path = "\n".join(
              f"[{get_error_type_name(e)}] {e.error_message} :: {e.debug_path or ''}"
              for e in errors
          )
          return {"debug_path": debug_path}
      except Exception as e:
          return {"error": str(e)}

if __name__ == "__main__":
    api = Api()

    def init_all():
        try:
            api._tkn = KoTokenizer()
            api._tkn.tokenize("")
            api._build_spell_checkers()
            api._ready = True
        except Exception as e:
            with open(os.path.join(_project, "launcher_error.log"), "w", encoding="utf-8") as f:
                import traceback
                f.write(traceback.format_exc())

    t = threading.Thread(target=init_all, daemon=True)
    t.start()

    window = webview.create_window(
        title="Korean Spell Checker Tools",
        html=HTML,
        js_api=api,
        width=860,
        height=680,
        text_select=True,
    )
    api._window = window
    webview.start()