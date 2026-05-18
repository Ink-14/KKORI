import socket
import threading
import time
from pathlib import Path

import uvicorn
import webview

from src.api import app


def _find_free_port(start: int = 8765) -> int:
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise TimeoutError(f"서버가 {timeout}초 내에 시작되지 않았습니다 (port={port})")


def _run_server(port: int) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    dist_dir = Path(__file__).parent.parent / "frontend" / "dist"
    if not (dist_dir / "index.html").exists():
        raise FileNotFoundError(
            f"프론트엔드 빌드 결과물이 없습니다: {dist_dir / 'index.html'}\n"
            "frontend 디렉토리에서 'npm run build:desktop'을 먼저 실행하세요."
        )

    port = _find_free_port()

    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()
    _wait_for_server(port)

    window = webview.create_window(
        title="한국어 맞춤법 검사기",
        url=f"http://127.0.0.1:{port}/",
        width=1000,
        height=700,
        min_size=(600, 400),
        text_select=True,
    )
    webview.start()
