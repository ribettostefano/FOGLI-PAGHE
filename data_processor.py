import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils import to_float, format_currency, calculate_period_dates

def process_data(payroll_data, manual_date_info=None):
    """
    Process and transform the payroll data.
    
    Args:
        payroll_data (pd.DataFrame): DataFrame containing raw payroll data
        manual_date_info (dict, optional): Dictionary with manually specified date information
        
    Returns:
        tuple: (processed_data, date_info)
    """
    try:
        # Clean column names (remove leading/trailing spaces and special characters)
        payroll_data.columns = payroll_data.columns.str.strip().str.replace('\n', ' ')
        
        # Print columns for debugging
        print("Payroll data columns:", payroll_data.columns.tolist())
        
        # Make a copy to avoid modifying the original
        df = payroll_data.copy()
        
        # Use manually specified date information if provided
        if manual_date_info:
            date_info = manual_date_info
        else:
            # Find the minimum date in the dataframe to determine the month
            # Assuming date column is named 'Data' or similar
            date_columns = [col for col in df.columns if 'data' in col.lower()]
            
            if not date_columns:
                # If no date column found, look for date-like values
                for col in df.columns:
                    if df[col].dtype == 'object':
                        # Check if column contains date-like strings
                        sample = df[col].dropna().head(5)
                        if any(isinstance(val, str) and '/' in val for val in sample):
                            date_columns.append(col)
                    elif 'datetime' in str(df[col].dtype):
                        date_columns.append(col)
            
            # Extract date information for PDF header
            date_info = calculate_period_dates(df, date_columns)
        
        # Tenta di identificare le colonne dalle posizioni esatte (A, B, C, D, ecc.)
        # Queste sarebbero le colonne 0, 1, 2, 3, ecc. nel dataframe
        
        # Assumendo che le colonne sono nell'ordine specificato dal cliente
        # -- Colonne richieste: B=Operatore, C=Codice, D=Azienda, L+M=Dipendenti+StagE, N=Parasub, P=Soci, O=Altro
        
        # Ottieni gli operatori dalla colonna B (indice 1)
        operatori_col = 1  # Colonna B
        if operatori_col < len(df.columns):
            # Rimovi gli spazi in eccesso dai nomi degli operatori
            df.iloc[:, operatori_col] = df.iloc[:, operatori_col].astype(str).str.strip()
            operatori = df.iloc[:, operatori_col].dropna().unique()
        else:
            # Fallback: cerca una colonna chiamata "Operatore" o simile
            operatori_col = next((i for i, col in enumerate(df.columns) if 'operatore' in col.lower()), None)
            if operatori_col is not None:
                df.iloc[:, operatori_col] = df.iloc[:, operatori_col].astype(str).str.strip()
                operatori = df.iloc[:, operatori_col].dropna().unique()
            else:
                # Ultimo fallback: usa la prima colonna
                df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                operatori = df.iloc[:, 0].dropna().unique()
        
        # Initialize new dataframe structure to match the expected output format
        processed_data = pd.DataFrame()
        
        # Per ogni operatore, ottieni i dati delle aziende associate
        rows = []
        for operatore in operatori:
            # Ottieni le righe per questo operatore
            operatore_rows = df[df.iloc[:, operatori_col] == operatore]
            
            # Per ogni riga, estrai i dati corretti
            for _, row in operatore_rows.iterrows():
                # Estrai colonne specifiche come specificato dal cliente
                try:
                    codice = row.iloc[2] if len(row) > 2 else ""  # Colonna C
                    azienda = row.iloc[3] if len(row) > 3 else ""  # Colonna D
                    
                    # L+M = Dipendenti + Stage/Interinali
                    dipendenti = 0
                    if len(row) > 11:  # Colonna L
                        dipendenti += to_float(row.iloc[11])
                    if len(row) > 12:  # Colonna M
                        dipendenti += to_float(row.iloc[12])
                    
                    parasub = to_float(row.iloc[13]) if len(row) > 13 else 0  # Colonna N
                    altro = to_float(row.iloc[15]) if len(row) > 15 else 0    # Colonna P = ALTRO
                    soci = to_float(row.iloc[14]) if len(row) > 14 else 0     # Colonna O = SOCI
                    
                    # Calcola il totale come somma di dipendenti, parasub e altro (escludendo soci)
                    totale = dipendenti + parasub + altro
                    
                    # Raccogli i dati in un dizionario
                    rows.append({
                        'Operatore': operatore,
                        'Codice': codice,
                        'Azienda': azienda,
                        'DIP.': dipendenti,
                        'PARAS.': parasub,
                        'ALTRO': altro,
                        'TOT.': totale,
                        'SOCI': soci,
                        'NOTE': ""  # Placeholder per eventuali note
                    })
                except Exception as row_e:
                    print(f"Errore nel processing della riga per l'operatore {operatore}: {str(row_e)}")
                    continue
        
        # Crea il dataframe dai dati raccolti
        if rows:
            processed_data = pd.DataFrame(rows)
        else:
            # Se non siamo riusciti a estrarre dati dalle colonne esatte, proviamo un'alternativa
            # Mappatura delle colonne per nome
            col_map = {
                'Operatore': next((col for col in df.columns if 'operatore' in col.lower() or 'descrizione oper' in col.lower()), None),
                'Codice': next((col for col in df.columns if 'codice' in col.lower()), None),
                'Azienda': next((col for col in df.columns if 'ragione sociale' in col.lower() or 'azienda' in col.lower()), None),
                'DIP.': next((col for col in df.columns if 'dipendenti' in col.lower()), None),
                'PARAS.': next((col for col in df.columns if 'parasub' in col.lower()), None),
                'ALTRO': next((col for col in df.columns if 'altro' in col.lower()), None),
                'TOT.': next((col for col in df.columns if 'totale' in col.lower()), None),
                'SOCI': next((col for col in df.columns if 'soci' in col.lower()), None)
            }
            
            # Usa le colonne trovate per creare il dataframe
            processed_data = pd.DataFrame()
            for output_col, input_col in col_map.items():
                if input_col and input_col in df.columns:
                    processed_data[output_col] = df[input_col]
                else:
                    # Se la colonna non è stata trovata, usa un valore di default
                    if output_col in ['DIP.', 'PARAS.', 'ALTRO', 'TOT.', 'SOCI']:
                        processed_data[output_col] = 0
                    else:
                        processed_data[output_col] = ""
            
            # Se non abbiamo il totale calcolato, calcoliamolo
            if 'TOT.' in processed_data.columns and all(processed_data['TOT.'] == 0):
                processed_data['TOT.'] = processed_data['DIP.'] + processed_data['PARAS.'] + processed_data['ALTRO']
        
        # Assicurati che tutte le colonne numeriche siano effettivamente numeri
        for col in ['DIP.', 'PARAS.', 'ALTRO', 'TOT.', 'SOCI']:
            if col in processed_data.columns:
                processed_data[col] = processed_data[col].apply(to_float)
        
        # Applica la logica corretta per le date secondo quanto richiesto:
        # - Match tra colonna C (Codice) del file "incolla qui" e colonna A (COD. AZIENDA) del file "lista aziende"
        # - Prendi il giorno dalla colonna DATA ELABORAZIONE (colonna C) del file "lista aziende"
        # - Applica la regola: se giorno > 15 usa il mese selezionato, altrimenti il mese successivo
        
        # Data corrente dal periodo selezionato (anno e mese)
        selected_year = date_info['min_date'].year
        selected_month = date_info['min_date'].month
        
        # Usa la colonna "Consegna PDF" dal file principale
        data_elab_col = df.columns.get_loc("Consegna") if "Consegna" in df.columns else None
        
        if data_elab_col is None:
            print("Colonna 'Consegna' non trovata nel file")
        
        # Crea un dizionario per mappare il codice azienda alla data di elaborazione
        # Formato: {codice_azienda: {'giorno': giorno, 'stringa_data': data_formattata}}
        azienda_to_date_mapping = {}
        
        # Estrai la data dalla colonna "Consegna"
        for idx, row in df.iterrows():
            try:
                cod_azienda = str(row['Codice']).strip()
                if not cod_azienda:
                    continue
                    
                # Ottieni la data dalla colonna "Consegna PDF"
                data_val = row.get('Consegna', None)
                
                # Stampa per debug
                print(f"Riga {idx}: Codice azienda: '{cod_azienda}', Data val: '{data_val}'")
                
                # Se la data è vuota, 0 o non valida, usa 01/01/1900
                if pd.isnull(data_val) or str(data_val).strip() == "" or str(data_val).strip() == "0":
                    azienda_to_date_mapping[cod_azienda] = {
                        'giorno': 1,
                        'data': datetime(1900, 1, 1),
                        'data_formattata': "01/01/1900"
                    }
                    print(f"  - Data mancante o zero per {cod_azienda}, usando 01/01/1900")
                    continue
                
                if pd.notnull(data_val):
                    # Prova diverse strategie per estrarre il giorno
                    giorno = None
                    
                    # Strategia 1: è già un numero intero
                    try:
                        giorno_val = int(float(str(data_val).strip()))
                        if 1 <= giorno_val <= 31:
                            giorno = giorno_val
                            print(f"  - Estratto giorno da numero: {giorno}")
                    except:
                        pass
                    
                    # Strategia 2: è una data in formato stringa
                    if giorno is None:
                        try:
                            # Tenta di convertire in data
                            data_str = str(data_val).strip()
                            # Verifica se è in formato gg/mm/aaaa o simili
                            if '/' in data_str:
                                parts = data_str.split('/')
                                if len(parts) >= 1 and parts[0].isdigit():
                                    giorno = int(parts[0])
                                    print(f"  - Estratto giorno da stringa con /: {giorno}")
                            # Verifica se è in formato gg-mm-aaaa o simili
                            elif '-' in data_str:
                                parts = data_str.split('-')
                                if len(parts) >= 1 and parts[0].isdigit():
                                    giorno = int(parts[0])
                                    print(f"  - Estratto giorno da stringa con -: {giorno}")
                        except:
                            pass
                    
                    # Strategia 3: è una data in formato datetime
                    if giorno is None:
                        try:
                            data_datetime = pd.to_datetime(data_val, errors='coerce')
                            if pd.notnull(data_datetime):
                                giorno = data_datetime.day
                                print(f"  - Estratto giorno da datetime: {giorno}")
                        except:
                            pass
                            
                    # Se non siamo riusciti a estrarre un giorno valido, usa un valore di default
                    if giorno is None:
                        # Usa il primo giorno del mese come fallback
                        giorno = 1
                        print(f"  - Usando giorno di default: {giorno}")
                        
                    # Calcola mese e anno secondo la regola
                    # Se giorno > 15, usa il mese selezionato
                    # Se giorno <= 15, usa il mese successivo
                    mese_da_usare = selected_month if giorno > 15 else (selected_month % 12) + 1
                    
                    # Gestisci il cambio di anno se necessario
                    anno_da_usare = selected_year
                    if mese_da_usare < selected_month:
                        anno_da_usare += 1
                    
                    # Assicurati che il giorno sia valido per il mese selezionato
                    try:
                        # Calcola l'ultimo giorno del mese
                        if mese_da_usare in [4, 6, 9, 11]:  # Aprile, Giugno, Settembre, Novembre
                            ultimo_giorno = 30
                        elif mese_da_usare == 2:  # Febbraio
                            # Controllo anno bisestile
                            if (anno_da_usare % 4 == 0 and anno_da_usare % 100 != 0) or (anno_da_usare % 400 == 0):
                                ultimo_giorno = 29
                            else:
                                ultimo_giorno = 28
                        else:
                            ultimo_giorno = 31
                        
                        # Usa il giorno corretto (non superiore all'ultimo giorno del mese)
                        giorno_corretto = min(giorno, ultimo_giorno)
                        
                        # Crea la data completa come datetime per elaborazioni interne
                        data_elaborazione = datetime(anno_da_usare, mese_da_usare, giorno_corretto)
                        
                        # Crea anche la stringa della data formattata
                        data_formattata = f"{giorno_corretto:02d}/{mese_da_usare:02d}/{anno_da_usare}"
                        
                        # Aggiungi al mapping sia il giorno originale che la data formattata
                        azienda_to_date_mapping[cod_azienda] = {
                            'giorno': giorno, 
                            'data': data_elaborazione,
                            'data_formattata': data_formattata
                        }
                        
                        print(f"  - Data finale per {cod_azienda}: {data_formattata}")
                    except ValueError as e:
                        # Se la data non è valida, stampa l'errore e salta
                        print(f"  - Errore nella creazione della data: {str(e)}")
                        continue
            except Exception as e:
                print(f"  - Errore nell'elaborazione della data: {str(e)}")
                continue

        # Stampa il mapping per debug
        print(f"Mapping codice azienda -> data: {azienda_to_date_mapping}")
        
        # Assegna le date alle righe in base al codice azienda
        processed_data['Data'] = None
        
        # Per ogni riga nel dataframe elaborato
        for idx, row in processed_data.iterrows():
            codice_azienda = str(row['Codice']).strip()
            
            # Cerca la data dal mapping
            if codice_azienda in azienda_to_date_mapping:
                # Usa la data formattata correttamente
                processed_data.at[idx, 'Data'] = azienda_to_date_mapping[codice_azienda]['data_formattata']
            else:
                # Data di fallback solo se l'azienda non è presente nel mapping
                processed_data.at[idx, 'Data'] = "01/01/1900"
                print(f"  - Azienda {codice_azienda} non trovata nel mapping, usando 01/01/1900")
        
        # Aggiungi altre colonne richieste per compatibilità con il generatore PDF
        processed_data['Importo'] = processed_data['TOT.']
        processed_data['Descrizione'] = processed_data['Azienda']
        
        # Format numeric columns
        for col in ['TOT.', 'Importo']:
            if col in processed_data.columns:
                processed_data[f'{col}_Formatted'] = processed_data[col].apply(format_currency)
        
        # Calculate totals by employee
        employee_totals = processed_data.groupby('Operatore')['Importo'].sum().reset_index()
        employee_totals.rename(columns={'Importo': 'TotaleImporto'}, inplace=True)
        
        # Merge totals back to the main dataframe
        processed_data = processed_data.merge(employee_totals, on='Operatore')
        
        # Add empty CompanyDetails column for compatibility with older code
        processed_data['CompanyDetails'] = [{}] * len(processed_data)
        
        return processed_data, date_info
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise e
