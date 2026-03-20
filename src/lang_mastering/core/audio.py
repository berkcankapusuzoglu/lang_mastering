"""Audio management: TTS generation with edge-tts and pyttsx3 fallback."""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Optional


# Voice mappings
VOICES = {
    "es": "es-ES-AlvaroNeural",
    "es_female": "es-MX-DaliaNeural",
    "tr": "tr-TR-AhmetNeural",
    "tr_female": "tr-TR-EmelNeural",
}

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "audio_cache"


class AudioManager:
    """Manages TTS audio generation and caching."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._pyttsx3_engine = None

    def _get_cache_path(self, text: str, language: str) -> Path:
        """Generate a cache file path based on content hash."""
        key = f"{language}:{text}"
        hash_val = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_val}.mp3"

    async def generate_audio(self, text: str, language: str) -> Optional[str]:
        """Generate TTS audio file. Returns path to audio file or None."""
        cache_path = self._get_cache_path(text, language)

        # Return cached file if exists
        if cache_path.exists():
            return str(cache_path)

        # Try edge-tts first
        try:
            return await self._generate_edge_tts(text, language, cache_path)
        except Exception:
            pass

        # Fallback to pyttsx3
        try:
            return self._generate_pyttsx3(text, language, cache_path)
        except Exception:
            return None

    async def _generate_edge_tts(self, text: str, language: str, output_path: Path) -> str:
        """Generate audio using edge-tts (requires internet)."""
        import edge_tts

        voice = VOICES.get(language, VOICES.get("es"))
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return str(output_path)

    def _generate_pyttsx3(self, text: str, language: str, output_path: Path) -> str:
        """Generate audio using pyttsx3 (offline fallback)."""
        import pyttsx3

        if self._pyttsx3_engine is None:
            self._pyttsx3_engine = pyttsx3.init()

        engine = self._pyttsx3_engine
        engine.setProperty('rate', 150)
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        return str(output_path)

    def generate_audio_sync(self, text: str, language: str) -> Optional[str]:
        """Synchronous wrapper for generate_audio."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.generate_audio(text, language)
                    )
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(self.generate_audio(text, language))
        except RuntimeError:
            return asyncio.run(self.generate_audio(text, language))

    def get_cached_path(self, text: str, language: str) -> Optional[str]:
        """Check if audio is already cached. Returns path or None."""
        cache_path = self._get_cache_path(text, language)
        if cache_path.exists():
            return str(cache_path)
        return None
