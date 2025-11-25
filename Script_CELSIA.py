import re
import PyPDF2
import csv
import os
from datetime import datetime

def extraer_datos_celsia(pdf_path):
    # Extraer texto del PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        texto_completo = ""
        for page in reader.pages:
            texto_completo += page.extract_text()
    
    datos = {}
    
    print(" Analizando factura CELSIA...")
    
    # 1. Extraer CONSUMO - Buscar diferencia entre lecturas del medidor
    patron_energia = r'Energia Activa\s+(\d+)\s+(\d+)\s+\d+\s+\d+'
    match_energia = re.search(patron_energia, texto_completo)
    if match_energia:
        lectura_actual = int(match_energia.group(1))
        lectura_anterior = int(match_energia.group(2))
        datos['Consumo'] = lectura_actual - lectura_anterior
    
    # 2. Extraer TARIFA - Buscar después de las lecturas
    patron_tarifa = r'Energia Activa\s+\d+\s+\d+\s+\d+\s+\d+\s*\$?(\d+\.\d+)'
    match_tarifa = re.search(patron_tarifa, texto_completo)
    if match_tarifa:
        datos['Tarifa'] = float(match_tarifa.group(1))
    
    # 3. Extraer VALOR OTROS - Buscar en la sección de otros conceptos
    # Buscar después de "OTROS CONCEPTOS" el primer valor grande con formato $xxx,xxx
    patron_otros = r'OTROS CONCEPTOS[^$]*\$(\d{1,3}(?:,\d{3})+)'
    match_otros = re.search(patron_otros, texto_completo, re.IGNORECASE | re.DOTALL)
    if match_otros:
        valor_str = match_otros.group(1).replace(',', '')
        datos['Valor Otros'] = float(valor_str)
    else:
        # Buscar cualquier valor grande con formato $xxx,xxx cerca de "OTROS"
        patron_otros_alt = r'\$(\d{1,3}(?:,\d{3})+)[^$]*OTROS'
        match_otros_alt = re.search(patron_otros_alt, texto_completo, re.IGNORECASE | re.DOTALL)
        if match_otros_alt:
            valor_str = match_otros_alt.group(1).replace(',', '')
            datos['Valor Otros'] = float(valor_str)
    
    # 4. Extraer TOTAL FACTURA - Buscar después de "TOTAL A PAGAR"
    patron_total = r'TOTAL\s*A\s*PAGAR[^$]*\$(\d{1,3}(?:,\d{3})+)'
    match_total = re.search(patron_total, texto_completo, re.IGNORECASE | re.DOTALL)
    if match_total:
        total_str = match_total.group(1).replace(',', '')
        datos['Total Factura'] = float(total_str)

    else:
        # Buscar en la tabla final el valor más grande
        patron_total_alt = r'\$(\d{3},\d{3})(?![^$]*\d{4})'  # Busca patrones $xxx,xxx que no tengan más de 6 dígitos
        matches_total = re.findall(patron_total_alt, texto_completo)
        if matches_total:
            # Tomar el valor más grande
            valores = [float(valor.replace(',', '')) for valor in matches_total]
            datos['Total Factura'] = max(valores)
    
    # 5. Calcular COSTO
    if 'Consumo' in datos and 'Tarifa' in datos:
        datos['Costo'] = datos['Consumo'] * datos['Tarifa']
    
    return datos

def mostrar_resultados(datos):
    print("\n" + "="*50)
    print("FACTURA CELSIA - DATOS EXTRAÍDOS")
    print("="*50)
    
    if 'Consumo' in datos:
        print(f" Consumo: {datos['Consumo']} kWh")
    else:
        print(" Consumo: No encontrado")
    
    if 'Tarifa' in datos:
        print(f"Tarifa: ${datos['Tarifa']:,.2f} por kWh")
    else:
        print(" Tarifa: No encontrada")
    
    if 'Costo' in datos:
        print(f"Costo (Consumo × Tarifa): ${datos['Costo']:,.0f}")
    else:
        print(" Costo: No se pudo calcular")
    
    if 'Valor Otros' in datos:
        print(f"Valor Otros: ${datos['Valor Otros']:,.0f}")
    else:
        print("Valor Otros: No encontrado")
    
    if 'Total Factura' in datos:
        print(f"Total Factura: ${datos['Total Factura']:,.0f}")
    else:
        print(" Total Factura: No encontrado")

def exportar_a_csv(datos, csv_filename="celsia_facturas.csv"):
    csv_data = {
        'Consumo_kWh': datos.get('Consumo', 'No encontrado'),
        'Tarifa_por_kWh': datos.get('Tarifa', 'No encontrado'),
        'Costo_Calculado': datos.get('Costo', 'No encontrado'),
        'Valor_Otros': datos.get('Valor Otros', 'No encontrado'),
        'Total_Factura': datos.get('Total Factura', 'No encontrado'),
        'Fecha_Extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Archivo_PDF': os.path.basename(pdf_path)
    }
    
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Fecha_Extraccion', 'Archivo_PDF', 'Consumo_kWh', 'Tarifa_por_kWh', 
                     'Costo_Calculado', 'Valor_Otros', 'Total_Factura']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(csv_data)
    
    print(f"\nResultados exportados a: {csv_filename}")
    return csv_filename

if __name__ == "__main__":
    pdf_path = "CELSIA_Test.pdf"
    
    try:

        datos = extraer_datos_celsia(pdf_path)
        mostrar_resultados(datos)
        
        archivo_csv = exportar_a_csv(datos)
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {pdf_path}")
    except Exception as e:
        print(f"Error: {str(e)}")