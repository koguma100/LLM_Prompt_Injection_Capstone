# LLM server

An [Ollama](https://ollama.com) server with `phi3:mini` built into the image, used by the sanitization pipeline in the web app. It serves Ollama's API (`/api/generate`, `/api/version`) on port 7860 and loads the model when it starts.

It runs alongside the web app in [docker-compose.yml](../docker-compose.yml) (local testing) and [deploy/docker-compose.yml](../deploy/docker-compose.yml) (the server). It has no authentication, so it should never be exposed to the internet: in the server setup, only the Caddy proxy is.
