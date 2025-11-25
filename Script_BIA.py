import pdfplumber
import re
import csv
import os
from datetime import datetime

def extract_invoice_data(pdf_path):
    """
    Extrae datos específicos de una factura de servicios públicos BIA
    """
    data = {
        'Consumo': None,
        'Tarifa': None,
        'Costo': None,  
        'Servicios BIA': None,
        'Otros cobros': None,
        'Energía Solar': None,
        'Intereses': None,
        'Retenciones': None,
        'Total de la Factura': None
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            patterns = {
                'Consumo': r'Energía activa\s*\(([\d.,]+)\s*kWh',
                'Tarifa': r'Cu\s*\$([\d.,]+)',
                'Servicios BIA': r'Servicios BIA.*?\$([\d.,]+)',
                'Otros cobros': r'Otros cobros\s*\$\s*([\d.,]+)',
                'Intereses': r'Intereses\s*\$\s*([\d.,]+)',
                'Retenciones': r'Retenciones\s*-\$([\d.,]+)',
                'Total de la Factura': r'Total a cobrar\s*\$\s*([\d.,]+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    if field == 'Retenciones':
                        data[field] = f"-{match.group(1)}"
                    else:
                        data[field] = match.group(1)
            
            energia_solar_patterns = [
                r'Energía Solar\s*[^\d]*-\$?([\d.,]+)',
                r'Energía Solar.*?-\$?([\d.,]+)',
            ]
            
            for pattern in energia_solar_patterns:
                match = re.search(pattern, text)
                if match:
                    data['Energía Solar'] = f"-{match.group(1)}"
                    break
            
            if data['Consumo'] and data['Tarifa']:

                consumo_num = float(data['Consumo'].replace('.', '').replace(',', '.'))
                tarifa_num = float(data['Tarifa'].replace('.', '').replace(',', '.'))
                
                costo_calculado = consumo_num * tarifa_num
                
                data['Costo'] = f"{costo_calculado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            return data
            
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
        return None

def exportar_a_csv(datos, pdf_path, csv_filename="BIA_facturas.csv"):
    """
    Exporta los datos extraídos a un archivo CSV
    """
    csv_data = {
        'Fecha_Extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Archivo_PDF': os.path.basename(pdf_path),
        'Consumo_kWh': datos.get('Consumo', 'No encontrado'),
        'Tarifa_por_kWh': datos.get('Tarifa', 'No encontrado'),
        'Costo_Calculado': datos.get('Costo', 'No encontrado'),
        'Servicios_BIA': datos.get('Servicios BIA', 'No encontrado'),
        'Otros_Cobros': datos.get('Otros cobros', 'No encontrado'),
        'Energia_Solar': datos.get('Energía Solar', 'No encontrado'),
        'Intereses': datos.get('Intereses', 'No encontrado'),
        'Retenciones': datos.get('Retenciones', 'No encontrado'),
        'Total_Factura': datos.get('Total de la Factura', 'No encontrado')
    }
    
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Fecha_Extraccion', 'Archivo_PDF', 'Consumo_kWh', 'Tarifa_por_kWh', 
            'Costo_Calculado', 'Servicios_BIA', 'Otros_Cobros', 'Energia_Solar',
            'Intereses', 'Retenciones', 'Total_Factura'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(csv_data)
    
    print(f" Resultados exportados a: {csv_filename}")
    return csv_filename

def mostrar_resultados(datos):
    """
    Muestra los resultados de forma organizada en consola
    """
    print("\n" + "="*60)
    print("FACTURA BIA - DATOS EXTRAÍDOS")
    print("="*60)
    
    campos = [
        ('Consumo', 'Consumo', ' kWh'),
        ('Tarifa', 'Tarifa', ' por kWh'),
        ('Costo', 'Costo Calculado', ''),
        ('Servicios BIA', 'Servicios BIA', ''),
        ('Otros cobros', 'Otros Cobros', ''),
        ('Energía Solar', 'Energía Solar', ''),
        ('Intereses', 'Intereses', ''),
        ('Retenciones', 'Retenciones', ''),
        ('Total de la Factura', 'Total Factura', '')
    ]
    
    for clave, nombre, unidad in campos:
        valor = datos.get(clave)
        if valor:
            print(f" {nombre}: {valor}{unidad}")
        else:
            print(f"{nombre}: No encontrado")

def main():
    pdf_path = "BIA_Test.pdf"  
    
    print("Procesando factura BIA...")
    extracted_data = extract_invoice_data(pdf_path)
    
    if extracted_data:
        print("=== DATOS EXTRAÍDOS DE LA FACTURA ===")
        for key, value in extracted_data.items():
            print(f"{key}: {value}")
        
        mostrar_resultados(extracted_data)
        
        archivo_csv = exportar_a_csv(extracted_data, pdf_path)
            
    else:
        print("No se pudieron extraer los datos del PDF")

if __name__ == "__main__":
    main()