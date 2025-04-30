# LocalBot Pipecat

This project implements a real-time voice bot using the [Pipecat](https://github.com/pipecat-ai/pipecat-python) framework, connecting to Google's Gemini Multimodal Live LLM service via Vertex AI. It allows users to interact with the Gemini model through voice using a simple web-based client.

## Architecture

The application consists of a Python backend powered by Pipecat and a simple HTML/JavaScript frontend for interaction.

**1. Backend (`bot.py`)**

*   **Framework:** Built using the `pipecat-ai` framework for managing real-time media pipelines.
*   **Transport:** Uses `WebsocketServerTransport` to establish a WebSocket connection with the client (`ws://localhost:8765` by default). It handles audio input/output and uses `SileroVADAnalyzer` for Voice Activity Detection.
*   **LLM Integration:** Integrates the custom `GeminiMultimodalLiveLLMService` (defined in `gemini_multimodal_live_vertex/gemini.py`) to connect to the Google Vertex AI Gemini endpoint.
    *   Configured for audio input/output (`modalities=GeminiMultimodalModalities.AUDIO`).
    *   Uses a system prompt to instruct the LLM on its role and behavior (e.g., how to handle call termination).
    *   Supports function calling/tools (e.g., an `end_call` tool is registered).
*   **Context Management:** Uses `OpenAILLMContext` (adapted for Gemini) to maintain the conversation history.
*   **Asynchronous Operations:** Leverages `asyncio` for handling concurrent operations like WebSocket communication and LLM interaction.
*   **Dependencies:** Relies on libraries listed in `requirements.txt`, including `pipecat-ai`, `google-cloud-*`, `websockets`, `loguru`, etc.

**2. Gemini LLM Service (`gemini_multimodal_live_vertex/gemini.py`)**

*   **Custom Pipecat Service:** Extends `pipecat.services.ai_services.LLMService`.
*   **Vertex AI Connection:** Connects securely to the Vertex AI Gemini Multimodal Live endpoint (`wss://us-central1-aiplatform.googleapis.com/ws/...`) using WebSockets.
*   **Authentication:** Uses Google Cloud Application Default Credentials (ADC) to authenticate requests.
*   **Real-time Communication:** Handles bidirectional streaming of audio data and control messages (configuration, tool calls, etc.) with the Gemini API.
*   **Context Adaptation:** Adapts the `OpenAILLMContext` structure for compatibility with the Gemini API's expected format.
*   **Audio Processing:** Manages sending user audio and receiving model audio. Includes optional integration with a transcriber (`AudioTranscriber`).

**3. Frontend (`index.html`)**

*   **Interface:** A basic HTML page with JavaScript for testing the bot.
*   **WebSocket Client:** Connects to the backend WebSocket server (`ws://localhost:8765`).
*   **Microphone Access:** Uses `navigator.mediaDevices.getUserMedia` to capture audio from the user's microphone.
*   **Audio Encoding/Decoding:**
    *   Sends microphone audio (converted to 16-bit PCM) to the backend, packaged using Protobuf (`frames.proto`).
    *   Receives audio chunks from the backend (also Protobuf encoded).
    *   Uses the Web Audio API (`AudioContext`, `AudioBufferSourceNode`) to decode and play the received audio in real-time.

**4. Configuration & Serialization**

*   **`.env`:** Stores sensitive configuration like Google Cloud `PROJECT_ID`, the Gemini `MODEL` name, and the deployment `LOCATION`. **This file should not be committed to version control.**
*   **`requirements.txt`:** Lists all necessary Python packages and their versions.
*   **`frames.proto`:** Defines the Protocol Buffers message structure used for WebSocket communication between the frontend and backend, ensuring consistent data format.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/gauravz7/localbot-pipecat.git
    cd localbot-pipecat
    ```
2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows use `venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Google Cloud Authentication:**
    *   Ensure you have the Google Cloud CLI (`gcloud`) installed and configured.
    *   Authenticate using Application Default Credentials:
        ```bash
        gcloud auth application-default login
        ```
    *   Make sure the authenticated user/service account has the necessary permissions to access Vertex AI (specifically the `aiplatform.endpoints.streamGenerateContent` permission for the Gemini endpoint).
5.  **Create `.env` File:**
    Create a file named `.env` in the project root and add the following variables, replacing the placeholders with your actual values:
    ```dotenv
    PROJECT_ID="your-gcp-project-id"
    LOCATION="us-central1" # Or your preferred GCP region supporting the model
    MODEL="gemini-1.5-flash-001" # Or another compatible Gemini model
    ```

## Running the Application

1.  **Start the Backend Server:**
    Make sure your virtual environment is active.
    ```bash
    python bot.py
    ```
    You should see log output indicating the server is running and waiting for connections on `localhost:8765`.

2.  **Open the Frontend:**
    Open the `index.html` file in your web browser (e.g., by double-clicking it or using `File > Open` in your browser).

3.  **Interact:**
    *   The page will initially show "Loading, wait..." while Protobuf definitions load.
    *   Once it shows "We are ready!", click the "Start Audio" button.
    *   Your browser will likely ask for permission to access your microphone. Allow it.
    *   The WebSocket connection will be established, and you can start speaking to the Gemini bot.
    *   The bot's audio responses will be played back through your speakers/headphones.
    *   Click "Stop Audio" to disconnect the microphone and close the WebSocket connection.

## Key Files

*   `bot.py`: Main Pipecat application orchestrating the pipeline.
*   `gemini_multimodal_live_vertex/gemini.py`: Custom Pipecat service for interacting with the Vertex AI Gemini Live API.
*   `index.html`: Simple web client for microphone input and audio output via WebSocket.
*   `requirements.txt`: Lists Python dependencies.
*   `.env`: Stores environment variables (GCP Project ID, Model, Location). **(Not version controlled)**
*   `frames.proto`: Protobuf definition for WebSocket message frames.
*   `.gitignore`: Specifies intentionally untracked files (like `venv/`, `.env`, `__pycache__/`).
