#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import json
import os


# Suppress gRPC fork warnings
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"

from typing import AsyncGenerator, Generator, Literal, Optional

from loguru import logger
from pydantic import BaseModel

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.services.tts_service import TTSService
from pipecat.transcriptions.language import Language

try:
    from google.auth import default
    from google.auth.exceptions import GoogleAuthError
    from google.cloud import texttospeech as texttospeech_v1  # Using the streaming class
    from google.oauth2 import service_account

except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use Google AI, you need to `pip install pipecat-ai[google]`. Also, set `GOOGLE_APPLICATION_CREDENTIALS` environment variable."
    )
    raise Exception(f"Missing module: {e}")


def language_to_google_tts_language(language: Language) -> Optional[str]:
    language_map = {
        # Afrikaans
        Language.AF: "af-ZA",
        Language.AF_ZA: "af-ZA",
        # Arabic
        Language.AR: "ar-XA",
        # Bengali
        Language.BN: "bn-IN",
        Language.BN_IN: "bn-IN",
        # Bulgarian
        Language.BG: "bg-BG",
        Language.BG_BG: "bg-BG",
        # Catalan
        Language.CA: "ca-ES",
        Language.CA_ES: "ca-ES",
        # Chinese (Mandarin and Cantonese)
        Language.ZH: "cmn-CN",
        Language.ZH_CN: "cmn-CN",
        Language.ZH_TW: "cmn-TW",
        Language.ZH_HK: "yue-HK",
        # Czech
        Language.CS: "cs-CZ",
        Language.CS_CZ: "cs-CZ",
        # Danish
        Language.DA: "da-DK",
        Language.DA_DK: "da-DK",
        # Dutch
        Language.NL: "nl-NL",
        Language.NL_BE: "nl-BE",
        Language.NL_NL: "nl-NL",
        # English
        Language.EN: "en-US",
        Language.EN_US: "en-US",
        Language.EN_AU: "en-AU",
        Language.EN_GB: "en-GB",
        Language.EN_IN: "en-IN",
        # Estonian
        Language.ET: "et-EE",
        Language.ET_EE: "et-EE",
        # Filipino
        Language.FIL: "fil-PH",
        Language.FIL_PH: "fil-PH",
        # Finnish
        Language.FI: "fi-FI",
        Language.FI_FI: "fi-FI",
        # French
        Language.FR: "fr-FR",
        Language.FR_CA: "fr-CA",
        Language.FR_FR: "fr-FR",
        # Galician
        Language.GL: "gl-ES",
        Language.GL_ES: "gl-ES",
        # German
        Language.DE: "de-DE",
        Language.DE_DE: "de-DE",
        # Greek
        Language.EL: "el-GR",
        Language.EL_GR: "el-GR",
        # Gujarati
        Language.GU: "gu-IN",
        Language.GU_IN: "gu-IN",
        # Hebrew
        Language.HE: "he-IL",
        Language.HE_IL: "he-IL",
        # Hindi
        Language.HI: "hi-IN",
        Language.HI_IN: "hi-IN",
        # Hungarian
        Language.HU: "hu-HU",
        Language.HU_HU: "hu-HU",
        # Icelandic
        Language.IS: "is-IS",
        Language.IS_IS: "is-IS",
        # Indonesian
        Language.ID: "id-ID",
        Language.ID_ID: "id-ID",
        # Italian
        Language.IT: "it-IT",
        Language.IT_IT: "it-IT",
        # Japanese
        Language.JA: "ja-JP",
        Language.JA_JP: "ja-JP",
        # Kannada
        Language.KN: "kn-IN",
        Language.KN_IN: "kn-IN",
        # Korean
        Language.KO: "ko-KR",
        Language.KO_KR: "ko-KR",
        # Latvian
        Language.LV: "lv-LV",
        Language.LV_LV: "lv-LV",
        # Lithuanian
        Language.LT: "lt-LT",
        Language.LT_LT: "lt-LT",
        # Malay
        Language.MS: "ms-MY",
        Language.MS_MY: "ms-MY",
        # Malayalam
        Language.ML: "ml-IN",
        Language.ML_IN: "ml-IN",
        # Marathi
        Language.MR: "mr-IN",
        Language.MR_IN: "mr-IN",
        # Norwegian
        Language.NO: "nb-NO",
        Language.NB: "nb-NO",
        Language.NB_NO: "nb-NO",
        # Polish
        Language.PL: "pl-PL",
        Language.PL_PL: "pl-PL",
        # Portuguese
        Language.PT: "pt-PT",
        Language.PT_BR: "pt-BR",
        Language.PT_PT: "pt-PT",
        # Punjabi
        Language.PA: "pa-IN",
        Language.PA_IN: "pa-IN",
        # Romanian
        Language.RO: "ro-RO",
        Language.RO_RO: "ro-RO",
        # Russian
        Language.RU: "ru-RU",
        Language.RU_RU: "ru-RU",
        # Serbian
        Language.SR: "sr-RS",
        Language.SR_RS: "sr-RS",
        # Slovak
        Language.SK: "sk-SK",
        Language.SK_SK: "sk-SK",
        # Spanish
        Language.ES: "es-ES",
        Language.ES_ES: "es-ES",
        Language.ES_US: "es-US",
        # Swedish
        Language.SV: "sv-SE",
        Language.SV_SE: "sv-SE",
        # Tamil
        Language.TA: "ta-IN",
        Language.TA_IN: "ta-IN",
        # Telugu
        Language.TE: "te-IN",
        Language.TE_IN: "te-IN",
        # Thai
        Language.TH: "th-TH",
        Language.TH_TH: "th-TH",
        # Turkish
        Language.TR: "tr-TR",
        Language.TR_TR: "tr-TR",
        # Ukrainian
        Language.UK: "uk-UA",
        Language.UK_UA: "uk-UA",
        # Vietnamese
        Language.VI: "vi-VN",
        Language.VI_VN: "vi-VN",
    }

    return language_map.get(language)


class GoogleTTSService(TTSService):
    class InputParams(BaseModel):
        pitch: Optional[str] = None
        rate: Optional[str] = None
        volume: Optional[str] = None
        emphasis: Optional[Literal["strong", "moderate", "reduced", "none"]] = None
        language: Optional[Language] = Language.EN
        gender: Optional[Literal["male", "female", "neutral"]] = None
        google_style: Optional[Literal["apologetic", "calm", "empathetic", "firm", "lively"]] = None
        # New parameters for streaming
        chunk_size: int = 100  # Number of characters per chunk for streaming

    def __init__(
        self,
        *,
        credentials: Optional[str] = None,
        credentials_path: Optional[str] = None,
        voice_id: str = "en-US-Neural2-A",
        sample_rate: Optional[int] = None,
        params: InputParams = InputParams(),
        **kwargs,
    ):
        super().__init__( **kwargs)

        self._settings = {
            "pitch": params.pitch,
            "rate": params.rate,
            "volume": params.volume,
            "emphasis": params.emphasis,
            "language": self.language_to_service_language(params.language)
            if params.language
            else "en-US",
            "gender": params.gender,
            "google_style": params.google_style,
            "chunk_size": params.chunk_size,
        }
        self.set_voice(voice_id)
        self._client = self._create_client(credentials, credentials_path)

    def _create_client(
        self, credentials: Optional[str], credentials_path: Optional[str]
    ) -> texttospeech_v1.TextToSpeechClient:
        creds: Optional[service_account.Credentials] = None

        # Create a Google Cloud service account for the Cloud Text-to-Speech API
        # Using either the provided credentials JSON string or the path to a service account JSON
        # file, create a Google Cloud service account and use it to authenticate with the API.
        if credentials:
            # Use provided credentials JSON string
            json_account_info = json.loads(credentials)
            creds = service_account.Credentials.from_service_account_info(json_account_info)
        elif credentials_path:
            # Use service account JSON file if provided
            creds = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            try:
                creds, project_id = default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            except GoogleAuthError:
                pass

        if not creds:
            raise ValueError("No valid credentials provided.")

        return texttospeech_v1.TextToSpeechClient(credentials=creds)

    def can_generate_metrics(self) -> bool:
        return True

    def language_to_service_language(self, language: Language) -> Optional[str]:
        return language_to_google_tts_language(language)

    def _construct_ssml(self, text: str) -> str:
        ssml = "<speak>"

        # Voice tag
        voice_attrs = [f"name='{self._voice_id}'"]

        language = self._settings["language"]
        voice_attrs.append(f"language='{language}'")

        if self._settings["gender"]:
            voice_attrs.append(f"gender='{self._settings['gender']}'")
        ssml += f"<voice {' '.join(voice_attrs)}>"

        # Prosody tag
        prosody_attrs = []
        if self._settings["pitch"]:
            prosody_attrs.append(f"pitch='{self._settings['pitch']}'")
        if self._settings["rate"]:
            prosody_attrs.append(f"rate='{self._settings['rate']}'")
        if self._settings["volume"]:
            prosody_attrs.append(f"volume='{self._settings['volume']}'")

        if prosody_attrs:
            ssml += f"<prosody {' '.join(prosody_attrs)}>"

        # Emphasis tag
        if self._settings["emphasis"]:
            ssml += f"<emphasis level='{self._settings['emphasis']}'>"

        # Google style tag
        if self._settings["google_style"]:
            ssml += f"<google:style name='{self._settings['google_style']}'>"

        ssml += text

        # Close tags
        if self._settings["google_style"]:
            ssml += "</google:style>"
        if self._settings["emphasis"]:
            ssml += "</emphasis>"
        if prosody_attrs:
            ssml += "</prosody>"
        ssml += "</voice></speak>"

        return ssml
    '''
    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks for streaming, respecting sentence boundaries when possible."""
        chunks = []
        chunk_size = self._settings["chunk_size"]
        
        # Try to split on sentence boundaries first
        sentences = []
        for sentence in text.replace(".", ". ").replace("!", "! ").replace("?", "? ").split(". "):
            if sentence:
                sentences.append(sentence.strip())
        
        current_chunk = ""
        for sentence in sentences:
            # If sentence is too large, split it
            if len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Further split long sentences
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= chunk_size:
                        if temp_chunk:
                            temp_chunk += " "
                        temp_chunk += word
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = word
                
                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                # Add sentence to current chunk if it fits
                if len(current_chunk) + len(sentence) + 2 <= chunk_size:  # +2 for ". "
                    if current_chunk:
                        current_chunk += ". "
                    current_chunk += sentence
                else:
                    # Chunk is full, add it and start a new one
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    '''

    '''
    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks for streaming, respecting natural language boundaries.
        
        Prioritizes:
        1. Sentence boundaries (. ! ?)
        2. Clause boundaries (, ; :)
        3. Groups of 5 words as a fallback
        
        Returns a list of text chunks ready for synthesis.
        """
        # Maximum words per chunk when no natural breaks are available
        MAX_WORDS_PER_CHUNK = 3
        
        # Normalize spacing and ensure proper sentence breaks
        normalized_text = text.replace(".", ". ").replace("!", "! ").replace("?", "? ")
        normalized_text = normalized_text.replace(".  ", ". ").replace("!  ", "! ").replace("?  ", "? ")
        
        # First-level split: Break at sentence boundaries
        sentence_splits = []
        for sentence in normalized_text.split(". "):
            if not sentence.strip():
                continue
                
            for exclamation in sentence.split("! "):
                if not exclamation.strip():
                    continue
                    
                for question in exclamation.split("? "):
                    if question.strip():
                        # Add the proper punctuation back
                        if "!" in exclamation:
                            sentence_splits.append(f"{question.strip()}!")
                        elif "?" in sentence:
                            sentence_splits.append(f"{question.strip()}?")
                        else:
                            sentence_splits.append(f"{question.strip()}.")
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentence_splits:
            # If sentence is relatively short, add it as a whole chunk
            if len(sentence.split()) <= MAX_WORDS_PER_CHUNK:
                if current_chunk:
                    chunks.append(current_chunk)
                chunks.append(sentence)
                current_chunk = ""
                continue
            
            # For longer sentences, try to split at clause boundaries
            clause_splits = []
            for clause in sentence.replace(", ", " , ").replace("; ", " ; ").replace(": ", " : ").split():
                if clause in [",", ";", ":"]:
                    # Add punctuation to the previous clause
                    if clause_splits:
                        clause_splits[-1] = clause_splits[-1] + clause
                    continue
                clause_splits.append(clause)
            
            # Group clauses into chunks of MAX_WORDS_PER_CHUNK
            temp_chunk = []
            for clause in clause_splits:
                temp_chunk.append(clause)
                
                # Check if we have punctuation indicating a good break point
                has_break = any(clause.endswith(p) for p in [",", ";", ":"])
                
                if has_break or len(temp_chunk) >= MAX_WORDS_PER_CHUNK:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = " ".join(temp_chunk)
                    temp_chunk = []
            
            # Add any remaining words from this sentence
            if temp_chunk:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = " ".join(temp_chunk)
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Clean up any double spaces and fix punctuation spacing
        result = []
        for chunk in chunks:
            # Fix spacing around punctuation
            chunk = chunk.replace(" ,", ",").replace(" ;", ";").replace(" :", ":")
            # Remove any double spaces
            chunk = " ".join(chunk.split())
            result.append(chunk)
        print(f"Chunked text: {result}")
        return result

        '''

    '''
    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks by first breaking at sentence boundaries,
        then splitting each sentence into chunks of MAX_WORDS_PER_CHUNK words.
        Preserves all original punctuation and spacing.
        
        Returns a list of text chunks ready for synthesis.
        """
        # Maximum words per chunk
        MAX_WORDS_PER_CHUNK = 3
         
        # First split by sentence boundaries
        sentence_boundaries = ['.', '!', '?']
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(text):
            current_sentence += text[i]
            
            # Check if we're at a sentence boundary
            if text[i] in sentence_boundaries:
                # Look ahead to check if this is really the end of a sentence
                # (e.g., not part of an abbreviation like "Dr." or a decimal like "3.14")
                is_sentence_end = True
                
                # If not at the end of text and next char is a quotation mark or closing parenthesis
                if i + 1 < len(text) and text[i+1] in ['\"', '\'', ')', ']', '}']:
                    # Include the closing punctuation in this sentence
                    i += 1
                    current_sentence += text[i]
                
                sentences.append(current_sentence)
                current_sentence = ""
            
            i += 1
        
        # Add any remaining text as a sentence
        if current_sentence:
            sentences.append(current_sentence)
        
        # Now split each sentence into word chunks
        chunks = []
        for sentence in sentences:
            # Split the sentence into words while preserving punctuation and spaces
            tokens = []
            current_word = ""
            
            for char in sentence:
                if char.isalnum() or char in "'":  # Consider apostrophes part of words
                    current_word += char
                else:
                    # When we hit non-alphanumeric chars (spaces, punctuation)
                    if current_word:  # If we have a word built up
                        tokens.append(current_word)  # Add the word
                        current_word = ""
                    tokens.append(char)  # Add the punctuation/space as its own token
            
            # Don't forget the last word if sentence doesn't end with punctuation
            if current_word:
                tokens.append(current_word)
            
            # Create chunks with exactly MAX_WORDS_PER_CHUNK actual words (not counting punctuation/spaces)
            current_chunk = []
            word_count = 0
            
            for token in tokens:
                current_chunk.append(token)
                if token.strip() and any(c.isalnum() for c in token):  # Count only actual words
                    word_count += 1
                
                if word_count == MAX_WORDS_PER_CHUNK:
                    # Join all tokens including punctuation and spaces exactly as they were
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    word_count = 0
            
            # Add the final chunk if there's anything left
            if current_chunk:
                chunks.append("".join(current_chunk))
        
        print(f"Chunked text: {chunks}")
        return chunks
    
    '''

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks by first breaking at sentence boundaries (including Hindi punctuation),
        newlines, then splitting each sentence into chunks of MAX_WORDS_PER_CHUNK words.
        Preserves all original punctuation and spacing.
        Ensures each chunk ends with a space.
        
        Returns a list of text chunks ready for synthesis.
        """
        # Maximum words per chunk
        MAX_WORDS_PER_CHUNK = 3
        
        # First split by sentence boundaries, including Hindi punctuations and newlines
        sentence_boundaries = ['.', '!', '?', '|', '\n']
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(text):
            # Handle newline as a special case - it's both a boundary and should be included
            if text[i] == '\n':
                current_sentence += text[i]
                sentences.append(current_sentence)
                current_sentence = ""
                i += 1
                continue
                
            current_sentence += text[i]
            
            # Check if we're at a sentence boundary
            if text[i] in sentence_boundaries:
                # Look ahead to check if this is really the end of a sentence
                # (e.g., not part of an abbreviation like "Dr." or a decimal like "3.14")
                
                # If not at the end of text and next char is a quotation mark or closing parenthesis
                if i + 1 < len(text) and text[i+1] in ['\"', '\'', ')', ']', '}']:
                    # Include the closing punctuation in this sentence
                    i += 1
                    current_sentence += text[i]
                
                sentences.append(current_sentence)
                current_sentence = ""
            
            i += 1
        
        # Add any remaining text as a sentence
        if current_sentence:
            sentences.append(current_sentence)
        
        # Now split each sentence into word chunks
        chunks = []
        for sentence in sentences:
            # Split the sentence into words while preserving punctuation and spaces
            tokens = []
            current_word = ""
            
            for char in sentence:
                if char.isalnum() or char in "'":  # Consider apostrophes part of words
                    current_word += char
                else:
                    # When we hit non-alphanumeric chars (spaces, punctuation)
                    if current_word:  # If we have a word built up
                        tokens.append(current_word)  # Add the word
                        current_word = ""
                    tokens.append(char)  # Add the punctuation/space as its own token
            
            # Don't forget the last word if sentence doesn't end with punctuation
            if current_word:
                tokens.append(current_word)
            
            # Create chunks with exactly MAX_WORDS_PER_CHUNK actual words
            # Ensure each chunk ends with a space
            current_chunk = []
            word_count = 0
            
            for i, token in enumerate(tokens):
                current_chunk.append(token)
                
                # Count if it's a real word
                if token.strip() and any(c.isalnum() for c in token):
                    word_count += 1
                
                # If we've hit MAX_WORDS_PER_CHUNK words and either:
                # 1. The current token is a space, OR
                # 2. We have more tokens and can add the next space
                if word_count == MAX_WORDS_PER_CHUNK:
                    # Check if current token is a space
                    if token.isspace():
                        chunks.append("".join(current_chunk))
                        current_chunk = []
                        word_count = 0
                    # Check if next token is a space we can include
                    elif i + 1 < len(tokens) and tokens[i+1].isspace():
                        current_chunk.append(tokens[i+1])
                        chunks.append("".join(current_chunk))
                        current_chunk = []
                        word_count = 0
                        i += 1  # Skip the space token since we've used it
                    # Otherwise, add a space manually
                    else:
                        chunks.append("".join(current_chunk) + " ")
                        current_chunk = []
                        word_count = 0
            
            # Add the final chunk if there's anything left
            if current_chunk:
                # Ensure it ends with a space
                final_chunk = "".join(current_chunk)
                if not final_chunk.endswith(' '):
                    final_chunk += " "
                chunks.append(final_chunk)
        
        # Final cleanup to ensure all chunks end with a space
        for i in range(len(chunks)):
            if not chunks[i].endswith(' '):
                chunks[i] += " "
        
        print(f"Chunked text: {chunks}")
        return chunks



    def _create_streaming_request_generator(self, text: str) -> Generator:
        """Create a generator for streaming TTS requests."""
        # Determine if the voice supports SSML
        is_chirp_voice = "chirp" in self._voice_id.lower()
        is_journey_voice = "journey" in self._voice_id.lower()
        use_ssml = not (is_chirp_voice or is_journey_voice)
        
        # Create config request
        streaming_config = texttospeech_v1.StreamingSynthesizeConfig(
            voice=texttospeech_v1.VoiceSelectionParams(
                language_code=self._settings["language"],
                name=self._voice_id,
            ),
            #audio_config=texttospeech_v1.AudioConfig(
            #    audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
            #    sample_rate_hertz=self.sample_rate,
            #),
        )
        
        config_request = texttospeech_v1.StreamingSynthesizeRequest(
            streaming_config=streaming_config
        )
        
        # Split text into chunks for streaming
        text_chunks = self._chunk_text(text)
        
        def request_generator():
            yield config_request
            
            for chunk in text_chunks:
                if use_ssml:
                    # For non-Chirp/Journey voices, use SSML for each chunk
                    ssml = self._construct_ssml(chunk)
                    yield texttospeech_v1.StreamingSynthesizeRequest(
                        input=texttospeech_v1.StreamingSynthesisInput(ssml=ssml)
                    )
                else:
                    # For Chirp and Journey voices, use plain text
                    yield texttospeech_v1.StreamingSynthesizeRequest(
                        input=texttospeech_v1.StreamingSynthesisInput(text=chunk)
                    )
        
        return request_generator()

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        logger.debug(f"{self}: Generating streaming TTS for [{text}]")

        try:
            await self.start_ttfb_metrics()
            await self.start_tts_usage_metrics(text)

            yield TTSStartedFrame()
            
            # Create the request generator
            request_generator = self._create_streaming_request_generator(text)
            
            # Use asyncio to run the streaming synthesis in a thread pool
            loop = asyncio.get_running_loop()
            
            # Get the streaming responses
            streaming_responses = await loop.run_in_executor(
                None, 
                lambda: self._client.streaming_synthesize(request_generator)
            )
            
            ttfb_sent = False
            
            # Process each streaming response
            for response in streaming_responses:
                if not ttfb_sent:
                    await self.stop_ttfb_metrics()
                    ttfb_sent = True
                
                # Stream the audio content
                audio_content = response.audio_content
                
                # Read and yield audio data in chunks
                CHUNK_SIZE = 1024
                for i in range(0, len(audio_content), CHUNK_SIZE):
                    chunk = audio_content[i : i + CHUNK_SIZE]
                    if not chunk:
                        break
                    
                    frame = TTSAudioRawFrame(chunk, self.sample_rate, 1)
                    yield frame
                    await asyncio.sleep(0.01)  # Allow other tasks to run

            yield TTSStoppedFrame()

        except Exception as e:
            logger.exception(f"{self} error generating streaming TTS: {e}")
            error_message = f"Streaming TTS generation error: {str(e)}"
            yield ErrorFrame(error=error_message)
