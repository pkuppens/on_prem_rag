# Chainlit UI for On-Prem RAG Assistant

This guide covers the setup, configuration, and usage of the Chainlit-based chat UI for the On-Prem RAG system.

## Overview

The Chainlit UI provides a production-ready chat interface for interacting with the agent framework. Key features include:

- **Role-Based Access**: GP and Patient roles with appropriate access levels
- **Multi-Agent Visibility**: Real-time display of agent thinking and tool usage
- **File Upload**: Document upload with RAG pipeline integration
- **Authentication**: OAuth2 and password-based authentication
- **On-Premises**: Self-hosted with no cloud dependencies

## Quick Start

### Starting the UI

```bash
# Start the Chainlit UI (default port: 8002)
uv run start-chat

# Or run directly with chainlit
cd src/frontend/chat
chainlit run app.py

# With custom port
CHAINLIT_PORT=8080 uv run start-chat
```

### Demo Users (Development)

For testing without OAuth setup:

| Username | Password | Role |
|----------|----------|------|
| gp | gp123 | General Practitioner |
| patient | patient123 | Patient |
| admin | admin123 | Administrator |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 Chainlit UI                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Chat Panel  │  │ Agent Steps │  │ File     │ │
│  │             │  │   Viewer    │  │ Upload   │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│           Chainlit Backend (app.py)              │
│  - Message handlers                              │
│  - Agent callbacks                               │
│  - Session management                            │
│  - Role routing                                  │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│            Agent Framework                       │
│  - CrewAI agents                                 │
│  - Memory management                             │
│  - NeMo Guardrails                              │
└─────────────────────────────────────────────────┘
```

## File Structure

```
src/frontend/chat/
├── app.py                       # Main Chainlit application
├── chainlit.md                  # Welcome message
├── __init__.py
├── .chainlit/
│   └── config.toml              # Chainlit configuration
├── handlers/
│   ├── __init__.py
│   ├── message_handler.py       # Chat message handling
│   ├── agent_callbacks.py       # CrewAI callbacks
│   └── document_upload.py       # File upload handling
├── auth/
│   ├── __init__.py
│   └── oauth_integration.py     # Auth service integration
├── public/
│   └── custom.css               # Custom styling
└── utils/
    ├── __init__.py
    └── session.py               # Session utilities
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAINLIT_HOST` | 0.0.0.0 | Host to bind to |
| `CHAINLIT_PORT` | 8002 | Port to listen on |
| `AUTH_SERVICE_URL` | http://localhost:8001 | Auth service URL |
| `SHOW_ROLE_ON_START` | true | Show role badge on session start |
| `OAUTH_GOOGLE_ENABLED` | true | Enable Google OAuth |
| `OAUTH_OUTLOOK_ENABLED` | false | Enable Outlook OAuth |

### Chainlit Configuration

The configuration file is located at `src/frontend/chat/.chainlit/config.toml`:

```toml
[project]
name = "On-Prem RAG Assistant"
enable_telemetry = false

[features]
multi_modal = true
speech_to_text = false

[UI]
name = "Medical Document Assistant"
show_readme_as_default = true
hide_cot = false  # Show chain of thought
```

## Authentication

### Role-Aware Authentication

The UI supports role-based access control with three roles:

1. **GP (General Practitioner)**: Clinical analysis, medical entity extraction
2. **Patient**: Health summaries, document queries
3. **Admin**: Full system access

### OAuth Integration

For production, configure OAuth through the auth service:

1. Set up OAuth providers in `src/backend/auth_service/`
2. Configure client IDs and secrets via environment variables
3. The Chainlit UI will use these automatically

### Role Extraction

Roles are extracted from OAuth data in this order:
1. Explicit `role` claim in token
2. `roles` array (prioritizes GP/doctor roles)
3. Group membership
4. Default to `patient`

## File Upload

### Supported Formats

| Format | Extensions | MIME Type |
|--------|------------|-----------|
| PDF | .pdf | application/pdf |
| Word | .docx, .doc | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| Text | .txt | text/plain |
| Markdown | .md | text/markdown |

### File Size Limit

Maximum file size: 10 MB

### Processing Flow

1. File is uploaded through the UI
2. Validation checks file type and size
3. File is processed through the RAG pipeline
4. Document chunks are created for search
5. User is notified of processing results

## Agent Step Visibility

The UI displays agent operations in real-time:

- **Agent Thinking**: Shows reasoning process
- **Tool Usage**: Displays tool invocations and results
- **Task Progress**: Shows step-by-step progress
- **Final Results**: Displays the final response

### Step Types

| Type | Color | Description |
|------|-------|-------------|
| LLM | Purple | LLM/agent processing |
| Tool | Green | Tool invocations |
| Run | Orange | Overall task execution |

## Customization

### Custom Styling

Edit `src/frontend/chat/public/custom.css` for custom styling:

```css
/* Role Badge Colors */
.role-badge-gp { background-color: #1976d2; }
.role-badge-patient { background-color: #388e3c; }
.role-badge-admin { background-color: #d32f2f; }
```

### Welcome Message

Edit `src/frontend/chat/chainlit.md` to customize the welcome message.

### Chat Profiles

Chat profiles are defined in `app.py` and vary by role:

- **General Assistant**: Available to all users
- **Clinical Analysis**: GP and Admin only
- **Document Summary**: GP and Admin only
- **System Admin**: Admin only

## Deployment

### Development

```bash
# Run with hot reload
chainlit run src/frontend/chat/app.py -w
```

### Production

```bash
# Run with production settings
CHAINLIT_HOST=0.0.0.0 CHAINLIT_PORT=8002 uv run start-chat
```

### Docker

The Chainlit UI can be containerized:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8002
CMD ["uv", "run", "start-chat"]
```

### Separate Endpoints per Role (Optional)

For maximum isolation, run separate instances:

```bash
# GP instance
CHAINLIT_PORT=8002 ROLE_FILTER=gp uv run start-chat

# Patient instance
CHAINLIT_PORT=8003 ROLE_FILTER=patient uv run start-chat
```

## Troubleshooting

### Common Issues

**"Session not found" error**
- Ensure cookies are enabled
- Try refreshing the page
- Clear browser cache and re-login

**Agent framework not responding**
- Check if backend services are running: `uv run start-backend`
- Verify auth service is running: `uv run start-auth`
- Check logs for connection errors

**File upload fails**
- Verify file type is supported
- Check file size is under 10 MB
- Ensure RAG pipeline is configured

**OAuth login fails**
- Verify OAuth provider configuration
- Check redirect URIs match
- Review auth service logs

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Access the UI at `http://localhost:8002` to verify it's running.

## API Integration

The Chainlit UI integrates with:

1. **Auth Service** (`/me`, `/oauth/*`): Authentication
2. **RAG Pipeline**: Document processing and search
3. **Agent Framework**: CrewAI orchestrator
4. **Guardrails**: NeMo input/output validation

## Security Considerations

1. **On-Premises**: All processing occurs locally
2. **No Telemetry**: Chainlit telemetry is disabled
3. **Role Isolation**: Users only access their role's features
4. **Session Management**: Sessions expire appropriately
5. **Input Validation**: NeMo Guardrails validate all inputs
