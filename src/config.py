"""Configuration manager for Claude OpenRouter Bridge."""
import json
import os
import secrets
from pathlib import Path
from typing import Dict, Any, List

DEFAULT_MODELS: List[str] = [
    "openrouter/free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-lightning:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
    "dots-studio/dots-3-note-preview:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "xingchen-agi/xing4.0-29b-a4b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "recursive/flint-v1.0:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "liquid/lfm-2.5-2.6b:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free"
]

class Config:
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or (Path.home() / ".claude" / "openrouter-config.json")
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        # Check env var fallback
        default_key = os.environ.get("OPENROUTER_API_KEY", "")
        return {
            "upstream": "https://openrouter.ai/api/v1",
            "openrouter_api_key": default_key,
            "local_key": secrets.token_urlsafe(32),
            "port": 4141,
            "cooldown_seconds": 60,
            "models": DEFAULT_MODELS
        }

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        os.chmod(self.config_path, 0o600)

    @property
    def api_key(self) -> str:
        return self.data.get("openrouter_api_key", os.environ.get("OPENROUTER_API_KEY", "")).strip()

    @api_key.setter
    def api_key(self, value: str):
        self.data["openrouter_api_key"] = value.strip()
        self.save()

    @property
    def local_key(self) -> str:
        return self.data.get("local_key", "")

    @property
    def port(self) -> int:
        return int(self.data.get("port", 4141))

    @property
    def cooldown_seconds(self) -> int:
        return int(self.data.get("cooldown_seconds", 60))

    @property
    def models(self) -> List[str]:
        return self.data.get("models", DEFAULT_MODELS)
