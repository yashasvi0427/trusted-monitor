"""One function, chat(), that sends a single-turn prompt to whichever backend
config.py selects and returns the same record shape for both:

    {"text", "stop_reason", "refused", "refusal_category", "usage", "raw"}

stop_reason uses Claude's names ("end_turn", "max_tokens", "refusal") so the
rest of the pipeline doesn't care which backend produced it.
"""

import json
import urllib.request

import config


class ModelError(Exception):
    """One call failed in a way worth skipping and retrying later (not caching)."""


class ModelTimeout(ModelError):
    """One call took longer than config.TIMEOUT_S (on 8 GB, usually swapping)."""


def chat(model: str, prompt: str, seed: int = config.SEED,
         max_tokens: int = config.MAX_TOKENS, temperature: float = config.TEMPERATURE) -> dict:
    if config.BACKEND == "ollama":
        return _chat_ollama(model, prompt, seed, max_tokens, temperature)
    if config.BACKEND == "claude":
        return _chat_claude(model, prompt)
    raise ValueError(f"unknown backend {config.BACKEND!r}")


def _chat_ollama(model: str, prompt: str, seed: int, max_tokens: int, temperature: float) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "keep_alive": config.KEEP_ALIVE,
        "options": {
            "num_ctx": config.NUM_CTX,
            "temperature": temperature,
            "seed": seed,
            "num_predict": max_tokens,
        },
    }
    req = urllib.request.Request(
        config.OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=config.TIMEOUT_S) as resp:
            raw = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SystemExit(f"Model {model!r} isn't downloaded. Run: ollama pull {model}")
        if e.code >= 500:
            raise ModelError(f"Ollama server error {e.code}")
        raise
    except TimeoutError:
        raise ModelTimeout(f"{model} took over {config.TIMEOUT_S}s")
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise ModelTimeout(f"{model} took over {config.TIMEOUT_S}s")
        raise SystemExit("Can't reach Ollama at localhost:11434. Start it with: ollama serve")

    stop_reason = {"stop": "end_turn", "length": "max_tokens"}.get(
        raw.get("done_reason"), raw.get("done_reason")
    )
    return {
        "text": raw["message"]["content"],
        "stop_reason": stop_reason,
        # Local models have no refusal signal: they refuse in plain text, if at
        # all. TODO (Day 3): when attack mode exists, flag replies that contain
        # no code / no exploit input and read a sample by hand.
        "refused": False,
        "refusal_category": None,
        "usage": {
            "input_tokens": raw.get("prompt_eval_count"),
            "output_tokens": raw.get("eval_count"),
            "seconds": raw.get("total_duration", 0) / 1e9,
        },
        "raw": raw,
    }


def _chat_claude(model: str, prompt: str) -> dict:
    import anthropic  # only needed for this backend

    # Deliberately NO server-side refusal fallback (the `fallbacks` parameter).
    # With fallbacks on, a refused request gets silently re-run on another
    # model, so we'd be measuring a different model than the one we named.
    # Here a refusal is a result: how often U declines (especially in attack
    # mode) is part of what we report.
    response = anthropic.Anthropic().messages.create(
        model=model,
        max_tokens=16000,
        output_config={"effort": "medium"},  # MBPP is easy; Sonnet 5.5 defaults to "high"
        messages=[{"role": "user", "content": prompt}],
    )
    # Always check stop_reason before trusting the content.
    refused = response.stop_reason == "refusal"
    return {
        "text": "".join(b.text for b in response.content if b.type == "text"),
        "stop_reason": response.stop_reason,
        "refused": refused,
        "refusal_category": response.stop_details.category
        if refused and response.stop_details else None,
        "usage": response.usage.model_dump(),
        "raw": response.model_dump(mode="json"),
    }
