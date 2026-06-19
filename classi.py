"""
Domotica virtuale - modello dati della casa.

Tre classi semplici (KISS), senza I/O:
    - Device : un singolo dispositivo (luce, termostato, ...) con il suo stato
    - Stanza : contiene piu' device
    - Casa   : contiene piu' stanze e sa cercare un device ovunque

Stanza e Casa contengono RIFERIMENTI agli stessi oggetti Device (non copie):
modificando un Device si aggiorna automaticamente lo stato della casa.
"""


class Device:
    """Un dispositivo della casa. Lo stato e' un dizionario, cosi' va bene
    sia per una luce (acceso/spento) sia per un termostato (temperatura), ecc."""

    def __init__(self, nome, tipo, stato=None):
        self.nome = nome              # es. "luce comodino"
        self.tipo = tipo              # es. "luce", "termostato", "tapparella"
        self.stato = stato or {}      # es. {"acceso": False, "intensita": 0}

    def set_state(self, chiave, valore):
        """Modifica (o aggiunge) un valore dello stato e lo restituisce."""
        self.stato[chiave] = valore
        return self.stato

    def get_state(self):
        """Mostra lo stato corrente del device."""
        return self.stato

    def __str__(self):
        return f"{self.nome} ({self.tipo}) -> {self.stato}"


class Stanza:
    """Una stanza della casa. Contiene i device in un dizionario,
    indicizzati per nome, cosi' la ricerca e' immediata."""

    def __init__(self, nome):
        self.nome = nome
        self.dispositivi = {}         # {nome_device: Device}

    def add_device(self, device):
        """Aggiunge un device alla stanza e lo restituisce."""
        self.dispositivi[device.nome] = device
        return device

    def get_device(self, nome=None):
        """Senza argomenti: restituisce tutti i device della stanza.
        Con un nome: restituisce quel device (o None se non c'e')."""
        if nome is None:
            return self.dispositivi
        return self.dispositivi.get(nome)

    def __str__(self):
        return f"Stanza '{self.nome}' con {len(self.dispositivi)} dispositivi"


class Casa:
    """La casa: contiene le stanze e sa cercare un device in tutte le stanze."""

    def __init__(self, nome="Casa"):
        self.nome = nome
        self.stanze = {}              # {nome_stanza: Stanza}

    def add_stanza(self, stanza):
        """Aggiunge una stanza alla casa e la restituisce."""
        self.stanze[stanza.nome] = stanza
        return stanza

    def get_room(self, nome=None):
        """Senza argomenti: restituisce tutte le stanze.
        Con un nome: restituisce quella stanza (o None se non c'e')."""
        if nome is None:
            return self.stanze
        return self.stanze.get(nome)

    def find_device(self, nome_device):
        """Cerca un device in tutte le stanze.
        Restituisce la coppia (stanza, device), oppure (None, None)."""
        for stanza in self.stanze.values():
            device = stanza.get_device(nome_device)
            if device is not None:
                return stanza, device
        return None, None

    def __str__(self):
        return f"{self.nome}: {len(self.stanze)} stanze"
