"""Pronunciation recording and score display component."""

import os
import tempfile
import threading

import flet as ft

from lang_mastering.ui.theme import (
    SURFACE_COLOR, TEXT_COLOR, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR,
)


def build_pronunciation_recorder(
    expected_text: str,
    language: str,
    on_result=None,
) -> ft.Column:
    """Build a pronunciation recording component.

    Args:
        expected_text: The text the user should say
        language: Language code ('es' or 'tr')
        on_result: Callback with pronunciation result dict
    """
    status_text = ft.Text("Tap the microphone to start recording", size=14, color=TEXT_SECONDARY)
    score_display = ft.Container(visible=False)
    word_display = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, visible=False)

    is_recording = {"value": False}
    recorder_ref = {"recorder": None, "temp_path": None}

    record_btn = ft.IconButton(
        icon=ft.Icons.MIC,
        icon_color=ACCENT_COLOR,
        icon_size=48,
        tooltip="Record",
    )

    def toggle_recording(e):
        if not is_recording["value"]:
            start_recording()
        else:
            stop_recording()

    def start_recording():
        is_recording["value"] = True
        record_btn.icon = ft.Icons.STOP
        record_btn.icon_color = ERROR_COLOR
        status_text.value = "Recording... Tap to stop"

        # Create temp file for recording
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        recorder_ref["temp_path"] = temp_path

        # Use Flet AudioRecorder
        recorder = ft.AudioRecorder(
            audio_encoder=ft.AudioEncoder.WAV,
            output_path=temp_path,
        )
        recorder_ref["recorder"] = recorder
        record_btn.page.overlay.append(recorder)
        record_btn.page.update()
        recorder.start_recording()
        record_btn.update()
        status_text.update()

    def stop_recording():
        is_recording["value"] = False
        record_btn.icon = ft.Icons.MIC
        record_btn.icon_color = ACCENT_COLOR
        status_text.value = "Processing..."
        record_btn.update()
        status_text.update()

        recorder = recorder_ref.get("recorder")
        if recorder:
            recorder.stop_recording()

        # Process in background thread
        def process():
            temp_path = recorder_ref.get("temp_path")
            if not temp_path or not os.path.exists(temp_path):
                status_text.value = "Recording failed. Try again."
                status_text.update()
                return

            try:
                from lang_mastering.core.pronunciation import PronunciationEngine
                engine = PronunciationEngine()
                result = engine.score_pronunciation(temp_path, expected_text, language)
                show_result(result)
                if on_result:
                    on_result(result)
            except Exception as ex:
                status_text.value = f"Error: {str(ex)[:50]}"
                status_text.update()
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        threading.Thread(target=process, daemon=True).start()

    def show_result(result: dict):
        status_text.value = result["feedback"]
        score = result["score"]

        if score >= 80:
            status_text.color = SUCCESS_COLOR
        elif score >= 60:
            status_text.color = WARNING_COLOR
        else:
            status_text.color = ERROR_COLOR

        # Show score
        score_display.content = ft.Text(
            f"{score}%",
            size=48, weight=ft.FontWeight.BOLD,
            color=SUCCESS_COLOR if score >= 80 else WARNING_COLOR if score >= 60 else ERROR_COLOR,
        )
        score_display.visible = True

        # Show word-level feedback
        word_controls = []
        for ws in result.get("word_scores", []):
            color = SUCCESS_COLOR if ws["correct"] else ERROR_COLOR
            word_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(ws["expected"], size=14, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(ws["heard"] or "?", size=12, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    padding=5,
                )
            )
        word_display.controls = word_controls
        word_display.visible = True

        status_text.update()
        score_display.update()
        word_display.update()

    record_btn.on_click = toggle_recording

    return ft.Column([
        ft.Container(
            content=ft.Text(expected_text, size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
            bgcolor=SURFACE_COLOR, border_radius=12, padding=20, width=350,
        ),
        ft.Container(height=15),
        record_btn,
        status_text,
        ft.Container(height=10),
        score_display,
        word_display,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
