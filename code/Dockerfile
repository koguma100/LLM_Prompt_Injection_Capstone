# Web app image (see docker-compose.yml and deploy/). Build from the code/ directory, which must contain the trained BoW models
# in models/ (see code/training/train_bow.py):
#   docker build -t capstone-web .
#   docker run -p 8000:8000 -e OLLAMA_URL=http://host.docker.internal:11434/api/generate capstone-web
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/usr/local/share/nltk_data \
    HF_HOME=/opt/huggingface

WORKDIR /app

# CPU-only PyTorch for sentence-transformers; the default build bundles CUDA and is several GB larger
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements-web.txt .
RUN pip install -r requirements-web.txt

# Download the sentence tokenizer and the embedding model at build time, so the app doesn't fetch them on startup
RUN python -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab \
 && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .
RUN pip install --no-deps .
RUN test -f models/BoWModel.pkl -a -f models/BoWModelMalicious.pkl \
    || (echo "Missing BoW models in code/models/; train them with training/train_bow.py" && exit 1)

# PORT can be changed by the host. One worker keeps a single copy of the embedding model in memory; threads serve concurrent
# requests while they wait on the LLM, and the long timeout allows for a slow CPU-only LLM server.
ENV PORT=8000
EXPOSE 8000
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 600 "webapp:create_app()"
