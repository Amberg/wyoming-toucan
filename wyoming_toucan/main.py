import asyncio
import logging
import argparse
from wyoming.server import AsyncServer
from wyoming.info import Attribution, Info, TtsProgram, TtsVoice, TtsVoiceSpeaker
from wyoming.server import AsyncServer
from functools import partial
from .handler import ToucanEventHandler

_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    parser = argparse.ArgumentParser()
    print("Roucan Wyoming Server is starting...")
        # Start server
    server = AsyncServer.from_uri("tcp://0.0.0.0:10200")
    _LOGGER.info("Ready")
    voices = [
    TtsVoice("bruce Willis", 
             installed=True,
             description="A voice that sounds like Bruce Willis",
             languages=["de"],
                         attribution=Attribution(
                            name="rhasspy", url="https://github.com/rhasspy/piper"
                        ),
                         version="1.0",
             ),
    ]
    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="toucan",
                description="A fast, local, neural text to speech engine",
                attribution=Attribution(
                    name="toucan", url="https://github.com/DigitalPhonetics/IMS-Toucan"
                ),
                installed=True,
                voices=sorted(voices, key=lambda v: v.name),
                version="1.0",
            )
        ],
    )
    parser.add_argument("--samples-per-chunk", type=int, default=1024)

    args = parser.parse_args()

    await server.run(
        partial(
            ToucanEventHandler,
            wyoming_info,
            args,
        )
)

if __name__ == "__main__":
    asyncio.run(main())