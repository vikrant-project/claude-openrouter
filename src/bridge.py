"""High-performance FastAPI Bridge for Claude Code & OpenRouter."""
import asyncio
import json
import logging
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import litellm
from litellm.llms.anthropic.pass_through.adapters.handler import LiteLLMMessagesToCompletionTransformationHandler
from litellm.llms.anthropic.pass_through.messages.streaming_iterator import anthropic_messages_response_as_sse_events
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from .config import Config
from .failover_pool import FailoverPool
from .sanitizers import sanitize_anthropic_response

litellm.telemetry = False
litellm.suppress_debug_info = True

cfg = Config()
pool = FailoverPool(cfg.models, cooldown_sec=cfg.cooldown_seconds)

logger = logging.getLogger("claude_openrouter_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Claude OpenRouter Bridge", version="1.0.0", docs_url=None, redoc_url=None)

@app.middleware("http")
async def check_auth(request: Request, call_next):
    if request.url.path in ("/health", "/models", "/status", "/"):
        return await call_next(request)
    supplied = request.headers.get("authorization", "").removeprefix("Bearer ") or request.headers.get("x-api-key", "")
    if cfg.local_key and not secrets.compare_digest(supplied, cfg.local_key):
        return JSONResponse(
            {"type": "error", "error": {"type": "authentication_error", "message": "Invalid local proxy credential"}},
            status_code=401
        )
    return await call_next(request)

@app.get("/")
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "claude-openrouter-bridge",
        "total_models": len(pool.models),
        "available_models": len(pool.get_candidates()),
        "port": cfg.port
    }

@app.get("/models")
@app.get("/status")
async def get_status():
    return {
        "pool": pool.get_status_list(),
        "total": len(pool.models)
    }

async def execute_request(params: dict, requested_model: str) -> dict:
    candidates = pool.get_candidates()
    errors = []
    
    for candidate in candidates:
        logger.info(f"[AutoRouter] Attempting candidate: '{candidate}'")
        try:
            result = await LiteLLMMessagesToCompletionTransformationHandler.async_anthropic_messages_handler(
                model="openai/" + candidate,
                custom_llm_provider="openai",
                api_base=cfg.data.get("upstream", "https://openrouter.ai/api/v1"),
                api_key=cfg.api_key,
                stream=False,
                timeout=120,
                num_retries=0,
                **params
            )
            if hasattr(result, "model_dump"):
                result = result.model_dump()
                
            pool.record_success(candidate)
            logger.info(f"[AutoRouter] SUCCESS with model '{candidate}'")
            return sanitize_anthropic_response(result, requested_model)
            
        except Exception as exc:
            err_type = type(exc).__name__
            logger.warning(f"[AutoRouter] FAILED on '{candidate}' ({err_type}): {exc}")
            pool.record_failure(candidate, exc)
            errors.append(f"{candidate} ({err_type})")
            continue
            
    summary = ", ".join(errors)
    raise RuntimeError(f"All free models exhausted: {summary}")

@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    requested_model = body.get("model", "claude-sonnet-4-6")
    stream = body.get("stream", False)
    
    allowed = {"max_tokens", "messages", "system", "temperature", "stop_sequences", "tool_choice", "tools", "top_p", "top_k"}
    params = {k: v for k, v in body.items() if k in allowed}
    if "max_tokens" not in params:
        params["max_tokens"] = 4096

    def make_error_payload(exc):
        status = getattr(exc, "status_code", 502)
        if not isinstance(status, int) or not 400 <= status <= 599:
            status = 502
        return status, {
            "type": "error",
            "error": {
                "type": "api_error",
                "message": f"Bridge Error: {exc}"
            }
        }

    if stream:
        async def events():
            task = asyncio.create_task(execute_request(params, requested_model))
            try:
                yield b'event: ping\ndata: {"type":"ping"}\n\n'
                while not task.done():
                    done, _ = await asyncio.wait({task}, timeout=10)
                    if not done:
                        yield b'event: ping\ndata: {"type":"ping"}\n\n'
                result = await task
                for event in anthropic_messages_response_as_sse_events(result):
                    yield event
            except Exception as exc:
                _, payload = make_error_payload(exc)
                yield ("event: error\ndata: " + json.dumps(payload) + "\n\n").encode()
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    try:
        res = await execute_request(params, requested_model)
        return JSONResponse(res)
    except Exception as exc:
        status, payload = make_error_payload(exc)
        return JSONResponse(payload, status_code=status)

def run():
    uvicorn.run(app, host="127.0.0.1", port=cfg.port, access_log=False)

if __name__ == "__main__":
    run()
