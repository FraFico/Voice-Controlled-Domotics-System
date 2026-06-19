# Voice-Controlled Home Automation 🏠🎤

Built with Azure Speech Services and OpenAI for natural language smart home control.

> ⚠️ **Important Notice**
>
> This project requires:
>
> - **Azure Speech Services** for speech-to-text and text-to-speech functionality.
> - **OpenAI or Azure OpenAI** for natural language understanding and command interpretation.
>
> These services are **mandatory**. The application will not function correctly without valid credentials configured in the `.env` file.

A voice-controlled smart home assistant: the user speaks, an **OpenAI** model interprets the request, the action is executed on a virtual home (lights, TV, windows, doors, thermostat), and the assistant confirms the result using **Isabella**, an Azure Speech voice. If the requested action cannot be performed, the assistant provides feedback.

## How It Works

```text
   voice ──► az_speech (speech-to-text)
                │  text
                ▼
        chiamata_chat ──► OpenAI interprets the command (JSON)
                │  intent
                ▼
           sistema ──► executes the action on the virtual home
                │  response
                ▼
        az_speech (text-to-speech, Isabella voice) ──► voice
```

## Files

| File | Purpose |
|------|---------|
| `classi.py` | Data model: `Device`, `Room`, `House` |
| `sistema.py` | Core logic: builds the house, generates model instructions, and executes actions |
| `chiamata_chat.py` | OpenAI API interaction (command → JSON) |
| `az_speech.py` | Voice interface: speech-to-text and text-to-speech using Azure Speech |
| `main.py` | Application entry point (main loop) |

## Setup

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Copy the example configuration file and fill in your credentials
cp .env.example .env
```

The application requires **Azure Speech** credentials (`AZ_SPEECH_*`) and **OpenAI / Azure OpenAI** credentials (`AI_KEY`, `AI_ENDPOINT`, `AI_MODEL`).

The `.env` file is ignored by Git, ensuring that real credentials are never committed to the repository.

## Run

From the project directory:

```bash
python main.py                  # Voice mode (microphone required)
MODO_VOCE=False python main.py  # Text mode (keyboard only)
```

## Example Commands

- "turn on the living room light"
- "open the bedroom window"
- "close the door"
- "I'm cold in the bedroom" → increases the thermostat temperature
- "what is the status of the house?" → lists the status of all devices
- "exit" → closes the application
