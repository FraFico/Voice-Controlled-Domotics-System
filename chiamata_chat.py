"""
Chiamata al modello OpenAI per la domotica.

Riceve il comando dell'utente + le istruzioni (costruite da sistema.py) e
restituisce l'intent come dizionario Python. Qui si concentrano i due pezzi
chiave: 'messages' (sistema + utente) e 'response' (parsata in JSON -> dict).

Uso da riga di comando (prova rapida, senza casa reale):
    python chiamata_chat.py "accendi la luce del salotto"
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Le credenziali OpenAI stanno nel .env di questa lezione (stesse di chatbot.py).
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

ai_key = os.getenv("AI_KEY")
ai_endpoint = os.getenv("AI_ENDPOINT")
ai_model = os.getenv("AI_MODEL")

client = OpenAI(api_key=ai_key, base_url=ai_endpoint)


def _estrai_json(testo):
    """L'LLM a volte incornicia il JSON tra ```; lo ripuliamo e prendiamo
    il primo oggetto { ... } che troviamo."""
    testo = testo.strip()
    if testo.startswith("```"):
        testo = testo.strip("`")
        # toglie un eventuale prefisso tipo 'json\n'
        if "\n" in testo:
            testo = testo.split("\n", 1)[1]
    inizio = testo.find("{")
    fine = testo.rfind("}")
    if inizio != -1 and fine != -1:
        testo = testo[inizio:fine + 1]
    return json.loads(testo)


def interpreta_comando(testo, istruzioni):
    """Chiede al modello di interpretare il comando dell'utente.
    Restituisce l'intent (dict). Su qualsiasi errore -> intent 'non fattibile'."""
    try:
        response = client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": istruzioni},
                {"role": "user", "content": testo},
            ],
        )
        contenuto = response.choices[0].message.content
        return _estrai_json(contenuto)
    except Exception as errore:
        # Niente crash: l'orchestratore puo' decidere un fallback alle regole.
        return {"device": None, "proprieta": None, "valore": None,
                "fattibile": False,
                "risposta": "Non sono riuscito a interpretare il comando.",
                "errore": str(errore)}


if __name__ == "__main__":
    # Prova rapida: serve solo per vedere il JSON grezzo del modello.
    from sistema import SistemaDomotica, costruisci_casa

    comando = " ".join(sys.argv[1:]) or "accendi la luce del salotto"
    istruzioni = SistemaDomotica(costruisci_casa()).istruzioni_per_modello()
    print(interpreta_comando(comando, istruzioni))
