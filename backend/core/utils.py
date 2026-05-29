def clean_csv_row(row_dict):
    clean = {}
    for key, value in row_dict.items():
        if key is None:
            clean['_extra_columns'] = value
            continue
        clean[key.strip().lower()] = str(value).strip() if value else None
    return clean

def parse_localized_number(val_str):
    if not val_str:
        return None
    val_str = str(val_str).strip()
    
    if ',' in val_str and '.' in val_str:
        last_comma = val_str.rfind(',')
        last_dot = val_str.rfind('.')
        if last_comma > last_dot:
            val_str = val_str.replace('.', '').replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    elif ',' in val_str:
        parts = val_str.split(',')
        if len(parts) == 2 and len(parts[1]) == 3:
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace(',', '.')
            
    try:
        return float(val_str)
    except ValueError:
        return None

