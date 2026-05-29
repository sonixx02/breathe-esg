import math
from datetime import datetime
from core.models import AirportMaster
from core.utils import clean_csv_row, parse_localized_number

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def parse_travel_row(row_dict, client):
    """
    Parses a single dict row from Travel CSV.
    """
    clean_row = clean_csv_row(row_dict)
    
    if not clean_row.get('category'):
        return False, None, "Missing category"
        
    category = clean_row['category'].lower()
    date_str = clean_row.get('date')
    
    parsed_date = None
    if date_str:
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
                
    if category == 'flight':
        distance_str = clean_row.get('distance_km')
        origin_code = clean_row.get('origin', '').upper()
        dest_code = clean_row.get('destination', '').upper()
        
        distance = None
        if distance_str:
            distance = parse_localized_number(distance_str)
                
        if distance is None:
            # Fallback to airport coords
            if not origin_code or not dest_code:
                return False, None, "Missing distance and airport codes"
                
            origin_apt = AirportMaster.objects.filter(iata_code=origin_code).first()
            dest_apt = AirportMaster.objects.filter(iata_code=dest_code).first()
            
            if not origin_apt or not dest_apt:
                return False, None, f"Unknown airport codes: {origin_code} to {dest_code}"
                
            distance = haversine_distance(
                origin_apt.latitude, origin_apt.longitude,
                dest_apt.latitude, dest_apt.longitude
            )
            
        status = 'PENDING'
        flag_reason = None
        if distance > 10000:
            status = 'FLAGGED'
            flag_reason = f"Flight distance {round(distance, 1)} km is unusually high."

        parsed_data = {
            'scope': 3,
            'activity_category': f"Flight - {clean_row.get('cabin_class', 'economy').title()}",
            'activity_date': parsed_date,
            'raw_value': distance,
            'raw_unit': 'km',
            'normalized_value': distance,
            'normalized_unit': 'km',
            'location_raw': f"{origin_code}->{dest_code}",
            'location_name': f"{origin_code} to {dest_code}",
            'status': status,
            'flag_reason': flag_reason
        }
        return True, parsed_data, None
        
    elif category == 'hotel':
        nights_str = clean_row.get('nights')
        if not nights_str:
            return False, None, "Missing nights for hotel stay"
            
        nights = parse_localized_number(nights_str)
        if nights is None:
            return False, None, "Invalid nights value"
            
        status = 'PENDING'
        flag_reason = None
        if nights > 14:
            status = 'FLAGGED'
            flag_reason = f"Hotel stay of {nights} nights is unusually long."

        parsed_data = {
            'scope': 3,
            'activity_category': 'Hotel Stay',
            'activity_date': parsed_date,
            'raw_value': nights,
            'raw_unit': 'nights',
            'normalized_value': nights,
            'normalized_unit': 'nights',
            'location_raw': clean_row.get('hotel_name', clean_row.get('origin', '')),
            'location_name': clean_row.get('hotel_name', clean_row.get('origin', '')),
            'status': status,
            'flag_reason': flag_reason
        }
        return True, parsed_data, None
        
    elif category == 'ground':
        distance_str = clean_row.get('distance_km')
        if not distance_str:
            return False, None, "Missing distance for ground transport"
            
        distance = parse_localized_number(distance_str)
        if distance is None:
            return False, None, "Invalid distance value"
            
        status = 'PENDING'
        flag_reason = None
        if distance > 300:
            status = 'FLAGGED'
            flag_reason = f"Ground transport distance {distance} km is unusually high."

        parsed_data = {
            'scope': 3,
            'activity_category': 'Ground Transport',
            'activity_date': parsed_date,
            'raw_value': distance,
            'raw_unit': 'km',
            'normalized_value': distance,
            'normalized_unit': 'km',
            'location_raw': f"{clean_row.get('origin')} -> {clean_row.get('destination')}",
            'location_name': f"{clean_row.get('origin')} -> {clean_row.get('destination')}",
            'status': status,
            'flag_reason': flag_reason
        }
        return True, parsed_data, None
        
    else:
        return False, None, f"Unsupported travel category: {category}"
