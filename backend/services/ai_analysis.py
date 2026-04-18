"""Google Generative AI (Gemma / Gemini) analysis service with caching, toggle, and auto-degradation."""

import asyncio
import re
from datetime import datetime
from typing import Optional

from loguru import logger

from config import get_settings
from core.cache import ai_cache
from core.exceptions import AIServiceUnavailable
from prompts.analysis import SYSTEM_PROMPT, build_analysis_prompt


# Lines that look like reasoning traces (to strip from Gemma 4 output)
_BULLET_PREFIXES = ("*", "-", "#", ">", "•")
_THINKING_KEYWORDS = (
    "draft ", "question:", "target:", "language:", "constraint:",
    "stock code:", "company:", "analysis:", "reasoning:",
    "final answer:", "answer:", "output:",
)


_SCORE_PATTERN = re.compile(r"\[SCORE:\s*([+-]?\d+)\]")


def _extract_ai_score(text: str) -> Optional[int]:
    """Extract [SCORE:X] from AI response. Returns int in -100..100 or None."""
    match = _SCORE_PATTERN.search(text)
    if match:
        score = int(match.group(1))
        return max(-100, min(100, score))
    return None


def _extract_final_answer(text: str) -> tuple[str, Optional[int]]:
    """
    Strip reasoning traces (drafts, constraint bullets, etc.) that Gemma 4 often
    emits before its final answer. Returns (cleaned_text, ai_score).

    Falls back to the trimmed raw text if no clean paragraph can be found.
    """
    if not text:
        return "", None

    raw = text.strip()

    # Extract AI score before cleaning
    ai_score = _extract_ai_score(raw)

    # Remove [SCORE:X] tag from text
    cleaned_raw = _SCORE_PATTERN.sub("", raw).strip()

    # Split into paragraphs separated by blank lines
    paragraphs = [p for p in re.split(r"\n\s*\n", cleaned_raw) if p.strip()]
    if not paragraphs:
        return cleaned_raw, ai_score

    def _clean(para: str) -> str:
        out = []
        for line in para.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Strip surrounding quotes if the whole line is quoted
            unquoted = stripped.strip('"\'「」『』')
            if unquoted != stripped and unquoted:
                stripped = unquoted
            if stripped.startswith(_BULLET_PREFIXES):
                continue
            lower = stripped.lower()
            if any(lower.startswith(k) for k in _THINKING_KEYWORDS):
                continue
            out.append(stripped)
        return "\n".join(out).strip()

    # Scan paragraphs from last to first; return first non-empty clean one
    for para in reversed(paragraphs):
        cleaned = _clean(para)
        if cleaned:
            return cleaned, ai_score

    # All paragraphs were reasoning — return trimmed raw as fallback
    return cleaned_raw, ai_score


class AIAnalysisService:
    """Integrates Google Generative AI (Gemma / Gemini) for stock analysis."""

    def __init__(self):
        settings = get_settings()
        self._enabled: bool = settings.AI_ENABLED
        self._api_key: str = settings.GOOGLE_API_KEY
        self._model: str = settings.AI_MODEL
        self._reason: str = ""
        self._disabled_at: Optional[datetime] = None
        self._consecutive_failures: int = 0
        self._max_failures: int = 5
        self._recovery_minutes: int = 10
        self._genai = None  # google.generativeai module

    def _init_genai(self):
        """Lazy import google.generativeai and configure API key."""
        if self._genai is not None or not self._api_key:
            return self._genai
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._genai = genai
            logger.info(f"Google GenAI initialized with model={self._model}")
        except Exception as e:
            logger.warning(f"Failed to initialize Google GenAI: {e}")
            self._genai = None
        return self._genai

    def _get_client(self):
        """Get or create a GenerativeModel client."""
        genai = self._init_genai()
        if genai is None:
            return None
        try:
            return genai.GenerativeModel(self._model)
        except Exception as e:
            logger.warning(f"Failed to create GenerativeModel({self._model}): {e}")
            return None

    @property
    def enabled(self) -> bool:
        # Auto-recovery check
        if not self._enabled and self._disabled_at:
            elapsed = (datetime.now() - self._disabled_at).total_seconds()
            if elapsed >= self._recovery_minutes * 60:
                logger.info("AI auto-recovery: attempting to re-enable")
                self._enabled = True
                self._consecutive_failures = 0
                self._reason = ""
                self._disabled_at = None
        return self._enabled

    def enable(self):
        self._enabled = True
        self._reason = ""
        self._disabled_at = None
        self._consecutive_failures = 0

    def disable(self, reason: str = "使用者手動關閉"):
        self._enabled = False
        self._reason = reason
        self._disabled_at = datetime.now()

    def update_config(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Update AI config at runtime (called from settings API)."""
        changed = False
        if api_key is not None:
            self._api_key = api_key
            self._genai = None  # force re-init
            changed = True
        if model is not None:
            self._model = model
            changed = True
        if changed:
            self._consecutive_failures = 0
            logger.info(f"AI config updated: model={self._model}, key={'set' if self._api_key else 'empty'}")

    def get_config(self) -> dict:
        """Return current AI config (API key is masked)."""
        key = self._api_key
        if key and len(key) > 8:
            masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
        elif key:
            masked = "****"
        else:
            masked = ""
        return {
            "api_key": masked,
            "model": self._model,
            "provider": "google",
        }

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self._reason,
            "consecutive_failures": self._consecutive_failures,
            "model": self._model,
            "provider": "google",
        }

    async def analyze(
        self,
        stock_code: str,
        stock_name: str,
        current_price: float,
        change_pct: float,
        signals: list[dict],
        weighted_total_score: float,
        direction: str,
        confidence: float,
        signal_agreement: str,
        horizon_label: str = "1週",
        news: Optional[list[dict]] = None,
        fundamentals: Optional[dict] = None,
    ) -> dict:
        """
        Run AI analysis using Google Gemma / Gemini.
        Returns dict with 'available', 'reasoning', 'horizon', 'model', 'sources', etc.
        Cache key includes stock + score bucket + horizon + news hash.
        """
        if not self.enabled:
            return {
                "available": False,
                "reasoning": "",
                "message": f"AI 分析功能已關閉（{self._reason or '未設定 GOOGLE_API_KEY'}）",
                "horizon": horizon_label,
                "model": self._model,
            }

        # Cache key: stock + score bucket + horizon + #news items (news freshness proxy)
        news = news or []
        fundamentals = fundamentals or {}
        score_bucket = round(weighted_total_score / 5) * 5
        news_hash = hash(tuple(n.get("title", "") for n in news[:5]))
        cache_key = f"ai:{stock_code}:{score_bucket}:{horizon_label}:{news_hash}"
        if cache_key in ai_cache:
            cached = dict(ai_cache[cache_key])
            cached["from_cache"] = True
            return cached

        # Build prompt with technical + fundamentals + news
        prompt = build_analysis_prompt(
            stock_code=stock_code,
            stock_name=stock_name,
            current_price=current_price,
            change_pct=change_pct,
            signals=signals,
            weighted_total_score=weighted_total_score,
            direction=direction,
            confidence=confidence,
            signal_agreement=signal_agreement,
            horizon_label=horizon_label,
            news=news,
            fundamentals=fundamentals,
        )

        try:
            reasoning, ai_score = await self._call_google(prompt)
            # Ensure reasoning is a complete Chinese summary, not a fragment.
            # If too long, truncate at last sentence boundary (。) rather than
            # cutting mid-sentence.
            if len(reasoning) > 300:
                # Find last sentence-ending punctuation within limit
                for sep in ("。", "，", "、"):
                    idx = reasoning.rfind(sep, 0, 300)
                    if idx > 0:
                        reasoning = reasoning[:idx + 1]
                        break
                else:
                    reasoning = reasoning[:297] + "..."

            self._consecutive_failures = 0
            result = {
                "available": True,
                "reasoning": reasoning,
                "ai_score": ai_score,
                "from_cache": False,
                "horizon": horizon_label,
                "model": self._model,
                "sources": {
                    "signals": True,
                    "fundamentals": bool(fundamentals),
                    "news_count": len(news),
                },
            }
            ai_cache[cache_key] = result
            return result

        except Exception as e:
            self._consecutive_failures += 1
            logger.error(f"AI analysis failed ({self._consecutive_failures}/{self._max_failures}): {e}")
            if self._consecutive_failures >= self._max_failures:
                self.disable(f"連續{self._max_failures}次失敗，自動關閉")
                logger.warning("AI auto-disabled due to consecutive failures")
            return {
                "available": False,
                "reasoning": "",
                "message": f"AI 分析暫時無法使用: {str(e)[:80]}",
                "horizon": horizon_label,
                "model": self._model,
            }

    async def _call_google(self, prompt: str, max_retries: int = 2) -> tuple[str, Optional[int]]:
        """
        Call Google GenAI with the configured model.
        Gemma models don't support system instructions, so we prepend them to the prompt.
        Returns (reasoning_text, ai_score) where ai_score is -100..100 or None.
        """
        if not self._api_key:
            raise AIServiceUnavailable("GOOGLE_API_KEY 未設定")

        full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"

        client = self._get_client()
        if client is None:
            raise AIServiceUnavailable(f"無法建立模型 {self._model}")

        for attempt in range(max_retries):
            try:
                response = await self._generate_async(client, full_prompt)
                content = (response or "").strip()
                if content:
                    text, ai_score = _extract_final_answer(content)
                    if text:
                        return text, ai_score
                raise AIServiceUnavailable(f"{self._model} returned empty response")
            except Exception as e:
                err_msg = str(e).lower()
                is_last_attempt = attempt == max_retries - 1

                if any(k in err_msg for k in ["quota", "unauthorized", "permission", "api_key"]):
                    logger.warning(f"{self._model} hit quota/auth error: {e}")
                    raise

                if is_last_attempt:
                    raise

                wait = 2 ** attempt
                logger.warning(
                    f"{self._model} attempt {attempt+1} failed: {e}, retrying in {wait}s"
                )
                await asyncio.sleep(wait)

        raise AIServiceUnavailable(f"模型 {self._model} 無法呼叫")

    async def _generate_async(self, client, prompt: str) -> str:
        """Run the sync generate_content in an executor and return text."""
        loop = asyncio.get_event_loop()

        def _sync_call():
            response = client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 512,
                    "top_p": 0.9,
                },
            )
            # Gemma / Gemini responses both have .text accessor
            return getattr(response, "text", "") or ""

        return await loop.run_in_executor(None, _sync_call)
