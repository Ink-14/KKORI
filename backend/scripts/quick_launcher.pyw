"""
규칙 테스트용 디버깅 툴입니다.
사용자용 메인 진입점은 main.py입니다!
"""

import gzip
import importlib
import json
import os
import pickle
import re
import sys
import threading
import traceback
import logging
from datetime import datetime

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# __file__ 절대경로 보장
_script = os.path.abspath(__file__)
_project = os.path.normpath(os.path.join(os.path.dirname(_script), ".."))
_repo = os.path.dirname(_project)
_venv_site = os.path.join(_repo, "venv", "Lib", "site-packages")
_assets = os.path.join(_project, "assets")
os.chdir(_project)
sys.path.insert(0, _project)
sys.path.insert(1, _assets)
sys.path.insert(2, _venv_site)

import webview

from src.tokenizations.ko_tokenizer import KoTokenizer
from src.models.interface import Tag, SpellErrorType
from src.engines.spell_checker import SpellChecker
from src.engines.raw_searcher import RawStringSearcher
import src.engines.configs.rule_meaning as _spell_meaning_cfg
import src.engines.configs.rule_spacing as _spell_spacing_cfg
import src.engines.configs.rule_specific as _spell_specific_cfg
import src.engines.configs.rule_spelling as _spell_spelling_cfg
import src.engines.configs.rule_complex as _spell_complex_cfg
import src.engines.configs.rule_warning as _spell_warning_cfg
import src.engines.configs.rule_proofread as _spell_proofread_cfg
import src.engines.configs.rule_suppress as _spell_suppress_cfg
import src.engines.configs.rule_constants as _spell_rule_constants
import src.engines.configs.rule as _spell_cfg
import src.engines.configs.raw_string_searcher_config as _raw_cfg
from src.reporters.html_reporter import highlight_text, get_error_type_name
from src.utils.file_io import get_all_file_paths
from src.utils.pandas_io import read_txt_file
from assets.bktree import BKTree
from jamo import h2j

TAG_REPLACE_REGEX = re.compile(r"\<[^>]+\>")

def _normalize_type_name(name: str) -> str:
    """평가 타입을 통일시키는 함수. 
    SPELLING_RAW -> SPELLING 처럼 _RAW 접미사 제거."""
    return name[:-4] if name.endswith("_RAW") else name

with open(os.path.join(os.path.dirname(_script), "quick_launcher.html"), encoding="utf-8") as _ui_file:
    HTML = _ui_file.read()

_dict_pkl = os.path.join(_project, "assets", "dict.pkl")

_log_path = os.path.join(_project, "folder_check_error.log")
logging.basicConfig(
    filename=_log_path,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

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
            return {"error": "초기화 중입니다. 잠시 후 다시 시도해 주세요."}
        return None

    def _reload_spell_modules(self):
        importlib.reload(_spell_rule_constants)
        importlib.reload(_spell_meaning_cfg)
        importlib.reload(_spell_spacing_cfg)
        importlib.reload(_spell_specific_cfg)
        importlib.reload(_spell_spelling_cfg)
        importlib.reload(_spell_complex_cfg)
        importlib.reload(_spell_warning_cfg)
        importlib.reload(_spell_proofread_cfg)
        importlib.reload(_spell_suppress_cfg)
        importlib.reload(_spell_cfg)

    def _build_spell_checkers(self):
        """기본(SPELL_CHECK_RULES) + TEST_SPELL_CHECK_RULES + RawString을 self에 세팅."""
        self._reload_spell_modules()
        importlib.reload(_raw_cfg)
        self._spell = SpellChecker(True)
        self._raw = RawStringSearcher()
        self._spell.add_rule_from_list(_spell_cfg.SPELL_CHECK_RULES)
        self._spell.add_rule_from_list(_spell_cfg.TEST_SPELL_CHECK_RULES)
        self._raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)
        self._raw.add_whitelist_word(_raw_cfg.RAW_WHITELISTS)

    # ── 토크나이저 API ──────────────────────────────────────────

    def tokenize(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        try:
            raw = self._tkn.tokenize(text=text)
            if not raw:
                return {"tokens": []}
            tokens = []
            for i, token in enumerate(raw):
                spaced = i > 0 and (token.start - raw[i - 1].end > 0)
                tokens.append({
                    "i": i,
                    "form": token.form,
                    "len": token.len,
                    "tag": f"{Tag(token.tag).name}({token.tag})",
                    "tag_name": Tag(token.tag).name,
                    "base_form": getattr(token, "base_form", token.form),
                    "raw_form": getattr(token, "raw_form", ""),
                    "lemma": getattr(token, "lemma", ""),
                    "oov": getattr(token, "oov", False),
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
            self._tkn.tokenize(text="")
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
            return {"items": matched[:300]}
        plain_query = re.sub(r'[-^]', '', query)
        matched = [e for e in self._dict_data if plain_query in e['word_plain']]
        if matched:
            matched.sort(key=lambda e: self._match_score(plain_query, e['word_plain']), reverse=True)
            return {"items": matched[:300]}
        suggestions = self._fuzzy_suggest(plain_query)
        return {"items": [], "suggestions": suggestions}

    # ── 오류 타입 목록 API (frozen 라벨링용) ────────────────────

    def get_error_types(self) -> dict:
        """SpellErrorType 이름을 _RAW 정규화 후 중복 제거하여 반환. (prod에서 안 나오는 NOT_SET/TEST 제외)"""
        exclude = {"NOT_SET", "TEST"}
        seen: list[str] = []
        for t in SpellErrorType:
            n = _normalize_type_name(t.name)
            if n in exclude:
                continue
            if n not in seen:
                seen.append(n)
        return {"types": seen}

    def get_tag_names(self) -> dict:
        """Tag enum 이름 전체 반환 (규칙 제작 탭 태그 드롭다운용)."""
        return {"tags": [t.name for t in Tag]}

    def get_spell_error_type_names(self) -> dict:
        """SpellErrorType 이름 전체 반환 (규칙 제작 탭 errtype 드롭다운용)."""
        return {"types": [t.name for t in SpellErrorType]}

    # ── 맞춤법 검사 API ─────────────────────────────────────────

    def spell_check(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        if not text:
            return {"highlighted": "", "errors": []}
        try:
            errors = list(self._raw.search(text))
            errors.extend(self._spell.check(self._tkn.tokenize(text=text)))

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
            result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
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
                webview.FileDialog.SAVE,
                save_filename=f"labels_{tstamp}.tsv",
                file_types=("TSV files (*.tsv)", "All files (*.*)")
            )
        except Exception as e:
            return {"error": str(e)}
        if not result:
            return {"cancelled": True}
        path = result if isinstance(result, str) else result[0]
        return {"path": path}

    def pick_frozen_save_file(self) -> dict:
        tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self._window:
            return {"error": "window not ready"}
        try:
            result = self._window.create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=f"frozen_{tstamp}.json",
                file_types=("JSON files (*.json)", "All files (*.*)")
            )
        except Exception as e:
            return {"error": str(e)}
        if not result:
            return {"cancelled": True}
        path = result if isinstance(result, str) else result[0]
        return {"path": path}

    def pick_frozen_open_file(self) -> dict:
        if not self._window:
            return {"error": "window not ready"}
        try:
            result = self._window.create_file_dialog(
                webview.FileDialog.OPEN,
                file_types=("JSON files (*.json)", "All files (*.*)")
            )
        except Exception as e:
            return {"error": str(e)}
        if not result:
            return {"cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        return {"path": path}

    def pick_html_save_file(self) -> dict:
        tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self._window:
            return {"error": "window not ready"}
        try:
            result = self._window.create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=f"folder_results_{tstamp}.html",
                file_types=("HTML files (*.html)", "All files (*.*)")
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

    def _collect_rows(self, file_path) -> list[str]:
        """frozen corpus용: txt를 row 단위로 읽어 정리 (줄바꿈으로 재분할하지 않음)."""
        df = read_txt_file(file_path)
        rows: list[str] = []
        for row_text in df["text"]:
            row_text = str(row_text)
            row_text = row_text.replace("<br>", "\n")
            row_text = row_text.replace("\\n", "\n")
            row_text = row_text.replace("\u00A0", " ")
            row_text = TAG_REPLACE_REGEX.sub("", row_text)
            row_text = row_text.strip()
            if row_text:
                rows.append(row_text)
        return rows

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
                           labeling_mode: bool, save_path: str | None,
                           use_raw: bool = False, dedup_msg: bool = False,
                           frozen_mode: bool = False) -> dict:
        if err := self._ensure_ready():
            return err
        if self._folder_state and self._folder_state.get("running"):
            return {"error": "이미 진행 중입니다."}
        if labeling_mode and not save_path:
            return {"error": "라벨링 모드에서는 저장 경로가 필요합니다."}
        if frozen_mode and not save_path:
            return {"error": "Frozen corpus 모드에서는 저장 경로가 필요합니다."}

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
            "use_raw": use_raw and not labeling_mode and not frozen_mode,
            "dedup_msg": dedup_msg and not labeling_mode and not frozen_mode,
            "rule_name": rule_name,
            "error": None,
            "history": [], # 뒤로 가기를 위한 히스토리
            "labeled_data": [], # 메모리에 라벨링 결과를 쌓아둘 리스트 추가
            # ── frozen corpus ──
            "frozen_mode": frozen_mode,
            "frozen_queue": [],
            "frozen_idx": 0,
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
        if state.get("frozen_mode"):
            self._run_frozen_scan(folder, rule_name)
            return
        self._folder_debug_spell = None
        self._folder_debug_rule_name = None
        try:
            files = get_all_file_paths(folder, "txt")
            state["total"] = len(files)
            state["stage"] = "checking"

            spell = self._build_folder_spell_checker(rule_name, debug=True)
            raw = None
            if state.get("use_raw"):
                importlib.reload(_raw_cfg)
                raw = RawStringSearcher()
                raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)
                raw.add_whitelist_word(_raw_cfg.RAW_WHITELISTS)

            dedup_msg = state.get("dedup_msg")
            seen_msgs: set[str] = set()

            for fi, file in enumerate(files):
                seen_hashes = set()

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

                # 1) 토크나이징 전에 먼저 중복 제거 (해시로 dedup)
                unique_paragraphs = []
                for paragraph in paragraphs:
                    if state["aborted"]:
                        break
                    h = hash(paragraph)
                    if h in seen_hashes:
                        continue
                    seen_hashes.add(h)
                    unique_paragraphs.append(paragraph)

                if not unique_paragraphs:
                    continue

                # 2) 고유 문단만 토크나이징
                unique_tokens = self._tkn.tokenize(text=unique_paragraphs)
                filtered_pairs = list(zip(unique_paragraphs, unique_tokens))

                # 3) 청크 단위 배치 spell check (Rust 측 병렬 처리)
                CHUNK = 1000
                filtered_tokens = [tokens for _, tokens in filtered_pairs]
                all_spell_errors = []
                for i in range(0, len(filtered_tokens), CHUNK):
                    chunk = filtered_tokens[i : i + CHUNK]
                    all_spell_errors.extend(spell.check_batch(chunk))

                # 4) 결과 조립 (순차)
                for (paragraph, tokens), spell_errors in zip(filtered_pairs, all_spell_errors):
                    if state["aborted"]:
                        break

                    errors = list(spell_errors)
                    if raw is not None:
                        errors.extend(raw.search(paragraph))

                    if not errors:
                        continue

                    if labeling_mode:
                        for e in errors:
                            highlighted = highlight_text(paragraph, [e])
                            state["label_queue"].append({
                                "paragraph": paragraph,
                                "highlighted": highlighted,
                                "start": e.start_index,
                                "end": e.end_index,
                                "rule_id": e.rule_id if e.rule_id else "-",
                            })
                    else:
                        highlighted = highlight_text(paragraph, errors)
                        error_types = "\n".join({get_error_type_name(e) for e in errors})
                        msg = "\n".join(e.error_message for e in errors)
                        if dedup_msg:
                            if msg in seen_msgs:
                                continue
                            seen_msgs.add(msg)
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
            tb = traceback.format_exc()
            logging.exception("folder check failed")
            state["error"] = f"{type(e).__name__}: {e}\n\n{tb}"
            state["stage"] = "done"
        finally:
            state["running"] = False

    def _run_frozen_scan(self, folder: str, rule_name: str):
        """frozen corpus 라벨링용 스캔: row 단위, 전역 dedup, spell+raw 실행."""
        state = self._folder_state
        try:
            files = get_all_file_paths(folder, "txt")
            state["total"] = len(files)
            state["stage"] = "checking"

            spell = self._build_folder_spell_checker(rule_name, debug=False)
            importlib.reload(_raw_cfg)
            raw = RawStringSearcher()
            raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)
            raw.add_whitelist_word(_raw_cfg.RAW_WHITELISTS)

            # 전역(파일 간 포함) dedup
            seen_hashes: set[int] = set()

            for fi, file in enumerate(files):
                if state["aborted"]:
                    break
                state["progress"] = fi
                state["current_file"] = file.stem if hasattr(file, "stem") else str(file)

                try:
                    rows = self._collect_rows(file)
                except Exception as e:
                    state["error"] = f"{state['current_file']}: {e}"
                    continue
                if not rows:
                    continue

                unique_rows: list[str] = []
                for row_text in rows:
                    if state["aborted"]:
                        break
                    h = hash(row_text)
                    if h in seen_hashes:
                        continue
                    seen_hashes.add(h)
                    unique_rows.append(row_text)

                if not unique_rows:
                    continue

                tokens_list = list(self._tkn.tokenize(text=unique_rows))
                CHUNK = 1000
                all_spell_errors = []
                for i in range(0, len(tokens_list), CHUNK):
                    chunk = tokens_list[i : i + CHUNK]
                    all_spell_errors.extend(spell.check_batch(chunk))

                for row_text, spell_errs in zip(unique_rows, all_spell_errors):
                    if state["aborted"]:
                        break
                    errs = list(spell_errs)
                    errs.extend(raw.search(row_text))

                    highlighted = highlight_text(row_text, errs)
                    engine_spans = [
                        {
                            "start": e.start_index,
                            "end": e.end_index,
                            "type": _normalize_type_name(get_error_type_name(e)),
                            "msg": e.error_message,
                        }
                        for e in errs
                    ]
                    state["frozen_queue"].append({
                        "file": state["current_file"],
                        "text": row_text,
                        "highlighted": highlighted,
                        "engine_spans": engine_spans,
                        "gt_spans": [],
                        "reviewed": False,
                        "noise": False,
                    })

            state["progress"] = state["total"]
            if state["frozen_queue"] and not state["aborted"]:
                state["stage"] = "frozen_labeling"
            else:
                state["stage"] = "done"
        except Exception as e:
            tb = traceback.format_exc()
            logging.exception("frozen scan failed")
            state["error"] = f"{type(e).__name__}: {e}\n\n{tb}"
            state["stage"] = "done"
        finally:
            state["running"] = False

    def start_frozen_resume(self, path: str, rule_name: str) -> dict:
        """저장된 frozen JSON을 열어 이어서 라벨링."""
        if err := self._ensure_ready():
            return err
        if self._folder_state and self._folder_state.get("running"):
            return {"error": "이미 진행 중입니다."}
        if not path:
            return {"error": "파일 경로가 없습니다."}
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception as e:
            return {"error": f"파일 로드 실패: {e}"}
        if not isinstance(loaded, list):
            return {"error": "JSON 형식이 올바르지 않습니다 (배열이 아님)."}

        self._folder_state = {
            "running": True,
            "aborted": False,
            "stage": "scanning",
            "progress": 0,
            "total": len(loaded),
            "current_file": "",
            "results": [],
            "label_queue": [],
            "label_idx": 0,
            "save_path": path,          # 열었던 파일에 그대로 덮어쓰기
            "labeling_mode": False,
            "use_raw": False,
            "dedup_msg": False,
            "rule_name": rule_name,
            "error": None,
            "history": [],
            "labeled_data": [],
            "frozen_mode": True,
            "frozen_queue": [],
            "frozen_idx": 0,
        }
        t = threading.Thread(
            target=self._run_frozen_resume,
            args=(loaded, rule_name),
            daemon=True,
        )
        t.start()
        return {"ok": True}

    def _run_frozen_resume(self, loaded: list, rule_name: str):
        """저장 파일을 다시 열어 엔진을 재실행(빨간 밑줄 복원)하고,
        저장돼 있던 gt_spans/reviewed/noise는 그대로 유지한 뒤 첫 미검토 row로 점프."""
        state = self._folder_state
        try:
            state["stage"] = "checking"
            spell = self._build_folder_spell_checker(rule_name, debug=False)
            importlib.reload(_raw_cfg)
            raw = RawStringSearcher()
            raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)
            raw.add_whitelist_word(_raw_cfg.RAW_WHITELISTS)

            texts: list[str] = []
            meta: list[dict] = []
            for row in loaded:
                if not isinstance(row, dict):
                    continue
                text = str(row.get("text", ""))
                if not text:
                    continue
                texts.append(text)
                meta.append({
                    "gt_spans": row.get("spans", []) or [],
                    "reviewed": bool(row.get("reviewed")),
                    "noise": bool(row.get("noise")),
                })

            state["total"] = len(texts)
            tokens_list = list(self._tkn.tokenize(text=texts)) if texts else []

            CHUNK = 1000
            all_spell_errors = []
            for i in range(0, len(tokens_list), CHUNK):
                if state["aborted"]:
                    break
                chunk = tokens_list[i : i + CHUNK]
                all_spell_errors.extend(spell.check_batch(chunk))
                state["progress"] = min(i + CHUNK, len(tokens_list))

            for text, errs_raw, m in zip(texts, all_spell_errors, meta):
                if state["aborted"]:
                    break
                errs = list(errs_raw)
                errs.extend(raw.search(text))
                highlighted = highlight_text(text, errs)
                engine_spans = [
                    {
                        "start": e.start_index,
                        "end": e.end_index,
                        "type": _normalize_type_name(get_error_type_name(e)),
                        "msg": e.error_message,
                    }
                    for e in errs
                ]
                gt_spans = [
                    {
                        "start": int(s["start"]),
                        "end": int(s["end"]),
                        "type": s["type"],
                        "unavoidable": bool(s.get("unavoidable")),
                    }
                    for s in m["gt_spans"]
                    if s.get("type")
                ]
                state["frozen_queue"].append({
                    "file": "(resumed)",
                    "text": text,
                    "highlighted": highlighted,
                    "engine_spans": engine_spans,
                    "gt_spans": gt_spans,
                    "reviewed": m["reviewed"],
                    "noise": m["noise"],
                })

            # 첫 미검토 row로 점프 (전부 검토됐으면 0)
            first_unreviewed = next(
                (i for i, it in enumerate(state["frozen_queue"]) if not it["reviewed"]),
                0,
            )
            state["frozen_idx"] = first_unreviewed
            state["progress"] = state["total"]
            if state["frozen_queue"] and not state["aborted"]:
                state["stage"] = "frozen_labeling"
            else:
                state["stage"] = "done"
        except Exception as e:
            tb = traceback.format_exc()
            logging.exception("frozen resume failed")
            state["error"] = f"{type(e).__name__}: {e}\n\n{tb}"
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
                    "labeling_mode": False,
                    "frozen_mode": False, "frozen_queue_count": 0}
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
            "frozen_mode": state.get("frozen_mode", False),
            "frozen_queue_count": len(state.get("frozen_queue", [])),
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

    # ── Frozen corpus 라벨링 API ────────────────────────────────

    def get_next_frozen_item(self) -> dict:
        state = self._folder_state
        if not state:
            return {"done": True, "idx": 0, "total": 0}
        idx = state["frozen_idx"]
        queue = state["frozen_queue"]
        total = len(queue)
        if idx >= total or state["aborted"]:
            return {"done": True, "idx": idx, "total": total}
        item = queue[idx]
        return {
            "done": False,
            "idx": idx + 1,
            "total": total,
            "file": item["file"],
            "text": item["text"],
            "highlighted": item["highlighted"],
            "engine_spans": item["engine_spans"],
            "gt_spans": item["gt_spans"],
            "noise": item.get("noise", False),
        }

    def _frozen_save_current(self, spans) -> None:
        state = self._folder_state
        idx = state["frozen_idx"]
        queue = state["frozen_queue"]
        if 0 <= idx < len(queue):
            clean = []
            for s in spans or []:
                clean.append({
                    "start": int(s["start"]),
                    "end": int(s["end"]),
                    "type": s["type"],
                    "unavoidable": bool(s.get("unavoidable")),
                })
            queue[idx]["gt_spans"] = clean
            queue[idx]["reviewed"] = True

    def frozen_next(self, spans) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        self._frozen_save_current(spans)
        state["frozen_idx"] += 1
        if state["frozen_idx"] >= len(state["frozen_queue"]):
            save_res = self._save_frozen_data(final=True)
            if save_res.get("error"):
                return {"error": f"저장 실패: {save_res['error']}"}
            return {"done": True}
        return {"ok": True}

    def frozen_back(self, spans) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        self._frozen_save_current(spans)
        if state["frozen_idx"] <= 0:
            return {"error": "이전 항목이 없습니다."}
        state["frozen_idx"] -= 1
        return {"ok": True}

    def frozen_toggle_noise(self, spans) -> dict:
        """현재 row의 noise 여부를 토글한다.
        noise를 켤 때(표시)만 D처럼 다음으로 넘어가고, 끌 때(해제)는 현재 row에 남는다.
        noise는 메모리에만 표시되고, 최종 저장(final=True) 때만 JSON에서 제거된다."""
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        idx = state["frozen_idx"]
        queue = state["frozen_queue"]
        if not (0 <= idx < len(queue)):
            return {"error": "잘못된 인덱스"}
        # 현재 구간 저장(+reviewed=True) 후 noise 토글
        self._frozen_save_current(spans)
        turned_on = not queue[idx].get("noise", False)
        queue[idx]["noise"] = turned_on
        if not turned_on:
            # noise 해제 시에는 현재 row에 그대로 남는다.
            return {"ok": True, "moved": False, "noise": False}
        # noise를 켤 때만 D와 동일하게 다음으로 이동
        state["frozen_idx"] += 1
        if state["frozen_idx"] >= len(state["frozen_queue"]):
            save_res = self._save_frozen_data(final=True)
            if save_res.get("error"):
                return {"error": f"저장 실패: {save_res['error']}"}
            return {"done": True, "moved": True}
        return {"ok": True, "moved": True}

    def frozen_skip_to_unreviewed(self, spans) -> dict:
        """현재 row를 저장한 뒤, reviewed=False인 다음 row로 건너뛴다.
        (사용자가 JSON에서 직접 reviewed를 false로 바꿔 재검토할 때 사용)"""
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}
        self._frozen_save_current(spans)
        queue = state["frozen_queue"]
        cur = state["frozen_idx"]
        nxt = next(
            (i for i in range(cur + 1, len(queue)) if not queue[i].get("reviewed")),
            None,
        )
        if nxt is None:
            nxt = next(
                (i for i in range(0, len(queue)) if not queue[i].get("reviewed")),
                None,
            )
        if nxt is None:
            return {"error": "reviewed=false인 row가 없습니다."}
        state["frozen_idx"] = nxt
        return {"ok": True}

    def _save_frozen_data(self, final: bool = False) -> dict:
        """모든 row를 pretty JSON 배열로 저장.
        - final=False (중단/진행 저장): noise row도 유지하되 "noise": true 플래그를 남긴다.
          → 나중에 '이어서 라벨링'으로 복원 후 다시 토글 가능.
        - final=True  (마지막 row까지 완료): noise row는 JSON에서 완전히 제거한다.
        각 row: {"text", "spans":[{"start","end","type",(선택)"unavoidable"}], "reviewed", (선택)"noise"}
        unavoidable=true인 span은 사전 미등재 고유명사 등으로 엔진이 구조적으로 검출할 수 없는
        미검출(FN)을 의미하며, 평가 시 일반 미탐과 분리 집계된다."""
        state = self._folder_state
        if not state or not state.get("save_path"):
            return {"error": "저장 경로가 없습니다."}
        try:
            data = []
            for item in state["frozen_queue"]:
                is_noise = bool(item.get("noise"))
                if final and is_noise:
                    continue  # 최종 저장 시 noise row 삭제
                spans = []
                for s in item.get("gt_spans", []):
                    span = {"start": int(s["start"]), "end": int(s["end"]), "type": s["type"]}
                    if s.get("unavoidable"):
                        span["unavoidable"] = True
                    spans.append(span)
                row = {
                    "text": item["text"],
                    "spans": spans,
                    "reviewed": bool(item.get("reviewed")),
                }
                if is_noise:
                    row["noise"] = True   # 진행 저장 시에만 플래그로 보존
                data.append(row)
            with open(state["save_path"], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def abort_labeling(self) -> dict:
        state = self._folder_state
        if not state:
            return {"error": "상태 없음"}

        # ── frozen corpus 모드 ──
        if state.get("frozen_mode"):
            queue = state.get("frozen_queue", [])
            reviewed_cnt = sum(1 for it in queue if it.get("reviewed"))
            if queue and self._window:
                do_save = self._window.create_confirmation_dialog(
                    "저장 확인",
                    f"진행 상황을 저장하시겠습니까?\n"
                    f"검토 완료 {reviewed_cnt} / 전체 {len(queue)} row\n"
                    "(모든 row가 저장되어 나중에 '이어서 라벨링'으로 이어할 수 있습니다.)"
                )
                if do_save:
                    save_res = self._save_frozen_data()
                    if save_res.get("error"):
                        return {"error": f"저장 실패: {save_res['error']}"}
            state["aborted"] = True
            if state["stage"] == "frozen_labeling":
                state["stage"] = "done"
            return {"ok": True}

        # ── 기존 ML 라벨링 모드 ──
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
                  rule_name, debug=True
              )
              self._folder_debug_rule_name = rule_name
          except Exception as e:
              return {"error": f"debug 빌드 실패: {e}"}

      try:
          tokens = self._tkn.tokenize(text=paragraph)
          errors = list(self._folder_debug_spell.check(tokens))
          debug_path = "\n".join(
              f"[{get_error_type_name(e)}] {e.error_message} :: {e.debug_path or ''}"
              for e in errors
          )
          return {"debug_path": debug_path}
      except Exception as e:
          return {"error": str(e)}

    def save_folder_html(self, save_path: str) -> dict:
        if err := self._ensure_ready():
            return err
        state = self._folder_state
        if not state or not state.get("results"):
            return {"error": "저장할 결과가 없습니다."}

        results = state["results"]
        rule_name = state.get("rule_name")

        # debug spell checker 준비
        if rule_name:
            try:
                if (self._folder_debug_spell is None
                        or self._folder_debug_rule_name != rule_name):
                    self._folder_debug_spell = self._build_folder_spell_checker(
                        rule_name, debug=True
                    )
                    self._folder_debug_rule_name = rule_name
            except Exception as e:
                return {"error": f"debug 빌드 실패: {e}"}

        # 모든 row에 대해 debug_path 계산
        debug_paths: list[str] = []
        for item in results:
            paragraph = item.get("paragraph")
            if not paragraph or not self._folder_debug_spell:
                debug_paths.append("")
                continue
            try:
                tokens = self._tkn.tokenize(text=paragraph)
                errors = list(self._folder_debug_spell.check(tokens))
                debug_paths.append("\n".join(
                    f"[{get_error_type_name(e)}] {e.error_message} :: {e.debug_path or ''}"
                    for e in errors
                ))
            except Exception as e:
                debug_paths.append(f"(debug 실패: {e})")

        try:
            html_str = self._build_results_html(results, debug_paths)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(html_str)
            return {"ok": True, "path": save_path}
        except Exception as e:
            return {"error": str(e)}

    def _build_results_html(self, results: list, debug_paths: list[str]) -> str:
      import html as _html

      rows_html = []
      for i, (r, dbg) in enumerate(zip(results, debug_paths)):
          row = (
              "<tr>"
              f"<td>{i+1}</td>"
              f"<td class='file'>{_html.escape(r['file'])}</td>"
              f"<td class='err-type'>{_html.escape(r['error_type'])}</td>"
              f"<td class='highlighted-cell'>{r['highlighted']}</td>"
              f"<td>{_html.escape(r['msg'])}</td>"
              f"<td><div class='debug-content'>"
              f"{_html.escape(dbg) if dbg else '(없음)'}"
              f"</div></td>"
              "</tr>"
          )
          rows_html.append(row)

      body_rows = "\n".join(rows_html)
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      headers = ["#", "File", "Error Type", "Original Text (Detected)", "Msg", "Debug"]
      th_html = "".join(
          f'<th onclick="sortTable({i})">{_html.escape(h)}'
          f'<span class="sort-arrow"></span></th>'
          for i, h in enumerate(headers)
      )

      return f"""<!DOCTYPE html>
  <html lang="ko">
  <head>
  <meta charset="UTF-8">
  <title>폴더 검사 결과 - {timestamp}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Malgun Gothic', system-ui, -apple-system, sans-serif;
      font-size: 13px; background: #f1f5f9; color: #0f172a;
      margin: 0; padding: 20px;
    }}
    h1 {{ font-size: 18px; margin: 0 0 6px; }}
    .meta {{ color: #64748b; font-size: 12px; margin-bottom: 16px; }}
    table {{
      width: 100%; border-collapse: collapse;
      background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.07);
      table-layout: fixed; border-radius: 8px; overflow: hidden;
    }}
    th {{
      background: #ef4444; color: #fff;
      padding: 9px 12px; text-align: left;
      font-size: 12px; font-weight: 500; letter-spacing: 0.03em;
      cursor: pointer; user-select: none;
      transition: background 0.15s;
    }}
    th:hover {{ background: #dc2626; }}
    th .sort-arrow {{
      display: inline-block; margin-left: 4px;
      opacity: 0.85; font-size: 10px;
    }}
    td {{
      padding: 8px 12px; border-bottom: 1px solid #e2e8f0;
      font-size: 12px; vertical-align: top;
      word-break: break-word; white-space: pre-wrap; line-height: 1.6;
    }}
    tr:last-child td {{ border-bottom: none; }}
    .err-type {{ font-weight: 600; color: #ef4444; white-space: pre-line; }}
    .file {{ word-break: break-all; }}
    .highlighted-cell {{ line-height: 1.7; }}
    .error-highlight {{
      text-decoration: underline;
      text-decoration-color: #ef4444;
      text-decoration-style: wavy;
      text-decoration-thickness: 1.5px;
      color: #dc2626; font-weight: 600;
      background: rgba(239,68,68,0.09);
      border-radius: 3px; padding: 0 1px;
    }}
    .debug-content {{
      font-family: 'Consolas', monospace;
      font-size: 11px; color: #64748b;
      line-height: 1.5; max-height: 300px;
      overflow-y: auto; white-space: pre-wrap;
    }}
    col.c0 {{ width: 4%; }}
    col.c1 {{ width: 10%; }}
    col.c2 {{ width: 10%; }}
    col.c3 {{ width: 28%; }}
    col.c4 {{ width: 22%; }}
    col.c5 {{ width: 26%; }}
  </style>
  </head>
  <body>
  <h1>폴더 검사 결과</h1>
  <div class="meta">생성 시각: {timestamp} · 전체 {len(results)}건</div>
  <table id="results-table">
  <colgroup>
    <col class="c0"><col class="c1"><col class="c2">
    <col class="c3"><col class="c4"><col class="c5">
  </colgroup>
  <thead>
  <tr>{th_html}</tr>
  </thead>
  <tbody>
  {body_rows}
  </tbody>
  </table>

  <script>
  (function() {{
    var table = document.getElementById('results-table');
    var arrows = table.querySelectorAll('th .sort-arrow');

    window.sortTable = function(n) {{
      var tbody = table.tBodies[0];
      var rows = Array.prototype.slice.call(tbody.rows);

      var prevCol = table.getAttribute('data-sort-col');
      var prevDir = table.getAttribute('data-sort-dir') || 'asc';
      var dir = (String(prevCol) === String(n) && prevDir === 'asc') ? 'desc' : 'asc';

      // 정렬 키를 한 번만 추출해서 캐싱 (textContent 반복 호출 방지)
      var isNumeric = (n === 0);
      var keyed = new Array(rows.length);
      for (var i = 0; i < rows.length; i++) {{
        var raw = rows[i].cells[n].textContent;
        keyed[i] = {{
          row: rows[i],
          key: isNumeric ? (parseInt(raw, 10) || 0) : raw
        }};
      }}

      // 내장 sort (Timsort 계열) — 절대 버블정렬 쓰지 말 것
      if (isNumeric) {{
        keyed.sort(function(a, b) {{
          return dir === 'asc' ? a.key - b.key : b.key - a.key;
        }});
      }} else {{
        var collator = new Intl.Collator('ko', {{ numeric: true, sensitivity: 'base' }});
        keyed.sort(function(a, b) {{
          var cmp = collator.compare(a.key, b.key);
          return dir === 'asc' ? cmp : -cmp;
        }});
      }}

      // DocumentFragment로 한 번에 DOM 삽입 (렌더링 1회)
      var frag = document.createDocumentFragment();
      for (var j = 0; j < keyed.length; j++) {{
        frag.appendChild(keyed[j].row);
      }}
      tbody.appendChild(frag);

      table.setAttribute('data-sort-col', n);
      table.setAttribute('data-sort-dir', dir);

      for (var k = 0; k < arrows.length; k++) {{
        arrows[k].textContent = (k === n) ? (dir === 'asc' ? '▲' : '▼') : '';
      }}
    }};
  }})();
  </script>
  </body>
  </html>
  """


if __name__ == "__main__":
    api = Api()

    def init_all():
        try:
            api._tkn = KoTokenizer()
            api._tkn.tokenize(text="")
            api._build_spell_checkers()
            api._ready = True
        except Exception as e:
            with open(os.path.join(_project, "launcher_error.log"), "w", encoding="utf-8") as f:
                import traceback
                f.write(traceback.format_exc())

    t = threading.Thread(target=init_all, daemon=True)
    t.start()

    window = webview.create_window(
        title="KKORI Debug Tool",
        html=HTML,
        js_api=api,
        width=1180,
        height=800,
        min_size=(760, 560),
        text_select=True,
    )
    api._window = window
    webview.start()