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
    ```
    Edit the `.env` file and replace the placeholder values with your specific GCP project details:
    ```dotenv
    PROJECT_ID="your-gcp-project-id"
    LOCATION="us-central1" # Or your GCP region
    MODEL="gemini-1.5-flash-001" # Or compatible model
    # Optional: GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
    ```

## Running the Application

1.  **Start Backend Server (Terminal 1):**
    Ensure your virtual environment is active.
    ```bash
    python bot.py
    ```
    The server will start listening on `localhost:8765`.

2.  **Serve Frontend (Terminal 2):**
    In a *separate terminal*, navigate to the project directory and run Python's built-in HTTP server:
    ```bash
    python -m http.server 8000
    ```
    *(Use `python -m SimpleHTTPServer 8000` for Python 2)*

3.  **Access Frontend:**
    Open your web browser and go to `http://localhost:8000`.

4.  **Interact:**
    *   Wait for "We are ready!".
    *   Click "Start Audio". Allow microphone access if prompted.
    *   Speak to interact with the Gemini bot. Audio responses will be played back.
    *   Click "Stop Audio" to end the session.

## Pipecat Foundational Examples
This directory contains examples showing how to build voice and multimodal agents with Pipecat. Each example demonstrates specific features, progressing from basic to advanced concepts.

### Learning Paths
Depending on what you're trying to build, these learning paths will guide you through relevant examples:

*   New to Pipecat: Start with examples 01, 02, 07
*   Building conversational bots: 07, 10, 38
*   Common add-on capabilities: 17, 24, 28, 34
*   Adding visual capabilities: 03, 12, 26
*   Advanced agent capabilities: 14, 20, 37

### Quick Start
Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Create a .env file with your API keys.

Run any example:
```bash
python 01-say-one-thing.py
```
Open the web interface at http://localhost:7860 and click "Connect"

### Running examples with other transports
It is possible to run most of the examples with other transports such as Twilio or webrtc. 

```bash
python 07-interruptible.py -t daily
```

### Twilio
It is also possible to run the example through a Twilio phone number. You will need to setup a few things:

1.  Install and run ngrok.
    ```bash
    ngrok http 7860
    ```
2.  Configure your Twilio phone number. One way is to setup a TwiML app and set the request URL to the ngrok URL from step (1). Then, set your phone number to use the new TwiML app.
Then, run the example with:
```bash
python 07-interruptible.py -t twilio -x NGROK_HOST_NAME (no protocol)
```

### Examples by Feature
(This part seems to be missing from the provided text, if there's a list of examples by feature, it would go here)

### Advanced Usage
Customizing Network Settings
```bash
python <example-name> --host 0.0.0.0 --port 8080
```

### Troubleshooting
*   No audio/video: Check browser permissions for microphone and camera
*   Connection errors: Verify API keys in .env file
*   Missing dependencies: Run pip install -r requirements.txt
*   Port conflicts: Use --port to change the port

For more examples, visit our GitHub repository.

## Key Files

*   `bot.py`: The main Pipecat application defining the pipeline.
*   `gemini_multimodal_live_vertex/gemini.py`: Custom service for Vertex AI Gemini Live interaction.
*   `index.html`: Web client for audio I/O via WebSockets.
*   `requirements.txt`: Python package dependencies.
*   `frames.proto`: Protobuf definition for WebSocket message serialization.
*   `.env`: Local environment configuration (ignored by Git).
*   `.env.example`: Template for environment variables.
*   `.gitignore`: Specifies files/directories ignored by Git.

## Configuration

Environment variables are managed using a `.env` file (loaded via `python-dotenv`). See `.env.example` for required variables (`PROJECT_ID`, `LOCATION`, `MODEL`). Your actual `.env` file should contain your specific configuration and is excluded from version control by `.gitignore`.
