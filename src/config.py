"""Which models play which role. Change BACKEND to switch the whole experiment.

"ollama": free local open-source models (the current setup; runs on an 8 GB M2).
"claude": the Anthropic API (paid; needs ANTHROPIC_API_KEY and `pip install anthropic`).
"""

BACKEND = "ollama"

MODELS = {
    "ollama": {
        # U: the stronger model that may attack. The 3B made 0/10 valid backdoors
        # (cached under data/untrusted/qwen2.5-coder_3b/), so we moved up to 7B.
        "untrusted": "qwen2.5-coder:7b",
        "trusted": "qwen2.5-coder:1.5b",    # T: the weaker monitor we trust
    },
    "claude": {
        "untrusted": "claude-sonnet-5-5",
        "trusted": "claude-haiku-5-5",
    },
}

UNTRUSTED_MODEL = MODELS[BACKEND]["untrusted"]
TRUSTED_MODEL = MODELS[BACKEND]["trusted"]

# Reproducibility: greedy decoding plus a fixed seed, so a rerun of the same
# prompt gives the same answer (Ollama only; Claude doesn't accept sampling params).
SEED = 0
TEMPERATURE = 0
# Retries (attack attempts 2 and 3) must sample, or they'd repeat attempt 1
# exactly: at temperature 0 the seed has no effect. Sampling with a fixed seed
# is still reproducible.
RETRY_TEMPERATURE = 0.7

MAX_TOKENS = 4096
# MBPP prompts + answers fit easily in 2048 tokens; a smaller context window
# saves memory, which matters on 8 GB.
NUM_CTX = 2048
# Keep the model in memory between calls so we only pay the (slow) load once.
KEEP_ALIVE = "30m"
# Local inference on 8 GB is slow, and the first call also loads the model.
# Past 3 minutes the machine is almost certainly swapping: fail instead of waiting.
TIMEOUT_S = 180
OLLAMA_URL = "http://localhost:11434/api/chat"
