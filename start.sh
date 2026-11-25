#!/usr/bin/env bash
# Démarre l'application web. Le cloud LLM Faucet est utilisé par défaut.
# Aucun binaire ni modèle local n'est nécessaire en mode cloud.
set -euo pipefail

APP_PORT="${APP_PORT:-12000}"

if [ "${AI_PROVIDER:-cloud}" = "local" ]; then
  LLAMA_BIN="${LLAMA_BIN:-/workspace/llama/llama-b10632/llama-server}"
  MODEL="${MODEL:-/workspace/models/qwen2.5-3b-instruct-q4_k_m.gguf}"
  LLM_PORT="${LLM_PORT:-8090}"

  if [ ! -x "$LLAMA_BIN" ] || [ ! -f "$MODEL" ]; then
    echo "AI_PROVIDER=local mais llama-server ou le modèle GGUF est introuvable." >&2
    exit 1
  fi

  if ! curl -sf -m 2 "http://127.0.0.1:${LLM_PORT}/health" > /dev/null 2>&1; then
    echo "Démarrage du modèle local (${MODEL##*/}) sur :${LLM_PORT}..."
    nohup "$LLAMA_BIN" -m "$MODEL" --port "$LLM_PORT" -c 4096 -t 4 --jinja \
      > /tmp/llama-server.log 2>&1 &
  fi
fi

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
