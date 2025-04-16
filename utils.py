import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import locale
import calendar

def format_currency(value):
    """
    Format a number as a currency string (€ X.XXX,XX).
    
    Args:
        value: The numeric value to format
        
    Returns:
        str: Formatted currency string
    """
    try:
        # Try to set Italian locale for proper formatting
        try:
            locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'it_IT')
            except:
                # Fallback if Italian locale is not available
                pass
        
        # Convert to float first
        val = to_float(value)
        
        # Format with Euro symbol
        return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        # Return original value if formatting fails
        return str(value)

def to_float(value):
    """
    Convert a value to float, handling different number formats.
    
    Args:
        value: The value to convert
        
    Returns:
        float: Converted value or 0.0 if conversion fails
    """
    if pd.isna(value):
        return 0.0
    
    try:
        # Try direct conversion
        return float(value)
    except (ValueError, TypeError):
        if isinstance(value, str):
            # Handle European number format (comma as decimal separator)
            try:
                return float(value.replace(".", "").replace(",", "."))
            except (ValueError, TypeError):
                # Remove currency symbols and try again
                clean_value = value.replace("€", "").replace("$", "").strip()
                try:
                    return float(clean_value.replace(".", "").replace(",", "."))
                except (ValueError, TypeError):
                    return 0.0
        return 0.0

def calculate_period_dates(df, date_columns):
    """
    Calculate the period start and end dates based on the data.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data
        date_columns (list): List of potential date column names
        
    Returns:
        dict: Dictionary with period information
    """
    min_date = None
    max_date = None
    
    # Try to find date columns and extract min/max dates
    for col in date_columns:
        if col in df.columns:
            series = pd.to_datetime(df[col], errors='coerce')
            if not series.isna().all():
                col_min = series.min()
                col_max = series.max()
                
                if min_date is None or col_min < min_date:
                    min_date = col_min
                
                if max_date is None or col_max > max_date:
                    max_date = col_max
    
    # If no valid dates found, use current month
    if min_date is None:
        now = datetime.now()
        min_date = datetime(now.year, now.month, 1)
        max_date = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    
    # Format dates
    month_name = min_date.strftime("%B").capitalize()
    year = min_date.year
    
    # If the period spans multiple months, use the range
    if min_date.month != max_date.month or min_date.year != max_date.year:
        period = f"{min_date.strftime('%B %Y')} - {max_date.strftime('%B %Y')}"
    else:
        period = f"{month_name} {year}"
    
    # Format dates for display
    start_date = min_date.strftime("%d/%m/%Y")
    end_date = max_date.strftime("%d/%m/%Y")
    
    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "min_date": min_date,
        "max_date": max_date
    }
