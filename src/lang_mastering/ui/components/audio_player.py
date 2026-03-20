"""Speaker icon button for audio playback."""

import threading

import flet as ft

from lang_mastering.core.audio import AudioManager
from lang_mastering.ui.theme import ACCENT_COLOR, TEXT_SECONDARY


def build_audio_button(
    text: str,
    language: str,
    audio_manager: AudioManager,
    size: int = 24,
) -> ft.IconButton:
    """Build a speaker icon button that plays TTS audio on click."""

    btn = ft.IconButton(
        icon=ft.Icons.VOLUME_UP,
        icon_color=ACCENT_COLOR,
        icon_size=size,
        tooltip="Play audio",
    )

    def play_audio(e):
        btn.icon_color = TEXT_SECONDARY
        btn.update()

        def _generate_and_play():
            audio_path = audio_manager.generate_audio_sync(text, language)
            if audio_path:
                # Use Flet's Audio control
                audio = ft.Audio(src=audio_path, autoplay=True)
                btn.page.overlay.append(audio)
                btn.page.update()

            btn.icon_color = ACCENT_COLOR
            btn.update()

        threading.Thread(target=_generate_and_play, daemon=True).start()

    btn.on_click = play_audio
    return btn
