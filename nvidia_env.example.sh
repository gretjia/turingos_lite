#!/usr/bin/env bash
# Copy to nvidia_env.sh (gitignored), fill your nvapi key, then: source nvidia_env.sh
export TURINGOS_META_BASE_URL="https://integrate.api.nvidia.com/v1"
export TURINGOS_META_API_KEY="nvapi-YOUR_KEY_HERE"
export TURINGOS_META_MODEL="nvidia/nemotron-3-ultra-550b-a55b"
export TURINGOS_META_TEMPERATURE="1"
export TURINGOS_META_TOP_P="0.95"
export TURINGOS_META_MAX_TOKENS="4096"
export TURINGOS_META_STREAM="true"
export TURINGOS_META_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":true},"reasoning_budget":4096}'