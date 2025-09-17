from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def brazilian_currency(value):
    """
    Format a number as Brazilian currency.
    
    Examples:
        1234.56 -> "1.234,56"
        1000000.00 -> "1.000.000,00"
        50.5 -> "50,50"
    """
    if value is None:
        return "0,00"
    
    try:
        # Convert to float if it's not already
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        
        value = float(value)
        
        # Format with 2 decimal places and use comma as decimal separator
        formatted = f"{value:,.2f}"
        
        # Replace . with temporary marker, , with ., and marker with ,
        # This converts US format (1,234.56) to Brazilian format (1.234,56)
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        
        return formatted
        
    except (ValueError, TypeError):
        return "0,00"

@register.filter
def brazilian_number(value):
    """
    Format a number as Brazilian decimal number.
    
    Examples:
        15.50 -> "15,50"
        1234.56 -> "1.234,56"
    """
    if value is None:
        return "0,00"
    
    try:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        
        value = float(value)
        
        # Format with 2 decimal places and use comma as decimal separator
        formatted = f"{value:,.2f}"
        
        # Convert US format to Brazilian format
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        
        return formatted
        
    except (ValueError, TypeError):
        return "0,00"