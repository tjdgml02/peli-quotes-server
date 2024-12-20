FROM python:3.9-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

COPY app/requirements.txt ./

RUN python -m venv venv
RUN . /app/venv/bin/activate && pip install --no-cache-dir -r requirements.txt
RUN git clone --depth=1 https://github.com/haven-jeon/PyKoSpacing.git && \
    cd PyKoSpacing && \
    . /app/venv/bin/activate && pip install . && \
    cd .. && rm -rf PyKoSpacing

FROM python:3.9-slim

ENV PATH="/app/venv/bin:$PATH"
ENV CUDA_VISIBLE_DEVICES="-1"

WORKDIR /app

COPY . .
COPY --from=builder /app/venv /app/venv

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]