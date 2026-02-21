import requests
import pandas as pd
import json
from fpdf import FPDF
import os

# Jumlah BTS per Kelurahan di Yogyakarta
bts_url = "https://dataset.jogjakota.go.id/api/3/action/datastore_search"
bts_params = {
    "resource_id": "d1ca8da3-5603-42d6-ade2-3b2400af02e4"  
}

# Lokasi Free Hotspot di Yogyakarta
hotspot_url = "https://dataset.jogjakota.go.id/api/3/action/datastore_search"
hotspot_params = {
    "resource_id": "dbbcef30-b61e-45f9-acb0-18d21efc5113"
}

RESULT_FOLDER = "../result"
os.makedirs(RESULT_FOLDER, exist_ok=True)

try:
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
        df3.to_csv(f"{RESULT_FOLDER}/bts_data.csv", index=False)
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
        print(df4.head())
        df4.to_csv(f"{RESULT_FOLDER}/hotspot_data.csv", index=False)
        print("Saved to hotspot_data.csv\n")
    else:
        print("Hotspot API request failed:", data4.get("error"))
        
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
except json.JSONDecodeError as e:
    print(f"JSON parsing error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

def csv_to_pdf(csv_file, pdf_file):
    """Convert CSV to PDF with Unicode support"""
    df = pd.read_csv(csv_file)
    
    cols_to_remove = ['_id', 'description', 'iconsrc', 'kategori']
    df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])
    
    df = df.fillna('-')

    pdf = FPDF(orientation='L')  
    pdf.add_page()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_FOLDER = os.path.join(BASE_DIR, "../font")  
    pdf.add_font("DejaVu", style="", fname=os.path.join(FONT_FOLDER, "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", style="B", fname=os.path.join(FONT_FOLDER, "DejaVuSans-Bold.ttf"))

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

csv_to_pdf(f"{RESULT_FOLDER}/hotspot_data.csv", f"{RESULT_FOLDER}/hotspot_data.pdf")
csv_to_pdf(f"{RESULT_FOLDER}/bts_data.csv", f"{RESULT_FOLDER}/bts_data.pdf")
