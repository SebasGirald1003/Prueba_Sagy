import easyocr
from pdf2image import convert_from_path
import numpy as np
import re
import os
import csv
from datetime import datetime

pdf_path = "AIRE_Test.pdf"

def limpiar_numero(n):
    if not n:
        return None
    n = re.sub(r'[^0-9\.,-]*', '', n)
    n = n.replace(".", "")
    n = n.replace(",", ".")
    return float(n)

def buscar_valor_decimal(texto, etiqueta, grupo=1):
    patron = rf"{etiqueta}" + r".*?[\d\.]+[,\.]\d+" * (grupo - 1) + r".*?([\d\.]+[,\.]\d+)"
    m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
    return limpiar_numero(m.group(1)) if m else None

def buscar_costo(texto):
    patron = r"Consumo activa.*?[\d\.]+[,\.]\d+.*?[\d\.]+[,\.]\d+.*?\s*[\$]?\s*([\d\.\,]+)"
    m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
    if m:
        valor = m.group(1)
        clean_len = len(valor.replace('.', '').replace(',', '').replace('$', ''))
        if clean_len > 9:
            return limpiar_numero(valor[1:])
        return limpiar_numero(valor)
    return None

def buscar_valor_con_salto(texto, etiqueta, req_len):
    patron = rf"{etiqueta}.*?\$?\s*([\d\.\,]+)"
    m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)

    if m:
        valor = m.group(1)
        clean_val = valor.replace('.', '').replace(',', '').replace('$', '')
        clean_len = len(clean_val)
        if clean_len > req_len:
            return limpiar_numero(valor[1:])
        return limpiar_numero(valor)
    return None

def buscar_total_entero(texto, etiqueta):
    patron = rf"{etiqueta}.*?\$?\s*([^0-9\.\,]*)([\d\.\,]+)"
    m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
    return limpiar_numero(m.group(2)) if m and len(m.groups()) >= 2 else None

def exportar_a_csv(datos, pdf_path, csv_filename="AIRE_facturas.csv"):
    """
    Exporta los datos extraídos a un archivo CSV
    """
    csv_data = {
        'Fecha_Extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Archivo_PDF': os.path.basename(pdf_path),
        'Consumo': datos.get('Consumo', 'No encontrado'),
        'Tarifa': datos.get('Tarifa', 'No encontrado'),
        'Costo': datos.get('Costo', 'No encontrado'),
        'Contribucion_Activa': datos.get('Contribucion_Activa', 'No encontrado'),
        'Total_Energia': datos.get('Total_Energia', 'No encontrado'),
        'Tasa_Seguridad': datos.get('Tasa_Seguridad', 'No encontrado'),
        'Total_Mes': datos.get('Total_Mes', 'No encontrado')
    }
    
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Fecha_Extraccion', 'Archivo_PDF', 'Consumo', 'Tarifa', 
            'Costo', 'Contribucion_Activa', 'Total_Energia', 'Tasa_Seguridad', 'Total_Mes'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(csv_data)
    
    print(f"Resultados exportados a: {csv_filename}")
    return csv_filename

def mostrar_resultados(datos):
    """
    Muestra los resultados de forma organizada en consola
    """
    print("\n" + "="*60)
    print("FACTURA AIRE - DATOS EXTRAÍDOS")
    print("="*60)
    
    campos = [
        ('Consumo', 'Consumo', ''),
        ('Tarifa', 'Tarifa', ''),
        ('Costo', 'Costo', ''),
        ('Contribucion_Activa', 'Contribución Activa', ''),
        ('Total_Energia', 'Total Energía', ''),
        ('Tasa_Seguridad', 'Tasa Seguridad', ''),
        ('Total_Mes', 'Total Mes', '')
    ]
    
    for clave, nombre, unidad in campos:
        valor = datos.get(clave)
        if valor is not None:
            print(f"{nombre}: {valor:,.2f}{unidad}")
        else:
            print(f"{nombre}: No encontrado")

def procesar_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: Archivo no encontrado: {pdf_path}")
        return None

    print("Convirtiendo PDF a imágenes...")
    paginas = convert_from_path(pdf_path, dpi=300)

    reader = easyocr.Reader(['es'], gpu=False)
    texto_total = ""

    print("Realizando OCR...")
    for img in paginas:
        img_np = np.array(img)
        resultado = reader.readtext(img_np, detail=0)
        texto_total += "\n".join(resultado) + "\n"

    return texto_total

def main():
    texto_extraido = procesar_pdf(pdf_path)

    if texto_extraido:

        datos = {
            "Consumo": buscar_valor_decimal(texto_extraido, "Consumo activa", grupo=2),
            "Tarifa": buscar_valor_decimal(texto_extraido, "Consumo activa", grupo=1),

            "Costo": buscar_costo(texto_extraido),

            "Contribucion_Activa": buscar_valor_con_salto(texto_extraido, "Contribución Activa", req_len=7),

            "Total_Energia": None,

            "Tasa_Seguridad": buscar_total_entero(texto_extraido, "Tasa Seguridad"),

            "Total_Mes": buscar_valor_con_salto(texto_extraido, "Total Mes", req_len=8),
        }

        try:
            datos["Total_Energia"] = datos["Costo"] + datos["Contribucion_Activa"]
            datos["Total_Energia"] = round(datos["Total_Energia"])  
        except:
            datos["Total_Energia"] = None

        try:
            valor = int(datos["Tasa_Seguridad"])
            if valor > 9_000_000:
                datos["Tasa_Seguridad"] = float(str(valor)[1:])
        except:
            pass

        print("\n========== RESULTADO FINAL ==========\n")
        print(datos)
        print("\n=====================================\n")

        mostrar_resultados(datos)
        
        archivo_csv = exportar_a_csv(datos, pdf_path)
        

    else:
        print("No se pudo procesar el PDF.")

if __name__ == "__main__":
    main()