# Ollama server with phi3:mini built in, used by the web app (see docker-compose.yml and deploy/).
FROM ollama/ollama:0.34.3

ENV OLLAMA_HOST=0.0.0.0:7860 \
    HOME=/ollama \
    OLLAMA_MODELS=/ollama/models \
    # Keep the model loaded between requests instead of unloading it after 5 idle minutes
    OLLAMA_KEEP_ALIVE=-1 \
    # Don't keep processed prompts in RAM (see the README); the pipeline never reuses a prompt
    LLAMA_ARG_CACHE_RAM=0

# Pull the model at build time so the container doesn't download 2 GB every time it starts
RUN mkdir -p /ollama \
 && (ollama serve >/dev/null 2>&1 &) \
 && until ollama list >/dev/null 2>&1; do sleep 1; done \
 && ollama pull phi3:mini \
 && chmod -R a+rwX /ollama

EXPOSE 7860

# Start the server, then load the model with a one-word prompt, so the first visitor doesn't wait for it to
# load and the server's memory use stays high enough that Oracle doesn't count it as idle (see deploy/README.md)
ENTRYPOINT ["/bin/sh", "-c", "ollama serve & until ollama list >/dev/null 2>&1; do sleep 1; done; ollama run phi3:mini hi >/dev/null; wait"]
CMD []
