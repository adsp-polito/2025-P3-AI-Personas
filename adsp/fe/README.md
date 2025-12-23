# Lavazza AI Personas Frontend

A Streamlit-based frontend for the Lavazza AI Personas application.

## Features

- **Authentication**: User login and registration with token-based authentication
- **Multiple Personas**: Select and chat with different AI personas
- **Multiple Chat Sessions**: Maintain multiple concurrent chat sessions
- **RAG Context Display**: View retrieved context and citations used for responses
- **Session Management**: Create, switch between, and delete chat sessions
- **Responsive UI**: Clean and intuitive interface with custom styling

## Running the Frontend

1. **Start the backend API server** (in a separate terminal):
   ```bash
   python scripts/run_api.py
   ```

2. **Start the Streamlit frontend**:
   ```bash
   python scripts/run_frontend.py
   ```

3. **Access the application**:
   - Open your browser to `http://localhost:8501`
   - Register a new user or login with existing credentials
   - Select a persona from the sidebar
   - Start chatting

## Usage

### Authentication

1. **Register**: Create a new account with a username and token
2. **Login**: Enter your credentials to access the chat interface

### Chatting with Personas

1. **Select Persona**: Click on a persona in the sidebar to start a new chat
2. **Send Messages**: Type your message and click "Send"
3. **View Context**: Enable "Show retrieved context" in settings to see RAG data
4. **Multiple Sessions**: Switch between different chat sessions in the sidebar

### Chat Settings

- **Show retrieved context**: Display the RAG context and citations
- **Number of context documents (top-k)**: Control how many documents are retrieved (1-20)

## Features in Detail

### Multiple Chat Sessions

- Create multiple chat sessions with the same or different personas
- Switch between sessions without losing conversation history
- Delete sessions when no longer needed

### RAG Context Display

When enabled, each assistant response shows:
- **Retrieved Context**: The text chunks used to generate the response
- **Citations**: Metadata about the sources (persona, domain, category, pages, indicators)

### Session Management

- Each session has a unique ID
- Sessions persist during your browser session
- Clear chat history without deleting the session
- View message count for each session

## Troubleshooting

### Cannot connect to API server

- Ensure the backend API is running
- Check the API URL in the configuration (default: `http://localhost:8000`)

### Authentication fails

- Ensure you've registered your user first
- Check that the token matches exactly (case-sensitive)
- Verify the API server is accepting authentication requests

### No personas available

- Ensure personas are loaded in the backend
- Check the logs for any errors in the API server
- Verify the persona registry is properly initialized

## Development

To modify the frontend:

1. Edit the relevant component files in `adsp/fe/components/`
2. The app will auto-reload when you save changes (Streamlit feature)
3. Check the browser console and terminal for any errors