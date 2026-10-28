"""Dynamic Model Failover Pool and Health Tracking."""
import time
import json
import urllib.request
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("failover_pool")

class FailoverPool:
    def __init__(self, models: List[str], cooldown_sec: int = 60):
        self.models = list(models)
        self.cooldown_sec = cooldown_sec
        # {model_id: {"success": 0, "fail": 0, "cooldown_until": 0.0, "last_error": None, "last_used": 0.0}}
        self.stats: Dict[str, Dict[str, Any]] = {
            m: {"success": 0, "fail": 0, "cooldown_until": 0.0, "last_error": None, "last_used": 0.0}
            for m in self.models
        }

    def get_candidates(self) -> List[str]:
        now = time.time()
        ready = [m for m in self.models if self.stats.get(m, {}).get("cooldown_until", 0) <= now]
        if ready:
            return ready
        
        # If all models are in cooldown, reset cooldown on the earliest one
        logger.warning("All models in pool are cooling down. Resetting the earliest model cooldown.")
        sorted_by_cd = sorted(self.models, key=lambda m: self.stats.get(m, {}).get("cooldown_until", 0))
        if sorted_by_cd:
            earliest = sorted_by_cd[0]
            self.stats[earliest]["cooldown_until"] = 0
            return sorted_by_cd
        return self.models

    def record_success(self, model: str):
        if model not in self.stats:
            self.stats[model] = {"success": 0, "fail": 0, "cooldown_until": 0.0, "last_error": None, "last_used": 0.0}
        self.stats[model]["success"] += 1
        self.stats[model]["last_used"] = time.time()
        self.stats[model]["last_error"] = None

    def record_failure(self, model: str, error: Exception):
        if model not in self.stats:
            self.stats[model] = {"success": 0, "fail": 0, "cooldown_until": 0.0, "last_error": None, "last_used": 0.0}
        self.stats[model]["fail"] += 1
        self.stats[model]["cooldown_until"] = time.time() + self.cooldown_sec
        self.stats[model]["last_error"] = f"{type(error).__name__}: {str(error)[:100]}"
        logger.warning(f"Model '{model}' failed ({type(error).__name__}). Cooldown {self.cooldown_sec}s.")

    def get_status_list(self) -> List[Dict[str, Any]]:
        now = time.time()
        results = []
        for m in self.models:
            st = self.stats.get(m, {})
            cd = max(0.0, round(st.get("cooldown_until", 0) - now, 1))
            results.append({
                "model": m,
                "status": "cooldown" if cd > 0 else "ready",
                "cooldown_remaining_sec": cd,
                "success_count": st.get("success", 0),
                "fail_count": st.get("fail", 0),
                "last_error": st.get("last_error")
            })
        return results
