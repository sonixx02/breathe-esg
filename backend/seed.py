import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breatheesg.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Client, PlantMaster, MaterialCategoryMap, AirportMaster

def seed_data():
    # 1. User
    user, created = User.objects.get_or_create(username='analyst', defaults={'email': 'analyst@acme.com'})
    if created:
        user.set_password('password123')
        user.save()
        print("Created analyst user.")
    
    # 2. Client
    client, _ = Client.objects.get_or_create(name='Acme Corp', slug='acme')
    print(f"Client: {client.name}")

    # 3. Plant Master
    plants = [
        {'plant_code': 'PLT_101', 'plant_name': 'Mumbai Refinery', 'city': 'Mumbai', 'country': 'India'},
        {'plant_code': 'PLT_102', 'plant_name': 'Pune Plant', 'city': 'Pune', 'country': 'India'},
        {'plant_code': 'PLT_103', 'plant_name': 'Chennai Facility', 'city': 'Chennai', 'country': 'India'},
    ]
    for p in plants:
        PlantMaster.objects.get_or_create(client=client, plant_code=p['plant_code'], defaults=p)
    print("Seeded PlantMaster.")

    # 4. Material Category Map
    materials = [
        {'material_code': 'DIESEL-HSD', 'material_name': 'High Speed Diesel', 'activity_category': 'Mobile Combustion', 'scope': 1, 'default_unit': 'L'},
        {'material_code': 'LPG-CYL', 'material_name': 'LPG Cylinder 14kg', 'activity_category': 'Stationary Combustion', 'scope': 1, 'default_unit': 'KG'},
        {'material_code': 'FURNACE-OIL', 'material_name': 'Furnace Oil', 'activity_category': 'Stationary Combustion', 'scope': 1, 'default_unit': 'L'},
    ]
    for m in materials:
        MaterialCategoryMap.objects.get_or_create(client=client, material_code=m['material_code'], defaults=m)
    print("Seeded MaterialCategoryMap.")

    # 5. Airport Master
    airports = [
        {'iata_code': 'BOM', 'airport_name': 'Chhatrapati Shivaji Maharaj International Airport', 'city': 'Mumbai', 'country': 'India', 'latitude': 19.0896, 'longitude': 72.8656},
        {'iata_code': 'LHR', 'airport_name': 'Heathrow Airport', 'city': 'London', 'country': 'UK', 'latitude': 51.4700, 'longitude': -0.4543},
        {'iata_code': 'JFK', 'airport_name': 'John F. Kennedy International Airport', 'city': 'New York', 'country': 'USA', 'latitude': 40.6413, 'longitude': -73.7781},
    ]
    for a in airports:
        AirportMaster.objects.get_or_create(iata_code=a['iata_code'], defaults=a)
    print("Seeded AirportMaster.")
    
    print("Seed complete.")

if __name__ == '__main__':
    seed_data()
