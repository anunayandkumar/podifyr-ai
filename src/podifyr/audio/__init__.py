"""Audio sub-package: TTS synthesis and audio stitching."""

from podifyr.audio.synthesizer import generate_audio_chunks
from podifyr.audio.stitcher import stitch_audio


__all__ = [
    "generate_audio_chunks",
    "stitch_audio",
]
