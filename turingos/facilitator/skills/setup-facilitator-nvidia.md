# Setup Facilitator (NVIDIA Diffusion Gemma)

1. Set env (or `nvidia_env.sh`, gitignored):
   - `TURINGOS_FACILITATOR_BASE_URL=https://integrate.api.nvidia.com/v1`
   - `TURINGOS_FACILITATOR_API_KEY=nvapi-...`
   - `TURINGOS_FACILITATOR_MODEL=google/diffusiongemma-26b-a4b-it`
2. Facilitator handles MCQ dialogue only; does not run workers.
3. Verify: restart `turing`, TopBar Model shows diffusiongemma.