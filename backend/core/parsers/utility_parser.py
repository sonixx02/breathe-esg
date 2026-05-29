from datetime import datetime
from core.utils import clean_csv_row, parse_localized_number

def parse_utility_row(row_dict, client):
    """
    Parses a single dict row from Utility CSV.
    """
    clean_row = clean_csv_row(row_dict)
    
    aliases = {
        'meter': 'meter_id',
        'meter id': 'meter_id',
        'meter_id': 'meter_id',
        'site': 'site_name',
        'site_name': 'site_name',
        'billing_period_start': 'billing_start',
        'billing_start': 'billing_start',
        'billing_period_end': 'billing_end',
        'billing_end': 'billing_end',
        'usage': 'consumption',
        'usage_kwh': 'consumption',
        'consumption': 'consumption',
        'unit': 'uom',
        'uom': 'uom',
    }
    clean_row = {aliases.get(key, key): value for key, value in clean_row.items()}

    required = ['meter_id', 'billing_start', 'billing_end', 'consumption', 'uom']
    missing = [req for req in required if not clean_row.get(req)]
    if missing:
        return False, None, f"Missing required fields: {', '.join(missing)}"
        
    meter_id = clean_row['meter_id']
    site_name = clean_row.get('site_name', '')
    consumption_str = clean_row['consumption']
    unit = clean_row['uom'].upper()
    
    consumption = parse_localized_number(consumption_str)
    if consumption is None:
        return False, None, f"Invalid consumption format: {consumption_str}"

    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
    
    def parse_date(date_str):
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    period_start = parse_date(clean_row['billing_start'])
    period_end = parse_date(clean_row['billing_end'])
    
    if not period_start or not period_end:
        return False, None, f"Could not parse billing dates"
        
    # Unit normalization (everything to kWh)
    unit_multipliers = {
        'KWH': 1.0,
        'WH': 0.001,
        'MWH': 1000.0,
    }
    
    if unit not in unit_multipliers:
        return False, None, f"Unknown/Unsupported unit: {unit}"
        
    normalized_value = consumption * unit_multipliers[unit]
    normalized_unit = 'kWh'
    
    status = 'PENDING'
    flag_reason = None
    if normalized_value > 100000:
        flag_reason = f"Consumption {normalized_value} {normalized_unit} is unusually high."
        status = 'FLAGGED'

    parsed_data = {
        'scope': 2,
        'activity_category': 'Purchased Electricity',
        'period_start': period_start,
        'period_end': period_end,
        'raw_value': consumption,
        'raw_unit': unit,
        'normalized_value': normalized_value,
        'normalized_unit': normalized_unit,
        'location_raw': meter_id,
        'location_name': site_name,
        'status': status,
        'flag_reason': flag_reason
    }
    
    return True, parsed_data, None
