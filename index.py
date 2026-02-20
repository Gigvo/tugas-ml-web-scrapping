import requests
import pandas as pd
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from fpdf import FPDF

# API 1: Jogja Dataset
jogja_url = "https://dataset.jogjakota.go.id/api/3/action/datastore_search"
jogja_params = {
    "resource_id": "eaccabe7-6167-4215-8654-787e76f56956",
}

# API 2: PeeringDB
peeringdb_url = "https://peeringdb.com/api/ix"
peeringdb_params = {
    "country": "ID",
    "city": "Yogyakarta"
}

# API 3: Jumlah BTS per Kelurahan di Yogyakarta
bts_url = "https://dataset.jogjakota.go.id/api/3/action/datastore_search"
bts_params = {
    "resource_id": "d1ca8da3-5603-42d6-ade2-3b2400af02e4"  
}

hotspot_url = "https://dataset.jogjakota.go.id/api/3/action/datastore_search"
hotspot_params = {
    "resource_id": "dbbcef30-b61e-45f9-acb0-18d21efc5113"
}

def reverse_geocode(latitude, longitude, retries=3):
    """Convert coordinates to address using Nominatim"""
    geolocator = Nominatim(user_agent="hotspot_geocoder")
    
    for attempt in range(retries):
        try:
            location = geolocator.reverse(f"{latitude}, {longitude}", language='id')
            return location.address
        except GeocoderTimedOut:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return "Address not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Address not found"

try:
    # Scrape from Jogja Dataset
    print("Fetching data from Jogja Dataset...")
    response1 = requests.get(jogja_url, params=jogja_params, timeout=30)
    response1.raise_for_status()
    
    data1 = response1.json()
    
    if data1.get("success"):
        records1 = data1["result"]["records"]
        df1 = pd.DataFrame(records1)
        print(f"Jogja data retrieved successfully! Got {len(df1)} records")
        print(df1.head())
        df1.to_csv("jogja_data.csv", index=False)
        print("Saved to jogja_data.csv\n")
    else:
        print("Jogja API request failed:", data1.get("error"))
    
    # Scrape from PeeringDB
    print("Fetching data from PeeringDB...")
    response2 = requests.get(peeringdb_url, params=peeringdb_params, timeout=30)
    response2.raise_for_status()
    
    data2 = response2.json()
    
    if "data" in data2:
        records2 = data2["data"]
        df2 = pd.DataFrame(records2)
        print(f"PeeringDB data retrieved successfully! Got {len(df2)} records")
        print(df2.head())
        df2.to_csv("peeringdb_yogyakarta.csv", index=False)
        print("Saved to peeringdb_yogyakarta.csv")
    else:
        print("PeeringDB API response format unexpected")
        
    # Scrape from BTS Dataset
    print("Fetching data from BTS Dataset...")
    response3 = requests.get(bts_url, params=bts_params, timeout=30)
    response3.raise_for_status()
    
    data3 = response3.json()
    
    if data3.get("success"):
        records3 = data3["result"]["records"]
        df3 = pd.DataFrame(records3)
        print(f"BTS data retrieved successfully! Got {len(df3)} records")
        print(df3.head())
        df3.to_csv("bts_data.csv", index=False)
        print("Saved to bts_data.csv\n")
    else:
        print("BTS API request failed:", data3.get("error"))
        
    # Scrape from Free Hotspot Dataset
    print("Fetching data from Free Hotspot Dataset...")
    
    response4 = requests.get(hotspot_url, params=hotspot_params, timeout=30)
    response4.raise_for_status()
    
    data4 = response4.json()
    
    if data4.get("success"):
        records4 = data4["result"]["records"]
        df4 = pd.DataFrame(records4)
        print(f"Hotspot data retrieved successfully! Got {len(df4)} records")
        
        # Convert coordinates to addresses
    
        print(df4.head())
        df4.to_csv("hotspot_data.csv", index=False)
    else:
        print("Hotspot API request failed:", data4.get("error"))
        
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
except json.JSONDecodeError as e:
    print(f"JSON parsing error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

# Convert CSV files to PDF
def csv_to_pdf(csv_file, pdf_file):
    """Convert CSV to PDF with Unicode support"""
    df = pd.read_csv(csv_file)
    
    cols_to_remove = ['_id', 'description' ,'iconsrc', 'kategori']
    df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])
    
    # Replace NaN/empty values with '-'
    df = df.fillna('-')

    pdf = FPDF(orientation='L')  
    pdf.add_page()

    pdf.add_font("DejaVu", style="", fname="DejaVuSans.ttf")
    pdf.add_font("DejaVu", style="B", fname="DejaVuSans-Bold.ttf")

    pdf.set_font("DejaVu", style="B", size=10)
    pdf.cell(0, 10, f"Data from {csv_file}", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)
    
    custom_widths = {
        'id': 10,
        'title': 60,
        'kecamatan': 30,
        'kelurahan': 30,
        'longitude': 25,
        'latitude': 25,
        # BTS columns
        'Kode Kecamatan': 35,
        'Kecamatan': 45,
        'Jumlah': 20,
    }
    
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_widths = []
    for col in df.columns:
        col_widths.append(custom_widths.get(col, 30))
    
    total = sum(col_widths)
    col_widths = [w * usable_width / total for w in col_widths]

    pdf.set_font("DejaVu", style="B", size=8)
    for col, width in zip(df.columns, col_widths):
        pdf.cell(width, 10, str(col), border=1)
    pdf.ln()
    
    pdf.set_font("DejaVu", size=8)
    for _, row in df.iterrows():
        for col, width in zip(df.columns, col_widths):
            cell_text = str(row[col])[:30]  
            pdf.cell(width, 10, cell_text, border=1)
        pdf.ln()
    
    pdf.output(pdf_file)
    print(f"Saved to {pdf_file}")

csv_to_pdf("hotspot_data.csv", "hotspot_data.pdf")
csv_to_pdf("bts_data.csv", "bts_data.pdf")
