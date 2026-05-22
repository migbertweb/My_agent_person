import os
import re
import subprocess
import tempfile
import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable
from utils.logger import logger


def strip_markdown(text: str) -> str:
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\|', ', ', text)
    text = re.sub(r'[*_~]{1,3}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class TTSProvider(ABC):
    @abstractmethod
    def speak(self, text: str) -> bool:
        pass

    @abstractmethod
    def stop(self):
        pass


class EdgeTTS(TTSProvider):
    def __init__(self, voice: str = "es-ES-AlvaroNeural",
                 rate: str = "0%", pitch: str = "0%"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self._process: Optional[subprocess.Popen] = None
        logger.info(f"EdgeTTS iniciado con voz: {voice}, rate: {rate}, pitch: {pitch}")

    def speak(self, text: str) -> bool:
        if not text.strip():
            return False

        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            asyncio.run(self._generate_audio(text, tmp_path))
            self._play_audio(tmp_path)
            return True
        except Exception as e:
            logger.error(f"Error en EdgeTTS: {e}")
            return False

    async def _generate_audio(self, text: str, output_path: str):
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
        await communicate.save(output_path)

    def _play_audio(self, file_path: str):
        player = self._find_player()
        if not player:
            logger.error("No se encontró reproductor de audio")
            return

        try:
            if player == "ffplay":
                self._process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif player == "mpv":
                self._process = subprocess.Popen(
                    ["mpv", "--no-video", "--really-quiet", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif player in ("paplay", "pw-play"):
                self._process = subprocess.Popen(
                    [player, file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif player == "aplay":
                self._process = subprocess.Popen(
                    ["aplay", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            if self._process:
                self._process.wait()
        except Exception as e:
            logger.error(f"Error reproduciendo audio: {e}")
        finally:
            self._cleanup_file(file_path)

    def _find_player(self) -> Optional[str]:
        for cmd in ["ffplay", "mpv", "pw-play", "paplay", "aplay"]:
            if shutil.which(cmd):
                return cmd
        return None

    def _cleanup_file(self, file_path: str):
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except Exception:
                self._process.kill()
            self._process = None


class PiperTTS(TTSProvider):
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._find_piper_model()
        self._process: Optional[subprocess.Popen] = None
        logger.info(f"PiperTTS iniciado con modelo: {self.model_path}")

    def _find_piper_model(self) -> Optional[str]:
        common_paths = [
            "/usr/share/piper/voices/es_ES/",
            "/usr/local/share/piper/voices/es_ES/",
            str(Path.home() / ".local/share/piper/voices/es_ES/"),
            str(Path.home() / ".piper/voices/es_ES/"),
        ]
        for base in common_paths:
            model_dir = Path(base)
            if model_dir.exists():
                for model_file in model_dir.glob("*.onnx"):
                    return str(model_file)
        return None

    def speak(self, text: str) -> bool:
        if not text.strip() or not self.model_path:
            return False

        if not shutil.which("piper"):
            logger.error("piper no está instalado en el sistema")
            return False

        try:
            self._process = subprocess.Popen(
                ["piper", "--model", self.model_path, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            player = self._find_player()
            if not player:
                return False

            play_cmd = {
                "ffplay": ["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet", "-f", "s16le", "-ar", "22050", "-ac", "1", "-"],
                "aplay": ["aplay", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                "paplay": ["paplay", "--format=s16le", "--rate=22050", "--channels=1"],
            }.get(player)

            if not play_cmd:
                return False

            player_proc = subprocess.Popen(
                play_cmd,
                stdin=self._process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self._process.stdin.write(text.encode("utf-8"))
            self._process.stdin.close()
            self._process.wait()
            player_proc.wait()
            return True
        except Exception as e:
            logger.error(f"Error en PiperTTS: {e}")
            return False
        finally:
            self._process = None

    def _find_player(self) -> Optional[str]:
        for cmd in ["ffplay", "aplay", "paplay"]:
            if shutil.which(cmd):
                return cmd
        return None

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except Exception:
                self._process.kill()
            self._process = None


def create_tts_provider(provider: str = "edge", voice: str = "es-ES-AlvaroNeural",
                        rate: str = "0%", pitch: str = "0%",
                        model_path: Optional[str] = None) -> TTSProvider:
    if provider == "piper":
        return PiperTTS(model_path)
    return EdgeTTS(voice, rate, pitch)
