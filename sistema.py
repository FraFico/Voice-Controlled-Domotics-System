"""
Domotica virtuale - il sistema (il "cervello" + le "mani").

Lavora SOLO con testo:
    testo del comando  ->  intent (dict)  ->  esegui  ->  testo della risposta

L'intent ha una forma comune, prodotta sia dalle regole (offline) sia dall'LLM:
    {"azione": "imposta"|"stato",
     "device": "luce salotto"|None,
     "proprieta": "acceso|aperto|temperatura"|None,
     "valore": True|False|<numero>,
     "fattibile": True|False,
     "risposta": "<frase in italiano>"|None}

- azione "imposta": cambia una proprieta' del device (accendi/apri/temperatura).
- azione "stato": chiede lo stato; device=None -> tutta la casa, altrimenti un device.
  Lo stato e' letto SEMPRE dalla casa (verita' viva), mai dalla frase del modello.

Cosi' e' indipendente dall'interfaccia: lo usano sia la tastiera sia la voce.
"""

from classi import Device, Stanza, Casa


# Per ogni tipo di device, qual e' la proprieta' di stato che si controlla.
# luce/tv -> acceso (on/off); porta/finestra -> aperto (on/off); termostato -> temperatura.
PROPRIETA_PER_TIPO = {
    "luce": "acceso",
    "tv": "acceso",
    "porta": "aperto",
    "finestra": "aperto",
    "termostato": "temperatura",
}


def costruisci_casa():
    """Costruisce una casa di esempio con qualche stanza e device."""
    casa = Casa("Casa di Gruppo 1")
    salotto = casa.add_stanza(Stanza("salotto"))
    camera = casa.add_stanza(Stanza("camera"))
    ingresso = casa.add_stanza(Stanza("ingresso"))
    cucina = casa.add_stanza(Stanza("cucina"))

    salotto.add_device(Device("luce salotto", "luce", {"acceso": False}))
    salotto.add_device(Device("tv", "tv", {"acceso": False, "canale": 1}))
    salotto.add_device(Device("finestra salotto", "finestra", {"aperto": False}))
    salotto.add_device(Device("porta salotto", "porta", {"aperto": False}))

    camera.add_device(Device("luce camera", "luce", {"acceso": False}))
    camera.add_device(Device("termostato", "termostato", {"temperatura": 19}))
    camera.add_device(Device("finestra camera", "finestra", {"aperto": False}))
    camera.add_device(Device("porta camera", "porta", {"aperto": False}))

    cucina.add_device(Device("luce cucina", "luce", {"acceso": False}))
    cucina.add_device(Device("termostato cucina", "termostato", {"temperatura": 19}))
    cucina.add_device(Device("finestra cucina", "finestra", {"aperto": False}))
    cucina.add_device(Device("porta cucina", "porta", {"aperto": False}))

    ingresso.add_device(Device("porta ingresso", "porta", {"aperto": False}))
    ingresso.add_device(Device("luce ingresso", "luce", {"acceso": False}))

    return casa


class SistemaDomotica:
    """Tiene UNA casa (la verita' sullo stato) e traduce i comandi in azioni."""

    # parole chiave -> azione (booleana). Usato solo dall'interprete a regole,
    # che fa da fallback offline quando l'LLM non e' disponibile.
    PAROLE_ON = ("accendi", "accendere", "attiva", "apri", "aprire", "on")
    PAROLE_OFF = ("spegni", "spegnere", "disattiva", "chiudi", "chiudere", "off")
    PAROLE_STATO = ("stato", "com'è", "com'e", "come sta", "come stanno",
                    "come va", "dimmi", "mostrami", "mostra")

    def __init__(self, casa):
        self.casa = casa

    # --- istruzioni per il modello (il system prompt) -------------------
    def istruzioni_per_modello(self):
        """Descrive la casa e impone all'LLM di rispondere SOLO con un JSON.
        Queste sono le 'istruzioni definite in sistema.py'."""
        righe = []
        for stanza in self.casa.get_room().values():
            for device in stanza.get_device().values():
                proprieta = PROPRIETA_PER_TIPO.get(device.tipo, "?")
                righe.append(
                    f'- "{device.nome}" (stanza: {stanza.nome}, tipo: {device.tipo}, '
                    f"proprieta: {proprieta}, stato: {device.get_state()})"
                )
        elenco = "\n".join(righe)

        return (
            "Sei l'assistente di una casa domotica. Interpreti il comando "
            "dell'utente e lo trasformi in UNA sola azione.\n\n"
            "Dispositivi disponibili:\n"
            f"{elenco}\n\n"
            "Puoi fare due tipi di azione:\n"
            "- \"imposta\": cambia una proprieta' di UN dispositivo "
            "(accendi/spegni, apri/chiudi, imposta la temperatura).\n"
            "- \"stato\": l'utente chiede lo stato. Per un singolo dispositivo metti "
            "il suo nome in 'device'; per TUTTA la casa metti 'device': null. "
            "In questo caso 'proprieta' e 'valore' restano null.\n\n"
            "Regole:\n"
            "- 'acceso' e 'aperto' sono booleani (true/false). 'temperatura' e' un numero.\n"
            "- Usa ESATTAMENTE il nome del dispositivo come scritto sopra.\n"
            "- Se il comando non e' eseguibile (dispositivo inesistente, azione "
            "impossibile), metti \"fattibile\": false e spiega in 'risposta'.\n\n"
            "Rispondi SOLO con un oggetto JSON, senza testo extra, in questa forma:\n"
            '{"azione": "imposta|stato", "device": "<nome esatto o null>", '
            '"proprieta": "acceso|aperto|temperatura|null", '
            '"valore": <true|false|numero|null>, "fattibile": <true|false>, '
            '"risposta": "<breve frase in italiano da dire all\'utente>"}'
        )

    # --- CERVELLO (fallback a regole): testo -> intent ------------------
    def interpreta(self, testo):
        """Interprete offline a parole chiave. Produce la forma-intent comune.
        Usato come fallback quando l'LLM non e' raggiungibile."""
        t = testo.lower()

        # richiesta di stato: un device specifico se nominato, altrimenti tutta la casa
        if any(parola in t for parola in self.PAROLE_STATO):
            _, device = self._trova_device(t)
            return {"azione": "stato", "device": device.nome if device else None,
                    "proprieta": None, "valore": None, "fattibile": True, "risposta": None}

        if any(parola in t for parola in self.PAROLE_ON):
            valore = True
        elif any(parola in t for parola in self.PAROLE_OFF):
            valore = False
        else:
            return {"azione": "imposta", "device": None, "proprieta": None, "valore": None,
                    "fattibile": False, "risposta": "Non ho capito il comando."}

        _, device = self._trova_device(t)
        if device is None:
            return {"azione": "imposta", "device": None, "proprieta": None, "valore": None,
                    "fattibile": False, "risposta": "Non ho capito quale dispositivo intendi."}

        proprieta = PROPRIETA_PER_TIPO.get(device.tipo)
        verbo = "Ho acceso" if valore else "Ho spento"
        if proprieta == "aperto":
            verbo = "Ho aperto" if valore else "Ho chiuso"
        return {"azione": "imposta", "device": device.nome, "proprieta": proprieta,
                "valore": valore, "fattibile": True, "risposta": f"{verbo} {device.nome}."}

    # --- MANI: intent -> azione sulla casa + risposta testuale ----------
    def esegui(self, intent):
        """Applica l'intent alla casa e restituisce la frase da dire all'utente.
        Il codice e' il garante: valida la fattibilita' prima di toccare lo stato."""
        risposta = intent.get("risposta")

        # 1) il modello (o le regole) hanno gia' detto che non si puo' fare
        if not intent.get("fattibile"):
            return risposta or "Mi dispiace, non posso eseguire questo comando."

        # 2) richiesta di stato: lo leggo dalla casa (verita' viva), non dal modello
        if intent.get("azione") == "stato":
            return self._riferisci_stato(intent.get("device"))

        # 3) il dispositivo deve esistere davvero
        nome = intent.get("device")
        _, device = self.casa.find_device(nome) if nome else (None, None)
        if device is None:
            return f"Non trovo il dispositivo '{nome}' in casa."

        # 4) la proprieta' deve essere quella giusta per quel tipo di device
        proprieta = intent.get("proprieta")
        if proprieta != PROPRIETA_PER_TIPO.get(device.tipo):
            return f"Non posso fare questo su {device.nome}."

        # 5) tutto ok: aggiorno lo stato della casa e confermo
        device.set_state(proprieta, intent.get("valore"))
        return risposta or f"Fatto: {device.nome} -> {device.get_state()}."

    # --- comodita': testo del comando -> testo della risposta (solo regole)
    def processa(self, testo):
        return self.esegui(self.interpreta(testo))

    # --- stato leggibile (per la voce) ----------------------------------
    def _riferisci_stato(self, nome=None):
        """Frase sullo stato: di un singolo device se 'nome' e' dato, altrimenti
        di tutta la casa. Legge sempre lo stato corrente degli oggetti."""
        if nome:
            _, device = self.casa.find_device(nome)
            if device is None:
                return f"Non trovo il dispositivo '{nome}' in casa."
            return self._descrivi_device(device).capitalize() + "."

        descrizioni = [self._descrivi_device(device)
                       for stanza in self.casa.get_room().values()
                       for device in stanza.get_device().values()]
        if not descrizioni:
            return "In casa non c'e' nessun dispositivo."
        return "Ecco lo stato della casa: " + "; ".join(descrizioni) + "."

    def _descrivi_device(self, device):
        """Descrizione naturale di un device (i nomi sono tutti femminili: luce,
        tv, finestra, porta -> accesa/spenta, aperta/chiusa)."""
        proprieta = PROPRIETA_PER_TIPO.get(device.tipo)
        stato = device.get_state()
        if proprieta == "acceso":
            return f"{device.nome} {'accesa' if stato.get('acceso') else 'spenta'}"
        if proprieta == "aperto":
            return f"{device.nome} {'aperta' if stato.get('aperto') else 'chiusa'}"
        if proprieta == "temperatura":
            return f"{device.nome} a {stato.get('temperatura')} gradi"
        return f"{device.nome}: {stato}"

    # --- aiutante: trova il device piu' probabile dal testo -------------
    def _trova_device(self, testo):
        """Sceglie il device il cui nome ha piu' parole in comune col testo.
        Es. 'accendi la luce del salotto' -> 'luce salotto' (2 parole)."""
        migliore = (None, None)
        punteggio_max = 0
        for stanza in self.casa.get_room().values():
            for device in stanza.get_device().values():
                parole = device.nome.lower().split()
                punteggio = sum(1 for parola in parole if parola in testo)
                if punteggio > punteggio_max:
                    punteggio_max = punteggio
                    migliore = (stanza, device)
        return migliore
