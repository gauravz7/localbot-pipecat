import os
import sys
import asyncio
import json
import time
import base64
import re
import logging

import boto3
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.frames.frames import (
    EndFrame,
    TTSSpeakFrame,
    EndTaskFrame,
)
from pipecat.frames.frames import BotInterruptionFrame, EndFrame
from pipecat.services.ai_services import LLMService 
from pipecat.processors.frame_processor import FrameDirection

#from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalModalities, InputParams
from gemini_multimodal_live_vertex.gemini import GeminiMultimodalLiveLLMService

from pipecat.transports.network.websocket_server import (
    WebsocketServerParams,
    WebsocketServerTransport,
)

from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.adapters.schemas.function_schema import FunctionSchema

load_dotenv(override=True)

#logger.remove(0)
logger.add(sys.stderr, level="DEBUG")




load_dotenv()

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

sys.path.append("./gemini_multimodal_live_vertex")



class SessionTimeoutHandler:
    """Handles actions to be performed when a session times out.
    Inputs:
    - task: Pipeline task (used to queue frames).
    - tts: TTS service (used to generate speech output).
    """

    def __init__(self, task, tts):
        self.task = task
        self.tts = tts
        self.background_tasks = set()

    async def handle_timeout(self, client_address):
        """Handles the timeout event for a session."""
        try:
            logger.info(f"Connection timeout for {client_address}")

            # Queue a BotInterruptionFrame to notify the user
            await self.task.queue_frames([BotInterruptionFrame()])

            # Send the TTS message to inform the user about the timeout
            await self.tts.say(
                "I'm sorry, we are ending the call now. Please feel free to reach out again if you need assistance."
            )

            # Start the process to gracefully end the call in the background
            end_call_task = asyncio.create_task(self._end_call())
            self.background_tasks.add(end_call_task)
            end_call_task.add_done_callback(self.background_tasks.discard)
        except Exception as e:
            logger.error(f"Error during session timeout handling: {e}")

    async def _end_call(self):
        """Completes the session termination process after the TTS message."""
        try:
            # Wait for a duration to ensure TTS has completed
            await asyncio.sleep(15)

            # Queue both BotInterruptionFrame and EndFrame to conclude the session
            await self.task.queue_frames([BotInterruptionFrame(), EndFrame()])

            logger.info("TTS completed and EndFrame pushed successfully.")
        except Exception as e:
            logger.error(f"Error during call termination: {e}")


PROJECT_ID=os.getenv("PROJECT_ID")
MODEL=os.getenv("MODEL")
LOCATION=os.getenv("LOCATION")

system_instruction = """"
You are a helpful LLM  call. 
Your goal is to demonstrate your capabilities in a succinct way. 
Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.

Terminate on User Closure:
If the user expresses a desire to end the conversation or user does not require any further assistance  (e.g., "goodbye", "dhanyawad", "that's all", "I'm done", "thank you", "nahi", "kuch aur nahi chahiye", or similar sentiments indicating closure)
 **immediately** Invoke the tool : "end_call" tool.

"""




async def main():

    transport = WebsocketServerTransport(
        params=WebsocketServerParams(
            serializer=ProtobufFrameSerializer(),
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=True,
            vad_analyzer=SileroVADAnalyzer(),
            session_timeout=60 * 3,  # 3 minutes
        )
    )
    # llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

    # stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    # tts = CartesiaTTSService(
    #     api_key=os.getenv("CARTESIA_API_KEY"),
    #     voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",  # British Lady
    # )





    '''
    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        system_instruction=system_instruction,
        #tools=tools,
        voice_id="Puck",                    # Voices: Aoede, Charon, Fenrir, Kore, Puck
        transcribe_user_audio=True,          # Enable speech-to-text for user input
        transcribe_model_audio=True,         # Enable speech-to-text for model responses
    )
    '''



    # Define function schemas for tools
    terminate_call_function = FunctionSchema(
        name="end_call",
        description="Call this function to terminate the call.",
        properties={},
        required=[],
    )

    tools = ToolsSchema(standard_tools=[terminate_call_function])




    llm = GeminiMultimodalLiveLLMService(
        api_key=None,
        project_id="vital-octagon-19612",
        location="us-central1",
        model=MODEL,
        voice_id="Aoede",
        tools=tools,
        system_instruction=system_instruction,
        transcribe_user_audio=False,  # Disable speech-to-text for user input if you don't need it
        transcribe_model_audio=False,  # Disable speech-to-text for model responses
        params=InputParams(modalities=GeminiMultimodalModalities.AUDIO ,max_tokens=100 ),
    )

    async def end_call_handler(
        function_name, toll_call_id, args, llm, context, result_callback
    ):
        await llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)

    async def callback_end_call(function_name, llm, context):
        await task.queue_frame(TTSSpeakFrame("Thanks for Calling, Goodbye!"))
        logger.debug(f"Ending call with function_name: {function_name}")

    llm.register_function("end_call", end_call_handler)

    #llm.register_function("get_payment_info", payment_kb)

        
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "You are a helpful LLM in an audio call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.",
    #     },
    # ]

    # context = OpenAILLMContext(messages)

    context = OpenAILLMContext(
        
        [{"role": "user", "content": "Say hello."}],
    )
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Websocket input from client
            # stt,  # Speech-To-Text
            context_aggregator.user(),
            llm,  # LLM
            # tts,  # Text-To-Speech
            transport.output(),  # Websocket output to client
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))




    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        # Kick off the conversation.
        # messages.append({"role": "system", "content": "Please introduce yourself to the user."})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.queue_frames([EndFrame()])

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())