"""Event handler for clients of the server."""
import argparse
import json
import logging
import math
import os
import wave
import soundfile as sf
import numpy as np
from typing import Any, Dict, Optional
from InferenceInterfaces.ToucanTTSInterface import ToucanTTSInterface

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from wyoming.tts import Synthesize


_LOGGER = logging.getLogger(__name__)

# Mapping of subtypes to byte sizes
SUBTYPE_TO_BYTES = {
    'PCM_16': 2,
    'PCM_24': 3,
    'PCM_32': 4,
    'FLOAT': 4,
    'DOUBLE': 8,
}

class ToucanEventHandler(AsyncEventHandler):
    def __init__(
        self,
        toucan_tts: ToucanTTSInterface,
        wyoming_info: Info,
        cli_args: argparse.Namespace,
        *args,
        **kwargs,
    ) -> None:
        _LOGGER.debug("Initializing ToucanEventHandler")
        super().__init__(*args, **kwargs)
        
        self.tts = toucan_tts
        self.cli_args = cli_args
        self.wyoming_info_event = wyoming_info.event()
        _LOGGER.debug("ToucanEventHandler initialized with TTS interface")

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            _LOGGER.debug("Sent info")
            return True

        if not Synthesize.is_type(event.type):
            _LOGGER.warning("Unexpected event: %s", event)
            return True

        try:
            return await self._handle_event(event)
        except Exception as err:
            await self.write_event(
                Error(text=str(err), code=err.__class__.__name__).event()
            )
            raise err

    async def _handle_event(self, event: Event) -> bool:
        synthesize = Synthesize.from_event(event)
        _LOGGER.debug(synthesize)

        raw_text = synthesize.text

        # Join multiple lines
        text = " ".join(raw_text.strip().splitlines())

        # wave is a  NumPyArry
        wave, sr = self.tts(text)
        audio_data = wave.astype(np.float32)
        
        channels = 1  # Mono Audio (falls mehrkanalig, entsprechend anpassen)
        bytes_per_sample = 2 * channels  # 2 Bytes für 16-Bit PCM
        
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
        bytes_per_chunk = bytes_per_sample * self.cli_args.samples_per_chunk
        num_chunks = int(math.ceil(len(audio_bytes) / bytes_per_chunk))

        # Split into chunks
        for i in range(num_chunks):
            offset = i * bytes_per_chunk
            chunk = audio_bytes[offset : offset + bytes_per_chunk]
            await self.write_event(
                AudioChunk(
                    audio=chunk,
                    rate=sr,
                    width=2,  # 2 bytes for 16-bit PCM
                    channels=channels,
                ).event(),
            )

        await self.write_event(AudioStop().event())
        _LOGGER.debug("Completed request")

        return True
