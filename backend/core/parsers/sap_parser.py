from datetime import datetime

from core.models import MaterialCategoryMap, PlantMaster
from core.utils import clean_csv_row, parse_localized_number


def parse_sap_row(row_dict, client):
    """
    Parses a single dict row from SAP CSV.
    Returns (is_valid, parsed_data, error_message)
    """
    # Normalize headers
    # English and German aliases mapping
    aliases = {
        'ebeln': 'po_number',
        'po_number': 'po_number',
        'matnr': 'material_code',
        'material_code': 'material_code',
        'txz01': 'material_desc',
        'maktx': 'material_desc',
        'material_desc': 'material_desc',
        'plant_code': 'plant_code',
        'werk': 'plant_code',
        'werks': 'plant_code',
        'menge': 'quantity',
        'quantity': 'quantity',
        'bestellmenge': 'quantity',
        'unit': 'unit',
        'meins': 'unit',
        'budat': 'doc_date',
        'doc_date': 'doc_date',
        'buchungsdatum': 'doc_date',
    }
    
    row_dict = clean_csv_row(row_dict)
    clean_row = {}
    for key, value in row_dict.items():
        if key in aliases:
            clean_row[aliases[key]] = value
            
    # Check required fields
    required = ['material_code', 'plant_code', 'quantity', 'unit']
    missing = [req for req in required if not clean_row.get(req)]
    if missing:
        return False, None, f"Missing required fields: {', '.join(missing)}"
        
    material_code = clean_row['material_code']
    plant_code = clean_row['plant_code']
    quantity_str = clean_row['quantity']
    unit = clean_row['unit'].upper()
    doc_date_str = clean_row.get('doc_date')
    
    # Parse quantity
    quantity = parse_localized_number(quantity_str)
    if quantity is None:
        return False, None, f"Invalid quantity format: {clean_row['quantity']}"

    # Parse date
    parsed_date = None
    if doc_date_str:
        date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d-%m-%Y', '%Y%m%d', '%m/%d/%Y', '%d/%m/%Y']
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(doc_date_str, fmt).date()
                break
            except ValueError:
                continue
        if not parsed_date:
            return False, None, f"Could not parse date: {doc_date_str}"
            
    # Lookup Plant
    plant = PlantMaster.objects.filter(client=client, plant_code=plant_code).first()
    if not plant:
        return False, None, f"Unknown plant code: {plant_code}"
        
    # Lookup Material
    material = MaterialCategoryMap.objects.filter(client=client, material_code=material_code).first()
    if not material:
        return False, None, f"Unknown/Unsupported material code: {material_code}"
        
    # Normalize Unit
    
    supported_units = {
        'L': ('L', 1.0),
        'KG': ('KG', 1.0),
        'MT': ('KG', 1000.0),
        'GAL': ('L', 3.78541),
        'BBL': ('L', 158.987),
        'PCS': ('PCS', 1.0)
    }
    
    if unit not in supported_units:
        return False, None, f"Unknown/Unsupported unit: {unit}"
        
    target_unit, multiplier = supported_units[unit]
    normalized_quantity = quantity * multiplier
    
   
    flag_reason = None
    status = 'PENDING'
    if normalized_quantity > 100000:
        flag_reason = f"Quantity {normalized_quantity} {target_unit} is unusually high."
        status = 'FLAGGED'

    parsed_data = {
        'scope': material.scope,
        'activity_category': material.activity_category,
        'activity_date': parsed_date,
        'raw_value': quantity,
        'raw_unit': unit,
        'normalized_value': normalized_quantity,
        'normalized_unit': target_unit,
        'location_raw': plant_code,
        'location_name': plant.plant_name,
        'status': status,
        'flag_reason': flag_reason
    }
    
    return True, parsed_data, None
