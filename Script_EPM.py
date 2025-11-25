import re
import numpy as np
import easyocr
from pdf2image import convert_from_path
import csv
import os
from datetime import datetime

def extraer_datos_factura_epm(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    reader = easyocr.Reader(['es'])

    texto = ""
    for page in pages:
        img_np = np.array(page)
        ocr_text = reader.readtext(img_np, detail=0)
        texto += " ".join(ocr_text).lower() + " "

    def buscar(patron):
        m = re.search(patron, texto)
        return m.group(1) if m else None

    consumo_acu = buscar(r"567\s+561\s+(\d+)\s*m[:]?")
    tarifa_acu = buscar(r"consumo\s+may-\d{2}\s+([\d\.\,]+)")
    costo_acu = buscar(r"acueducto\s+6\s*m3\s*\$?\s*([\d\.\,]+)")

    consumos = re.findall(r"consumo\s+may-\d{2}\s+([\d\.\,]+)", texto)
    tarifas = re.findall(r"consumo\s+may-\d{2}\s+([\d\.\,]+)", texto)

    consumo_alc = buscar(r"consumo\s+(\d+)\s*m[:]?")
    tarifa_alc = tarifas[1] if len(tarifas) > 1 else None
    costo_alc = buscar(r"total alcantarillado\s*\$?\s*([\d\.\,]+)")

    consumo_ene = buscar(r"([\d\.\,]+)\s*kwh")
    tarifa_ene = buscar(r"energía\s+may-\d{2}\s+[\d\.\,]+\s+([\d\.\,]+)")
    costo_ene = buscar(r"total energía\s*\$?\s*([\d\.\,]+)")

    otras = buscar(r"total otras entidades\s*\$?\s*([\d\.\,]+)")

    def to_number(x):
        if not x:
            return 0
        return float(x.replace(".", "").replace(",", "."))

    total_general = (
        to_number(costo_acu) +
        to_number(costo_alc) +
        to_number(costo_ene) +
        to_number(otras)
    )

    total_general = f"{total_general:,.0f}".replace(",", ".")

    return {
        "acueducto": {
            "consumo": consumo_acu,
            "tarifa": tarifa_acu,
            "costo": costo_acu
        },
        "alcantarillado": {
            "consumo": consumo_alc,
            "tarifa": tarifa_alc,
            "costo": costo_alc
        },
        "energia": {
            "consumo": consumo_ene,
            "tarifa": tarifa_ene,
            "costo": costo_ene
        },
        "otras_entidades": otras,
        "total_general": total_general
    }

def exportar_epm_a_csv(datos, pdf_filename, output_file='epm_facturas.csv'):
    """
    Exporta los datos de EPM a un archivo CSV
    """
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Archivo', 
            'Fecha_Extraccion',
            'Acueducto_Consumo',
            'Acueducto_Tarifa', 
            'Acueducto_Costo',
            'Alcantarillado_Consumo',
            'Alcantarillado_Tarifa',
            'Alcantarillado_Costo',
            'Energia_Consumo',
            'Energia_Tarifa',
            'Energia_Costo',
            'Otras_Entidades',
            'Total_General'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'Archivo': pdf_filename,
            'Fecha_Extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Acueducto_Consumo': datos['acueducto']['consumo'] or '',
            'Acueducto_Tarifa': datos['acueducto']['tarifa'] or '',
            'Acueducto_Costo': datos['acueducto']['costo'] or '',
            'Alcantarillado_Consumo': datos['alcantarillado']['consumo'] or '',
            'Alcantarillado_Tarifa': datos['alcantarillado']['tarifa'] or '',
            'Alcantarillado_Costo': datos['alcantarillado']['costo'] or '',
            'Energia_Consumo': datos['energia']['consumo'] or '',
            'Energia_Tarifa': datos['energia']['tarifa'] or '',
            'Energia_Costo': datos['energia']['costo'] or '',
            'Otras_Entidades': datos['otras_entidades'] or '',
            'Total_General': datos['total_general'] or ''
        })

def mostrar_resultados_epm(datos):
    """
    Muestra los resultados de forma organizada
    """
    print("=== RESULTADOS FACTURA EPM ===")
    
    print("\n--- ACUEDUCTO ---")
    if datos['acueducto']['consumo']:
        print(f"Consumo: {datos['acueducto']['consumo']} m³")
    if datos['acueducto']['tarifa']:
        print(f"Tarifa: ${datos['acueducto']['tarifa']}")
    if datos['acueducto']['costo']:
        print(f"Costo: ${datos['acueducto']['costo']}")
    
    print("\n--- ALCANTARILLADO ---")
    if datos['alcantarillado']['consumo']:
        print(f"Consumo: {datos['alcantarillado']['consumo']} m³")
    if datos['alcantarillado']['tarifa']:
        print(f"Tarifa: ${datos['alcantarillado']['tarifa']}")
    if datos['alcantarillado']['costo']:
        print(f"Costo: ${datos['alcantarillado']['costo']}")
    
    print("\n--- ENERGÍA ---")
    if datos['energia']['consumo']:
        print(f"Consumo: {datos['energia']['consumo']} kWh")
    if datos['energia']['tarifa']:
        print(f"Tarifa: ${datos['energia']['tarifa']}")
    if datos['energia']['costo']:
        print(f"Costo: ${datos['energia']['costo']}")
    
    print("\n--- OTROS ---")
    if datos['otras_entidades']:
        print(f"Otras entidades: ${datos['otras_entidades']}")
    
    print("\n--- TOTAL ---")
    if datos['total_general']:
        print(f"Total general: ${datos['total_general']}")

def main():
    pdf_path = 'EPM_Test.pdf'  
    
    try:
        print("Procesando factura EPM...")
        datos = extraer_datos_factura_epm(pdf_path)
        
        mostrar_resultados_epm(datos)
        
        pdf_filename = os.path.basename(pdf_path)
        exportar_epm_a_csv(datos, pdf_filename)
        print(f"\n✓ Datos exportados a: epm_facturas.csv")
        
    except Exception as e:
        print(f"Error al procesar la factura: {e}")

if __name__ == "__main__":
    main()