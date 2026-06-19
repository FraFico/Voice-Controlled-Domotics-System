"""
Domotica vocale - punto di ingresso (orchestratore).

Flusso:
    l'utente parla  ->  il modello OpenAI interpreta (chiamata_chat)
    ->  il sistema esegue l'azione sulla casa (sistema.esegui)
    ->  la casa risponde a voce con Isabella (az_speech.text_to_speech)

Modalita':
    - voce  (default): microfono + voce Isabella
    - testo (MODO_VOCE=False): tastiera + stampa, comodo per provare senza microfono
L'interpretazione e' sempre affidata all'LLM; se la chiamata fallisce
(credenziali assenti, rete giu'), si ricade automaticamente sulle regole.
"""

import os
import string

import az_speech
import chiamata_chat
from sistema import SistemaDomotica, costruisci_casa

# "1/true/si" -> voce; qualunque altra cosa -> testo. Default: voce.
MODO_VOCE = os.getenv("MODO_VOCE", "true").lower() in ("1", "true", "si", "sì", "yes")

USCITA = ("esci", "exit", "quit", "stop", "basta")


# ---------------------------------------------------------------------------
# I/O: cambia solo in base alla modalita'. Il resto del programma e' identico.
# ---------------------------------------------------------------------------
def ascolta():
    """Riceve un comando dall'utente (voce o tastiera)."""
    if MODO_VOCE:
        testo, _ = az_speech.speech_to_text()
        return testo
    return input("Tu> ")


def rispondi(testo):
    """Comunica una risposta all'utente (sempre a schermo; a voce se MODO_VOCE)."""
    print(f"Casa> {testo}")
    if MODO_VOCE:
        az_speech.text_to_speech(testo)


def capisci(testo, sistema, istruzioni):
    """LLM come interprete principale; regole come rete di sicurezza."""
    intent = chiamata_chat.interpreta_comando(testo, istruzioni)
    if intent.get("errore"):              # l'LLM non era raggiungibile
        return sistema.interpreta(testo)
    return intent


def main():
    if MODO_VOCE:
        az_speech.configura()             # config Azure Speech + voce Isabella

    sistema = SistemaDomotica(costruisci_casa())
    istruzioni = sistema.istruzioni_per_modello()

    rispondi("Domotica pronta. Dimmi cosa fare, ad esempio 'accendi la luce del salotto'. Per uscire di' 'esci'.")

    while True:
        comando = ascolta()
        if not comando.strip():
            continue
        # la voce restituisce es. "Esci." con maiuscola e punto: ripulisco
        # punteggiatura e maiuscole prima di confrontare con le parole d'uscita
        if comando.strip().lower().strip(string.punctuation + " ") in USCITA:
            rispondi("A presto!")
            break
        intent = capisci(comando, sistema, istruzioni)
        rispondi(sistema.esegui(intent))


if __name__ == "__main__":
    main()
