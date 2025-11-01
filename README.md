Line 3: Adds a brief description of the new feature to the README.

AFTER:
  This project provides real-time transcription capabilities using a WebSocket endpoint.

---

Line 5: Adds a section describing the features of the project.

AFTER:
  ## Features
  
  *   Real-time transcription via WebSocket.

---

Line 7: Adds instructions for installing the dependencies.

AFTER:
  ## Usage
  
  1.  **Install Dependencies:**
      ```bash
      pip install websockets vosk
      ```

---

Line 12: Adds instructions for running the server.

AFTER:
  2.  **Run the Server:**
      ```bash
      python main.py
      ```

---

Line 17: Adds instructions for accessing the example client.

AFTER:
  3.  **Access the Example Client:** Open `example_client.html` in your browser.  Ensure your browser has microphone access enabled.

---

Line 19: Adds detailed documentation for the WebSocket endpoint, including request/response formats and an example client reference.

AFTER:
  ## WebSocket Endpoint
  
  *   **Endpoint:** `ws://localhost:8765` (configurable in `websocket_handler.py`)
  *   **Request:**  Binary audio data (chunks).  Client should send audio data in small chunks (e.g., 100ms).  Send the string "close" to signal the end of the stream.
  *   **Response:** JSON messages with the following types:
      *   `"partial"`:  Contains a partial transcription (`"text"` field).
      *   `"final"`: Contains the final transcription (`"text"` field).
      *   `"error"`:  Contains an error message (`"message"` field).
  
  ## Example Client
  
  See `example_client.html` for a basic JavaScript client implementation.

---
