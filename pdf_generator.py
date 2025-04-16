from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
import pandas as pd
from utils import format_currency
import locale
from datetime import datetime
import re

def generate_pdf(employee_data, output_path, date_info):
    """
    Generate a PDF payslip for an employee.
    
    Args:
        employee_data (pd.DataFrame): DataFrame containing the employee's data
        output_path (str): Path where to save the PDF
        date_info (dict): Dictionary with date information for the header
    """
    if employee_data.empty:
        return False
    
    # Get employee name and total amount
    employee_name = str(employee_data['Operatore'].iloc[0])
    total_amount = employee_data['TotaleImporto'].iloc[0]
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container for PDF elements
    elements = []
    
    # Conta il numero totale di date (una tabella per data)
    total_pages = len(pd.unique(employee_data['Data']))
    
    # Modern Apple-style colors
    apple_blue = colors.HexColor('#007AFF')
    # Funzione per convertire stringhe di data
    def convert_date_string(date_str):
        try:
            # Estrai giorno, mese e anno con regex
            match = re.match(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', date_str)
            if match:
                day, month, year = map(int, match.groups())
                return f"{year:04d}{month:02d}{day:02d}"  # Formato YYYYMMDD per ordinamento
            return date_str
        except:
            return date_str

    apple_light_gray = colors.HexColor('#F5F5F7')
    apple_dark_gray = colors.HexColor('#333333')
    
    # Styles with Apple-like design
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles["Heading1"],
        alignment=1,  # Center alignment
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=apple_dark_gray,
        spaceAfter=16,
        leading=22
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles["Heading2"],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=apple_blue,
        spaceBefore=12,
        spaceAfter=8,
        leading=18
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles["Normal"],
        fontSize=10,
        fontName='Helvetica',
        textColor=apple_dark_gray,
        leading=14
    )
    
    # Pagina header
    elements.append(Paragraph(f"Elenco mese di {date_info['period']} - {employee_name}", title_style))
    elements.append(Spacer(1, 0.3*cm))  # Ridotto spazio dopo il titolo
    
    # Ottieni le date uniche e ordinale dalla più vecchia alla più recente
    unique_dates = sorted(employee_data['Data'].unique(), key=convert_date_string)
    
    # Stima di quanto spazio rimane nella pagina corrente
    available_space = 0  # Inizialmente 0, sarà aggiornato dopo ogni tabella
    
    # Inizializza il contatore di pagine
    page_counter = [1]  # Usa una lista per permettere la modifica dall'interno delle funzioni
    
    # Funzione per incrementare il contatore di pagine
    def increment_page_counter():
        page_counter[0] += 1
        
    # Funzione per ottenere il numero totale di pagine
    def get_total_pages():
        return page_counter[0]
    
    # Per ogni data, crea una sezione separata
    for i, date in enumerate(unique_dates):
        # Formato data più leggibile
        date_str = date if isinstance(date, str) else str(date)
        
        # Calcola lo spazio necessario per questa tabella
        date_data = employee_data[employee_data['Data'] == date]
        rows_count = len(date_data) + 1  # +1 per l'header
        estimated_table_height = (rows_count * 12) * mm  # Stima rozza: 12mm per riga
        
        # Calcola lo spazio necessario includendo tutti gli elementi
        space_for_header = 0.8*cm  # Ridotto spazio per l'intestazione della data
        space_between_tables = 0.5*cm  # Ridotto spazio tra le tabelle
        footer_space = 1*cm  # Spazio riservato per il footer
        
        # Calcola l'altezza totale stimata per questa tabella
        estimated_total_height = estimated_table_height + space_for_header
        
        # Gestione diversa per la prima tabella e le successive
        if i == 0:
            # La prima tabella inizia sempre nel foglio 1 dopo l'intestazione
            available_space = 25*cm - footer_space
        else:
            # Per le tabelle successive, aggiungi lo spazio tra le tabelle
            estimated_total_height += space_between_tables
            
            if estimated_total_height > available_space:
                elements.append(PageBreak())
                available_space = 25*cm  # Reset dello spazio disponibile
                estimated_total_height = estimated_table_height + space_for_header
            else:
                # Se c'è spazio, aggiungi solo lo spaziatore
                elements.append(Spacer(1, space_between_tables))
        
        # Intestazione della data con stile Apple
        elements.append(Paragraph(f"Per il {date_str}", subtitle_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Crea la tabella per questa data
        table_data = []
        
        # Intestazioni tabella con stile Apple
        headers = ['COD.', 'DATORE DI LAVORO', 'DIP.', 'PARAS.', 'ALTRO', 'TOT.', 'SOCI', 'NOTE']
        table_data.append(headers)
        
        # Aggiungi righe
        for _, row in date_data.iterrows():
            table_row = [
                str(row.get('Codice', '')),
                str(row.get('Azienda', ''))[:40],  # Tronca i nomi troppo lunghi a 40 caratteri
                str(int(row.get('DIP.', 0))),      # Converti a intero
                str(int(row.get('PARAS.', 0))),    # Converti a intero
                str(int(row.get('ALTRO', 0))),     # Converti a intero
                str(int(row.get('DIP.', 0) + row.get('PARAS.', 0) + row.get('ALTRO', 0))),  # Calcola TOT
                str(int(row.get('SOCI', 0))),      # Converti a intero
                str(row.get('NOTE', ''))
            ]
            table_data.append(table_row)
        
        # Crea tabella con larghezze personalizzate
        table = Table(table_data, colWidths=[2*cm, 8*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm])
        
        # Stile tabella moderno
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), apple_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Dati
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), apple_dark_gray),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Codice centrato
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Datore di lavoro a sinistra
            ('ALIGN', (2, 1), (6, -1), 'CENTER'),  # Valori numerici centrati
            ('ALIGN', (7, 1), (7, -1), 'LEFT'),    # Note a sinistra
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Colore TOT.
            ('TEXTCOLOR', (5, 1), (5, -1), apple_blue),
            ('FONTNAME', (5, 1), (5, -1), 'Helvetica-Bold'),
            
            # Bordi
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('LINEABOVE', (0, 0), (-1, 0), 1, apple_blue),
            ('LINEBELOW', (0, 0), (-1, 0), 1, apple_blue),
            
            # Righe alternate
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, apple_light_gray])
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        # Aggiorna lo spazio disponibile
        available_space -= estimated_total_height
    
    # Crea il PDF con intestazione e piè di pagina
    def add_page_number(canvas, doc):
        canvas.saveState()
        
        # Colore della pagina
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, doc.width + doc.leftMargin + doc.rightMargin, 
                   doc.height + doc.topMargin + doc.bottomMargin, fill=1)
        
        # Intestazione
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(apple_blue)
        
        # Intestazione destra
        canvas.drawRightString(doc.width + doc.rightMargin, doc.height + doc.topMargin, "Studio Associato Bontempo")
        
        # Intestazione sinistra
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin, employee_name)
        
        # Linea sottile sotto l'intestazione
        canvas.setStrokeColor(apple_light_gray)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 5, 
                   doc.width + doc.rightMargin, doc.height + doc.topMargin - 5)
        
        # Piè di pagina
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(apple_dark_gray)
        
        # Footer con periodo e studio
        footer_text = f"{date_info['period']} - Studio Associato Bontempo"
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 12, footer_text)
        
        # Incrementa il contatore quando viene creata una nuova pagina
        if canvas.getPageNumber() > page_counter[0]:
            increment_page_counter()
        
        # Solo numero pagina corrente
        page_num = canvas.getPageNumber()
        page_text = f"Pagina {page_num}"
        canvas.drawRightString(doc.width + doc.rightMargin, doc.bottomMargin - 12, page_text)
        
        # Linea sottile sopra il piè di pagina
        canvas.line(doc.leftMargin, doc.bottomMargin, 
                   doc.width + doc.rightMargin, doc.bottomMargin)
        
        canvas.restoreState()
    
    # Crea il PDF
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    return True
