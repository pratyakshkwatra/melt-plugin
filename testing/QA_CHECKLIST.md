# Backend QA & Testing Automation Framework

## 1. Automated Testing

### Backend (Python/OctoPrint Plugin)
*   **Unit Testing (PyTest)**: 
    *   Test standard API endpoints for correct HTTP status codes and responses.
    *   Test internal event hooks (e.g., `on_event`, `on_after_startup`).
*   **WebSocket Payload Testing**:
    *   Mock the OctoPrint printer state (using the Virtual Printer).
    *   Assert that the plugin broadcasts the correct JSON payloads (temperatures, print progress, ETA) over the WebSocket connection.
*   **Plugin Integration Tests**:
    *   Validate communication with third-party plugins (`BedLevelVisualizer`, `PrintTimeGenius`, etc.).
