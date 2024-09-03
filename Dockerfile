FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libreoffice  \
    vim \
    ffmpeg \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN adduser --disabled-password worker
USER worker
WORKDIR /home/worker

COPY --chown=worker:worker app.py .
COPY --chown=worker:worker requirements.txt .
COPY --chown=worker:worker backend.py .
COPY --chown=worker:worker .streamlit /home/worker/.streamlit
RUN pip3 install --user -r requirements.txt

ENV PATH="/home/worker/.local/bin:${PATH}"

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
