import pdfplumber
import re
import csv
import os
from datetime import datetime

def extract_gascaribe_data(pdf_path):
    """
    Extrae datos específicos de una factura GASCARIBE sin valores por defecto
    """
    data = {
        'Consumo': None,
        'Tarifa': None,
        'Costo': None,
        'Total Factura': None
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            pattern_match = re.search(r'1333\s+1331\s+0\s+-\s+1000\s+(\d+)\s+(\d+)\s+([\d,]+)', text)
            if pattern_match:
                data['Tarifa'] = pattern_match.group(1)
                data['Consumo'] = pattern_match.group(2)
                data['Costo'] = pattern_match.group(3)
            
            if not data['Consumo']:
                consumo_match = re.search(r'(\d+)\s+M3\s+Equivalen', text)
                if consumo_match:
                    data['Consumo'] = consumo_match.group(1)
            
            if not data['Tarifa']:
                if data['Consumo']:
                    tarifa_match = re.search(rf'0\s+-\s+1000\s+(\d+)\s+{data["Consumo"]}', text)
                    if tarifa_match:
                        data['Tarifa'] = tarifa_match.group(1)
            
            if not data['Costo']:
                costo_match = re.search(r'31 - CONSUMO DE GAS NATURAL.*?und\s+1\s+([\d,]+)', text, re.DOTALL)
                if costo_match:
                    data['Costo'] = costo_match.group(1)
            
            if not data['Total Factura']:
                total_match = re.search(r'\$\s*([\d,]+)\s*\n\s*Consulta tu cupo', text)
                if total_match:
                    data['Total Factura'] = total_match.group(1)
                else:
                    total_alt_match = re.search(r'\$\s*([\d,]+)', text)
                    if total_alt_match:
                        data['Total Factura'] = total_alt_match.group(1)
            
            return data
            
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
        return None

def export_to_csv(data, pdf_filename, output_file='gascaribe_facturas.csv'):
    """
    Exporta los datos a un archivo CSV
    """
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Archivo', 'Fecha_Extraccion', 'Consumo', 'Tarifa', 'Costo', 'Total_Factura']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'Archivo': pdf_filename,
            'Fecha_Extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Consumo': data['Consumo'] if data['Consumo'] else '',
            'Tarifa': data['Tarifa'] if data['Tarifa'] else '',
            'Costo': data['Costo'] if data['Costo'] else '',
            'Total_Factura': data['Total Factura'] if data['Total Factura'] else ''
        })

def main():
    pdf_path = "GASCARIBE_Test.pdf" 
    
    extracted_data = extract_gascaribe_data(pdf_path)
    
    if extracted_data:
        print("=== RESULTADOS ENCONTRADOS ===")
        
        if extracted_data['Consumo']:
            print(f"Consumo: {extracted_data['Consumo']}")
        else:
            print("Consumo: No encontrado")
            
        if extracted_data['Tarifa']:
            print(f"Tarifa: {extracted_data['Tarifa']}")
        else:
            print("Tarifa: No encontrado")
            
        if extracted_data['Costo']:
            print(f"Costo: {extracted_data['Costo']}")
        else:
            print("Costo: No encontrado")
            
        if extracted_data['Total Factura']:
            print(f"Total Factura: {extracted_data['Total Factura']}")
        else:
            print("Total Factura: No encontrado")
        
        pdf_filename = os.path.basename(pdf_path)
        export_to_csv(extracted_data, pdf_filename)
        print(f"\n✓ Datos exportados a: gascaribe_facturas.csv")
        
    else:
        print("Error: No se pudieron extraer datos del PDF")

if __name__ == "__main__":
    main()