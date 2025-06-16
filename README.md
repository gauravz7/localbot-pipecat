# LocalBot Pipecat

## Overview

This project implements a real-time, voice-controlled chatbot using the [Pipecat](https://github.com/pipecat-ai/pipecat-python) framework. It connects to Google's Gemini Multimodal Live LLM service via Vertex AI, allowing users to interact with the Gemini model through voice using a simple web-based client.

## Features

*   Real-time, bidirectional audio streaming.
*   Integration with Google Vertex AI Gemini Live API.
*   WebSocket communication between backend and frontend.
*   Voice Activity Detection (VAD).
*   Basic function calling support (e.g., ending the call).
*   Configurable via environment variables.
*   Support for capturing and processing video frames from participant's camera and screen via `bot_camera.py`.

## Architecture

The application consists of a Python backend powered by Pipecat and a simple HTML/JavaScript frontend for interaction.

### Backend (`bot.py`)

*   **Framework:** Utilizes the `pipecat-ai` framework for managing the real-time media pipeline.
*   **Transport:** Employs `WebsocketServerTransport` to handle WebSocket connections from the client (default `ws://localhost:8765`), managing audio input/output streams and VAD using `SileroVADAnalyzer`.
*   **LLM Integration:** Leverages the custom `GeminiMultimodalLiveLLMService` (from `gemini_multimodal_live_vertex/gemini.py`) to communicate with the Google Vertex AI Gemini endpoint. It's configured for audio modalities and uses a system prompt for LLM guidance.
*   **Context Management:** Maintains conversation history using an adapted `OpenAILLMContext`.
*   **Asynchronicity:** Built on `asyncio` for efficient handling of concurrent network and AI operations.

### LLM Service (`gemini_multimodal_live_vertex/gemini.py`)

*   **Custom Pipecat Service:** Extends `LLMService` to specifically handle the Gemini Live API.
*   **Vertex AI Connection:** Establishes a secure WebSocket connection to the Vertex AI Gemini Multimodal Live endpoint (`wss://[location]-aiplatform.googleapis.com/ws/...`), which includes specific handling for Vertex AI tool integration.
*   **Authentication:** Authenticates using Google Cloud Application Default Credentials (ADC).
*   **Real-time Streaming:** Manages the bidirectional flow of audio data and control messages (configuration, tool calls) with the Gemini API.

### Frontend (`index.html`)

*   **Interface:** Provides a minimal web interface for user interaction (start/stop audio).
*   **WebSocket Client:** Connects to the backend WebSocket server (`ws://localhost:8765`).
*   **Audio Handling:** Captures microphone input using `navigator.mediaDevices.getUserMedia` and plays back received audio using the Web Audio API. Audio data is exchanged with the backend via Protobuf-encoded messages over WebSocket.

### Video-Enabled Bot (`bot_camera.py`)

*   **Purpose:** Extends the functionality of `bot.py` by enabling video input. This script captures video frames from the participant's camera and/or screen.
*   **Video Capture:** Uses `maybe_capture_participant_camera` and `maybe_capture_participant_screen` from Pipecat to stream video frames at a configurable framerate (default 1fps in the script).
*   **Transport Configuration:** The `DailyParams` and `TransportParams` are configured with `video_in_enabled=True`.
*   **LLM Modality:** While video frames are captured and sent, the `GeminiMultimodalLiveLLMService` in this script is currently configured with `modalities=GeminiMultimodalModalities.AUDIO`. This means the LLM primarily processes audio, but the framework is set up for potential multimodal (audio + video) interactions if the LLM service configuration is updated.
*   **Usage:** Similar to `bot.py`, it uses the Pipecat pipeline for real-time communication.

## Prerequisites

*   Python 3.9+
*   Google Cloud Platform (GCP) account with a project created.
*   Vertex AI API enabled in your GCP project.
*   Google Cloud CLI (`gcloud`) installed and configured locally.
*   Permissions to access Vertex AI endpoints (specifically `aiplatform.endpoints.streamGenerateContent`).

## Setup

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/gauravz7/localbot-pipecat.git
    cd localbot-pipecat
    ```
2.  **Create & Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Authenticate with Google Cloud:**
    Log in using Application Default Credentials:
    ```bash
    gcloud auth application-default login
    ```
5.  **Configure Environment Variables:**
        Copy the example environment file:
        ```bash
        cp .env.example .env
        
        Edit the `.env` file. Here's an example of what it might look like with your specific GCP project details:
        
        GOOGLE_CLOUD_PROJECT=vital-octagon-19612
        GOOGLE_CLOUD_LOCATION=us-central1
        ```
    
# Set this to enable VertexAI integration

    ```bash
        GOOGLE_GENAI_USE_VERTEXAI=True
        PROJECT_ID="vital-octagon-19612"
        #MODEL="gemini-2.0-flash-live-preview-04-09"
        MODEL="gemini-2.0-flash-live-preview-04-09"

        LOCATION="us-central1"
    ```


## Running the Application

Ensure your virtual environment is active before running any bot script.

1.  **Start Audio-Only Bot Server (`bot.py`) (Terminal 1):**
    ```bash
    python bot.py -t webrtc
    ```

2.  **Start Video-Enabled Bot Server (`bot_camera.py`) (Terminal 1):**
    This script enables camera and screen capture in addition to audio.
    ```bash
    python bot_camera.py -t webrtc
    ```

*(Note: You can typically only run one bot server at a time on the default port unless configured otherwise.)*

### Customizing Network Settings for Bot Scripts

To run `bot.py` or `bot_camera.py` on a specific host or port:
```bash
python <script_name.py> --host YOUR_HOST --port YOUR_PORT -t <transport_type>
```
(e.g., `python bot_camera.py --host 0.0.0.0 --port 8766 -t webrtc`)

### Troubleshooting Bot Scripts
*   No audio/video: Check browser permissions for microphone and camera if using WebRTC.
*   Connection errors: Verify API keys and GCP configuration in `.env` file.
*   Missing dependencies: Ensure `pip install -r requirements.txt` was successful.
*   Port conflicts: Use `--port` to change the port for the bot script.

For more examples of running other scripts, see the "Pipecat Foundational Examples" section below.



## Key Files

*   `bot.py`: The main Pipecat application defining the pipeline.
*   `bot_camera.py`: Pipecat application similar to `bot.py` but with added video capture capabilities (camera and screen).
*   `gemini_multimodal_live_vertex/gemini.py`: Custom service for Vertex AI Gemini Live interaction.
*   `index.html`: Web client for audio I/O via WebSockets.
*   `requirements.txt`: Python package dependencies.
*   `frames.proto`: Protobuf definition for WebSocket message serialization.
*   `.env`: Local environment configuration (ignored by Git).
*   `.env.example`: Template for environment variables.
*   `.gitignore`: Specifies files/directories ignored by Git.

## Configuration

Environment variables are managed using a `.env` file (loaded via `python-dotenv`). See `.env.example` for required variables (`PROJECT_ID`, `LOCATION`, `MODEL`). Your actual `.env` file should contain your specific configuration and is excluded from version control by `.gitignore`.
