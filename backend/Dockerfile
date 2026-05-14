FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /build

COPY requirements.prod.txt .
RUN pip install --no-cache-dir maturin

COPY rust/ rust/
COPY pyproject.toml .
RUN maturin build --release --manifest-path rust/Cargo.toml --out /wheels

RUN pip install --no-cache-dir -r requirements.prod.txt --target /deps
RUN pip install --no-cache-dir /wheels/*.whl --target /deps


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /deps /deps
ENV PYTHONPATH="/deps:/app"

COPY src/ src/
COPY assets/ assets/

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
