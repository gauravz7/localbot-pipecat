#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import argparse
import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
#from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from gemini_multimodal_live_vertex.gemini import GeminiMultimodalLiveLLMService

from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
#from pipecat.transports.services.daily import DailyParams
from pipecat.services.gemini_multimodal_live.gemini import InputParams
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalModalities

load_dotenv(override=True)

PROJECT_ID=os.getenv("PROJECT_ID")
MODEL=os.getenv("MODEL")
LOCATION=os.getenv("LOCATION")


# Function handlers for the LLM
search_tool = {"google_search": {}}
#tools = [search_tool]
tools = []

system_instruction = """
Just be friendly and engaging. You are a helpful assistant.
You can answer questions, provide information, and engage in casual conversation.

"""


# We store functions so objects (e.g. SileroVADAnalyzer) don't get
# instantiated. The function will be called when the desired transport gets
# selected.
transport_params = {

    "twilio": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        # set stop_secs to something roughly similar to the internal setting
        # of the Multimodal Live api, just to align events. This doesn't really
        # matter because we can only use the Multimodal Live API's phrase
        # endpointing, for now.
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        # set stop_secs to something roughly similar to the internal setting
        # of the Multimodal Live api, just to align events. This doesn't really
        # matter because we can only use the Multimodal Live API's phrase
        # endpointing, for now.
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
    ),
}


async def run_example(transport: BaseTransport, _: argparse.Namespace, handle_sigint: bool):
    logger.info(f"Starting bot")

    # Initialize the Gemini Multimodal Live model
    llm = GeminiMultimodalLiveLLMService(
        api_key=None,
        project_id=PROJECT_ID,
        location=LOCATION,
        model=MODEL,
        tools=tools,
        voice_id="Aoede",
        system_instruction=system_instruction,
        transcribe_user_audio=False,  # Disable speech-to-text for user input if you don't need it
        transcribe_model_audio=False,  # Disable speech-to-text for model responses
        params=InputParams(modalities=GeminiMultimodalModalities.AUDIO ,max_tokens=100 ),
    )


    context = OpenAILLMContext(
        [
            {
                "role": "user",
                "content": "Start by greeting the user warmly, introducing yourself, and mentioning the current day. Be friendly and engaging to set a positive tone for the interaction.",
            }
        ],
    )
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            context_aggregator.user(),  # User responses
            llm,  # LLM
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Kick off the conversation.
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=handle_sigint)

    await runner.run(task)


if __name__ == "__main__":
    from pipecat.examples.run import main

    main(run_example, transport_params=transport_params)