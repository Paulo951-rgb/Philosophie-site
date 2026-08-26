#!/usr/bin/env bash
# Démarre le modèle local (llama-server) + l'application web (uvicorn).
# Le modèle LLM est hors dépôt : /workspace/models/*.gguf
set -u

LLAMA_BIN="${LLAMA_BIN:-/workspace/llama/llama-b10632/llama-server}"
MODEL="${MODEL:-/workspace/models/qwen2.5-3b-instruct-q4_k_m.gguf}"
LLM_PORT="${LLM_PORT:-8090}"
APP_PORT="${APP_PORT:-12000}"

if [ -x "$LLAMA_BIN" ] && [ -f "$MODEL" ]; then
  if ! curl -sf -m 2 "http://127.0.0.1:${LLM_PORT}/health" > /dev/null 2>&1; then
    echo "Démarrage du modèle local (${MODEL##*/}) sur :${LLM_PORT}..."
    nohup "$LLAMA_BIN" -m "$MODEL" --port "$LLM_PORT" -c 4096 -t 4 --jinja \
      > /tmp/llama-server.log 2>&1 &
    echo "llama-server pid $!"
  else
    echo "Modèle local déjà actif sur :${LLM_PORT}."
  fi
else
  echo "Modèle ou binaire llama-server introuvable — repli procédural actif."
fi

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
