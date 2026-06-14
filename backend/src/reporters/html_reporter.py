from html import escape
from typing import Iterable

from src.models.interface import SpellError

# AI로 구현한 코드. 블랙박스임.

# 정렬을 버블정렬로 하면 절대 안됨(브라우저 뻗음)
# 내장 sort를 써서 정렬한 다음 렌더링은 1번만 해야 대량의 텍스트도 처리 가능하니 항상 유의할 것.

def get_error_type_name(match: SpellError) -> str:
    error_type = getattr(match, "error_type", None)
    return getattr(error_type, "name", "NOT_SET")

def summarize_error_types(matches: Iterable[SpellError]) -> str:
    ordered_unique = []
    seen = set()

    for match in matches:
        type_name = get_error_type_name(match)
        if type_name not in seen:
            seen.add(type_name)
            ordered_unique.append(type_name)

    return ", ".join(ordered_unique)


def highlight_text(original_text: str, matches: list[SpellError]) -> str:
    """
    원본 텍스트와 매치 정보(list[SpellError])를 받아
    빨간 밑줄이 그어진 HTML 문자열을 반환합니다.
    각 에러에는 hover 시 표시될 tooltip 메시지와 error type이 포함됩니다.

    주의:
    - match.start_index, match.end_index 는 original_text 기준 인덱스라고 가정합니다.
    - end_index 는 포함(inclusive) 인덱스라고 가정합니다.
    - 겹치는 매치는 하나의 하이라이트로 합쳐지며, tooltip 메시지도 함께 표시됩니다.
    """
    if not matches:
        return escape(original_text)

    valid_matches = []
    for match in matches:
        start = getattr(match, "start_index", None)
        end = getattr(match, "end_index", None)

        if start is None or end is None:
            continue
        if start < 0 or end < start:
            continue
        if start >= len(original_text):
            continue

        end -= 1
        end = min(end, len(original_text) - 1)

        valid_matches.append((start, end, match))

    if not valid_matches:
        return escape(original_text)

    valid_matches.sort(key=lambda x: (x[0], x[1]))

    # 겹치는 매치를 그룹으로 합치기
    groups = []
    for start, end, match in valid_matches:
        if groups and start <= groups[-1][1]:
            group = groups[-1]
            group[1] = max(group[1], end)
            group[2].append(match)
        else:
            groups.append([start, end, [match]])

    result = []
    cursor = 0

    for start, end, group_matches in groups:
        # 에러 전 일반 텍스트
        if cursor < start:
            result.append(escape(original_text[cursor:start]))

        tooltip_msg = "\n\n".join(
            f"[{get_error_type_name(m)}] {getattr(m, 'error_message', '')}"
            for m in group_matches
        )
        escaped_tooltip = escape(tooltip_msg, quote=True)
        highlighted_text = escape(original_text[start:end + 1])

        result.append(
            f"<span class='error-highlight' data-error-msg=\"{escaped_tooltip}\">{highlighted_text}</span>"
        )

        cursor = end + 1

    # 남은 일반 텍스트
    if cursor < len(original_text):
        result.append(escape(original_text[cursor:]))

    return "".join(result)


def build_report_item(file_path: str, original_text: str, matches: list[SpellError]) -> dict:
    matches = list(matches)

    msg_lines = [
        f"[{get_error_type_name(match)}] {getattr(match, 'error_message', '')}"
        for match in matches
    ]

    return {
        "file": file_path,
        "text": highlight_text(original_text, matches),
        "msg": "\n".join(msg_lines),
        "error_types": summarize_error_types(matches),
    }


def create_html_report(data_list, output_filename="report.html"):
    """
    data_list: [
        {
            'file': str,
            'text': str(html),
            'msg': str,
            'error_types': str
        },
        ...
    ]
    output_filename: 저장할 파일 경로
    """

    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>맞춤법 검사 결과</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }

            .container {
                max-width: 1600px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: visible;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 40px;
                position: relative;
                z-index: 1;
            }

            .header h2 {
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 8px;
            }

            .header p {
                font-size: 14px;
                opacity: 0.9;
            }

            .table-container {
                overflow-x: auto;
                overflow-y: visible;
                padding: 20px;
                position: relative;
            }

            table {
                border-collapse: collapse;
                width: 100%;
                background: white;
                table-layout: fixed;
            }

            th, td {
                border: 1px solid #e5e7eb;
                padding: 16px;
                text-align: left;
                position: relative;
                text-overflow: ellipsis;
                vertical-align: top;
            }

            th {
                overflow: hidden;
                background: linear-gradient(180deg, #f9fafb 0%, #f3f4f6 100%);
                font-weight: 600;
                color: #374151;
                cursor: pointer;
                user-select: none;
                position: relative;
                transition: all 0.2s ease;
            }

            td {
                overflow: visible;
            }

            th:hover {
                background: linear-gradient(180deg, #f3f4f6 0%, #e5e7eb 100%);
            }

            th.resizing {
                background: #e5e7eb;
            }

            .resizer {
                position: absolute;
                top: 0;
                right: 0;
                width: 8px;
                height: 100%;
                cursor: col-resize;
                z-index: 10;
                background: transparent;
            }

            .resizer:hover {
                background: rgba(102, 126, 234, 0.3);
            }

            .resizer.resizing {
                background: rgba(102, 126, 234, 0.6);
            }

            .error-highlight {
                position: relative;
                text-decoration: underline;
                text-decoration-color: #ef4444;
                text-decoration-style: wavy;
                text-decoration-thickness: 1px;
                color: #dc2626;
                font-weight: 600;
                background: rgba(239, 68, 68, 0.1);
                padding: 0px 0px;
                border-radius: 3px;
                cursor: help;
            }

            .error-highlight::before {
                content: attr(data-error-msg);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                margin-bottom: 10px;

                background: white;
                color: #333;
                padding: 10px 14px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

                white-space: pre-wrap;
                word-wrap: break-word;
                min-width: 220px;
                max-width: 340px;

                font-size: 13px;
                font-weight: 400;
                line-height: 1.5;

                opacity: 0;
                visibility: hidden;
                transition: opacity 0.2s ease, visibility 0.2s ease;

                z-index: 10000;
                pointer-events: none;
            }

            .error-highlight::after {
                content: '';
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                margin-bottom: 4px;

                border: 6px solid transparent;
                border-top-color: white;
                filter: drop-shadow(0 2px 2px rgba(0, 0, 0, 0.1));

                opacity: 0;
                visibility: hidden;
                transition: opacity 0.2s ease, visibility 0.2s ease;

                z-index: 10000;
                pointer-events: none;
            }

            .error-highlight:hover::before,
            .error-highlight:hover::after {
                opacity: 1;
                visibility: visible;
            }

            tbody tr {
                position: relative;
                z-index: 10;
            }

            tbody tr:hover {
                z-index: 100;
                background: #f0f9ff !important;
            }

            .idx-cell {
                font-size: 13px;
                color: #9ca3af;
                font-weight: 500;
                text-align: center;
            }

            .filename {
                font-size: 13px;
                color: #6366f1;
                font-weight: 500;
                font-family: 'Consolas', 'Monaco', monospace;
                word-break: break-all;
                overflow-wrap: break-word;
            }

            .type-cell {
                font-size: 13px;
                color: #374151;
                font-weight: 600;
                white-space: pre-line;
                word-break: break-word;
                overflow-wrap: break-word;
            }

            .msg-cell {
                white-space: pre-line;
                color: #4b5563;
                line-height: 1.6;
                word-break: break-word;
                overflow-wrap: break-word;
            }

            .detected-cell {
                white-space: pre-wrap;
                word-break: break-word;
                overflow-wrap: break-word;
                line-height: 1.7;
            }

            tbody tr:nth-child(even) {
                background: #fafafa;
            }

            tbody tr:nth-child(odd) {
                background: white;
            }

            .table-container::-webkit-scrollbar {
                height: 10px;
            }

            .table-container::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }

            .table-container::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
            }

            .table-container::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📝 맞춤법 검사 결과</h2>
                <p>컬럼 헤더를 클릭하면 정렬되며, 경계선을 드래그하여 너비를 조절할 수 있습니다. 에러 부분에 마우스를 올리면 error type과 상세 메시지를 볼 수 있습니다.</p>
            </div>

            <div class="table-container">
                <table id="resultTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)" style="width: 7%;">
                                No.
                                <div class="resizer" data-col="0"></div>
                            </th>
                            <th onclick="sortTable(1)" style="width: 18%;">
                                File
                                <div class="resizer" data-col="1"></div>
                            </th>
                            <th onclick="sortTable(2)" style="width: 15%;">
                                Error Type
                                <div class="resizer" data-col="2"></div>
                            </th>
                            <th onclick="sortTable(3)" style="width: 30%;">
                                Original Text (Detected)
                                <div class="resizer" data-col="3"></div>
                            </th>
                            <th onclick="sortTable(4)" style="width: 20%;">
                                Msg
                                <div class="resizer" data-col="4"></div>
                            </th>
                            <th onclick="sortTable(5)" style="width: 10%;">
                                Debug Path
                                <div class="resizer" data-col="5"></div>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for idx, item in enumerate(data_list, start=1):
        file_text = escape(str(item.get("file", "")))
        error_types = escape(str(item.get("error_types", "")))
        msg_text = escape(str(item.get("msg", "")))
        detected_html = str(item.get("text", ""))
        debug_path_text = escape(str(item.get("debug_path", "")))

        html_content += f"""
                        <tr>
                            <td class="idx-cell">{idx}</td>
                            <td class="filename">{file_text}</td>
                            <td class="type-cell">{error_types}</td>
                            <td class="detected-cell">{detected_html}</td>
                            <td class="msg-cell">{msg_text}</td>
                            <td class="msg-cell">{debug_path_text}</td>
                        </tr>
        """

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            function sortTable(n) {
                const table = document.getElementById("resultTable");
                const tbody = table.tBodies[0];
                const rows = Array.from(tbody.rows);

                const currentDir = table.dataset.sortDir || 'asc';
                const currentCol = table.dataset.sortCol || -1;
                const dir = (currentCol == n && currentDir === 'asc') ? 'desc' : 'asc';

                rows.sort((rowA, rowB) => {
                    const cellA = rowA.cells[n];
                    const cellB = rowB.cells[n];

                    let aContent = cellA.innerText || cellA.textContent;
                    let bContent = cellB.innerText || cellB.textContent;

                    if (n === 0) {
                        aContent = parseInt(aContent) || 0;
                        bContent = parseInt(bContent) || 0;
                        return dir === 'asc' ? aContent - bContent : bContent - aContent;
                    }

                    const comparison = aContent.localeCompare(bContent);
                    return dir === 'asc' ? comparison : -comparison;
                });

                const fragment = document.createDocumentFragment();
                rows.forEach(row => fragment.appendChild(row));
                tbody.appendChild(fragment);

                table.dataset.sortDir = dir;
                table.dataset.sortCol = n;
            }

            (function() {
                const resizers = document.querySelectorAll('.resizer');
                let currentResizer = null;
                let currentTh = null;
                let startX = 0;
                let startWidth = 0;

                resizers.forEach(resizer => {
                    resizer.addEventListener('mousedown', function(e) {
                        e.stopPropagation();
                        currentResizer = this;
                        currentTh = this.parentElement;
                        startX = e.pageX;
                        startWidth = currentTh.offsetWidth;

                        currentResizer.classList.add('resizing');
                        currentTh.classList.add('resizing');

                        document.addEventListener('mousemove', handleMouseMove);
                        document.addEventListener('mouseup', handleMouseUp);

                        document.body.style.cursor = 'col-resize';
                        document.body.style.userSelect = 'none';
                    });
                });

                function handleMouseMove(e) {
                    if (currentResizer) {
                        const diff = e.pageX - startX;
                        const newWidth = startWidth + diff;

                        if (newWidth >= 50) {
                            currentTh.style.width = newWidth + 'px';

                            const colIndex = Array.from(currentTh.parentElement.children).indexOf(currentTh);
                            const rows = document.querySelectorAll('#resultTable tbody tr');

                            rows.forEach(row => {
                                const td = row.children[colIndex];
                                if (td) {
                                    td.style.width = newWidth + 'px';
                                }
                            });
                        }
                    }
                }

                function handleMouseUp() {
                    if (currentResizer) {
                        currentResizer.classList.remove('resizing');
                        currentTh.classList.remove('resizing');
                        currentResizer = null;
                        currentTh = null;

                        document.removeEventListener('mousemove', handleMouseMove);
                        document.removeEventListener('mouseup', handleMouseUp);

                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';
                    }
                }
            })();
        </script>
    </body>
    </html>
    """

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Info] HTML 리포트가 생성되었습니다: {output_filename}")