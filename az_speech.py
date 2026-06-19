import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk


def configura():
    """Crea la config di Azure Speech (lingua it-IT, voce Isabella) e la rende
    disponibile a speech_to_text/text_to_speech. Va chiamata una volta all'avvio,
    sia dalla demo qui sotto sia dall'app di domotica."""
    load_dotenv(Path(__file__).resolve().parent / ".env")
    key = os.getenv("AZ_SPEECH_KEY")
    region = os.getenv("AZ_SPEECH_REGION")

    global config   # una sola config condivisa da tutte le funzioni
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = os.getenv("AZ_SPEECH_LANGUAGE") or "it-IT"
    config.speech_synthesis_voice_name = os.getenv("AZ_SPEECH_VOICE") or "it-IT-IsabellaNeural"
    return config


def speech_to_text():
    # config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)
    
    print("Sto ascoltando...       ") # "parla pure"
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text, result.duration
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("Nessun discorso riconosciuto.")
        return "", 0   # tupla coerente: 'testo, _ = speech_to_text()' non rompe
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Cancellato: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Errore: {cancellation_details.error_details}")
        raise RuntimeError(f"Errore durante il riconoscimento vocale.  {cancellation_details.error_details}")
    
    
def text_to_speech(text):
    # use_default_speaker=True riproduce direttamente dall'altoparlante:
    # niente file da scrivere/flushare, niente afplay.
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthetizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=audio_config)

    result = synthetizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return "done"
    elif result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        print(f"Sintesi annullata: {details.reason} - {details.error_details}")
        return "fail"
    else:
        return "fail"
    

def main():
    configura()

    testo, durata = speech_to_text()
    
    
    
    print(f"Ho capito: ({durata} ticks): {testo}") # 1 ticks = 100 nanosecondi
    #TODO: implimentare una logica utile
    text_to_speech(f"Hai detto: {testo}? ")


if __name__ == "__main__":
    main()
    