"""Audio sub-package: TTS synthesis and audio stitching."""

from podifyr.audio.stitcher import stitch_audio
from podifyr.audio.synthesizer import generate_audio_chunks


__all__ = [
    "generate_audio_chunks",
    "stitch_audio",
]
