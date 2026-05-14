# PR Description: Fix Koolnova Home Assistant Integration

## Problemi risolti:

1. **Login API**: Supporto per username e email (session.py)
2. **Stato globale**: Sincronizzazione corretta dello stato del fan globale
3. **Rate limiting**: Gestione migliorata degli errori 429 con backoff esponenziale
4. **Type hints**: Aggiunti typing corretti per tutte le funzioni
5. **Manifest**: Aggiornata versione a 1.2.6 e dipendenze

## Cambi specifici:

### session.py (koolnova_api/session.py):
- Fix payload construction per supporto username/email
- Migliorata gestione errori di autenticazione
- Aggiunto logging dettagliato

### climate.py (koolnova/climate.py):
- Sincronizzazione corretta dello stato globale del fan
- Miglior gestione errori nell'aggiornamento globale
- Aggiunti controlli di validità parametri

### Manifest.json:
- Aggiornata versione a 1.2.6
- Aggiunte dipendenze: requests>=2.25.0, python-dateutil>=2.8.0

## Test eseguiti:
- [x] Login API con username/email
- [x] Controllo globale HVAC
- [x] Gestione errori rate limiting
- [x] Cache sensori ottimizzata
- [x] Type hints corretti
- [x] Lint pass

## Checklist:
- [x] Codice funzionale
- [x] Test passati
- [x] Documentazione aggiornata
- [x] Manifest aggiornato
- [x] PR descritto chiaramente