#!/usr/bin/env bash
# Facilitator (fast MCQ) — copy to facilitator_env.sh (gitignored)
export TURINGOS_FACILITATOR_BASE_URL="https://integrate.api.nvidia.com/v1"
export TURINGOS_FACILITATOR_API_KEY="nvapi-YOUR_KEY_HERE"
export TURINGOS_FACILITATOR_MODEL="google/diffusiongemma-26b-a4b-it"
export TURINGOS_FACILITATOR_TEMPERATURE="1.0"
export TURINGOS_FACILITATOR_TOP_P="0.95"
export TURINGOS_FACILITATOR_MAX_TOKENS="4096"
export TURINGOS_FACILITATOR_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":true}}'