# Generatore Fogli Paga

Un'applicazione web per generare automaticamente i fogli paga in formato PDF.

## Funzionalità

- Generazione automatica di PDF per ogni operatore
- Elaborazione dei dati da file Excel/CSV
- Gestione delle date in base alle regole aziendali
- Interfaccia utente intuitiva e moderna

## Requisiti

- Python 3.8 o superiore
- Le dipendenze elencate in `requirements.txt`

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/tuonome/PayrollGenerator.git
cd PayrollGenerator
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Avvia l'applicazione:
```bash
streamlit run app.py
```

## Utilizzo

1. Seleziona l'anno e il mese di elaborazione
2. Carica il tracciato di CL scaricabile dal campo (05>07>11)
3. Carica il file Excel con la lista delle aziende e la data di elaborazione
4. Clicca su "Genera PDF" per creare i documenti
5. Scarica il file ZIP contenente tutti i PDF generati

## Note

- L'applicazione è ottimizzata per funzionare con i formati di file specifici della tua azienda
- Le date vengono calcolate automaticamente in base alle regole aziendali
- I PDF vengono generati con un layout professionale e ordinato 