# Domotica vocale 🏠🎤

Assistente domestico a comando vocale: parli, un modello **OpenAI** interpreta
la richiesta, l'azione viene eseguita sulla casa virtuale (luci, TV, finestre,
porte, termostato) e l'assistente conferma a voce con la voce **Isabella**
(Azure Speech). Se l'azione non è possibile, ti avvisa.

## Come funziona

```
   voce ──► az_speech (speech-to-text)
                │  testo
                ▼
        chiamata_chat ──► il modello OpenAI interpreta (JSON)
                │  intent
                ▼
           sistema ──► esegue l'azione sulla casa
                │  risposta
                ▼
        az_speech (text-to-speech, voce Isabella) ──► voce
```

## File

| File | Ruolo |
|------|-------|
| `classi.py` | Modello dati: `Device`, `Stanza`, `Casa` |
| `sistema.py` | Logica: costruisce la casa, istruzioni per il modello, esegue le azioni |
| `chiamata_chat.py` | Chiamata al modello OpenAI (comando → JSON) |
| `az_speech.py` | Voce: speech-to-text e text-to-speech (Azure) |
| `main.py` | Punto di ingresso (il loop) |

## Setup

```bash
# 1) dipendenze
pip install -r requirements.txt

# 2) credenziali: copia l'esempio e riempi i valori
cp .env.example .env
```

Servono le credenziali **Azure Speech** (`AZ_SPEECH_*`) e **OpenAI / Azure AI**
(`AI_KEY`, `AI_ENDPOINT`, `AI_MODEL`). Il file `.env` è ignorato da git: le
credenziali reali non finiscono mai nel repository.

## Avvio

Dalla cartella `domotica/`:

```bash
python main.py                  # modalità voce (richiede il microfono)
MODO_VOCE=False python main.py  # modalità testo (tastiera, senza microfono)
```

## Esempi di comandi

- "accendi la luce del salotto"
- "apri la finestra della camera"
- "chiudi la porta"
- "ho freddo in camera"  → alza il termostato
- "che stato ha la casa?" → elenca lo stato di tutti i dispositivi
- "esci" → termina
