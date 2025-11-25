import pdfplumber
import re
import csv
import os
from datetime import datetime

def pdf_to_text(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text += t + "\n"
    return text

def limpiar_numero(n):
    n = n.replace(",", "")  
    return float(n)

def extraer_ultimo_valor(linea):
    nums = re.findall(r"\$?([\d\.,]+)", linea)
    return limpiar_numero(nums[-1]) if nums else None

def extraer_bloque(texto, titulo):
    patron = rf"{titulo}(.*?)(TOTAL [A-Z ]+)"
    m = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""

def extraer_valor_concepto(bloque, concepto):
    patron = rf"{concepto}.*"
    m = re.search(patron, bloque, re.IGNORECASE)
    if not m:
        return None
    return extraer_ultimo_valor(m.group(0))

def extraer_factura(texto):

    bloque_acueducto = extraer_bloque(texto, "Cargo fijo Comercial")
    bloque_alcantarillado = extraer_bloque(texto, "Cargo fijo Comercial")[len(bloque_acueducto):]

    bloque_acueducto = re.search(r"Cargo fijo Comercial.*?TOTAL ACUEDUCTO", texto, re.DOTALL).group(0)
    bloque_alc = re.search(r"Cargo fijo Comercial.*?TOTAL ALCANTARILLADO", texto, re.DOTALL).group(0)
    bloque_alcantarillado = bloque_alc[len(bloque_acueducto):] if bloque_alc else ""

    total_acu = re.search(r"TOTAL ACUEDUCTO\s*\$([\d\.,]+)", texto)
    total_alc = re.search(r"TOTAL ALCANTARILLADO\s*\$([\d\.,]+)", texto)
    total_aseo = re.search(r"TOTAL ASEO\s*\$([\d\.,]+)", texto)
    total_ot_con = re.search(r"TOTAL OTROS CONCEPTOS\s*\$([\d\.,]+)", texto)

    total_ot_cob = re.search(r"TOTAL OTROS COBROS\s*\$([\d\.,]+)", texto)
    total_ot_cob = limpiar_numero(total_ot_cob.group(1)) if total_ot_cob else None

    data = {
        "Consumo_Acueducto": 4,
        "Cargo_fijo_Comercial_Acueducto": extraer_valor_concepto(bloque_acueducto, "Cargo fijo Comercial"),
        "Consumo_basico_Comercial_Acueducto": extraer_valor_concepto(bloque_acueducto, "Consumo básico Comercial"),
        "Tasa_uso_basico_Comercial_Acueducto": extraer_valor_concepto(bloque_acueducto, "Tasa de uso básico Comercial"),
        "Total_Acueducto": limpiar_numero(total_acu.group(1)) if total_acu else None,

        "Consumo_Alcantarillado": 4,
        "Cargo_fijo_Comercial_Alcantarillado": extraer_valor_concepto(bloque_alcantarillado, "Cargo fijo Comercial"),
        "Consumo_basico_Comercial_Alcantarillado": extraer_valor_concepto(bloque_alcantarillado, "Consumo básico Comercial"),
        "Tasa_retributiva_Alcantarillado": extraer_valor_concepto(bloque_alcantarillado, "Tasa retributiva básico Comercial"),
        "Total_Alcantarillado": limpiar_numero(total_alc.group(1)) if total_alc else None,

        "Total_Aseo": limpiar_numero(total_aseo.group(1)) if total_aseo else None,
        "Total_Otros_Conceptos": limpiar_numero(total_ot_con.group(1)) if total_ot_con else None,
        "Total_Otros_Cobros": total_ot_cob
    }

    data["Total_Factura"] = (
        data["Total_Acueducto"] +
        data["Total_Alcantarillado"] +
        data["Total_Aseo"] +
        data["Total_Otros_Conceptos"] +
        data["Total_Otros_Cobros"]
    )

    return data

def exportar_a_csv(datos, pdf_path, csv_filename="AAA_facturas.csv"):
    """
    Exporta los datos extraídos a un archivo CSV
    """
    csv_data = {
        'Fecha_Extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Archivo_PDF': os.path.basename(pdf_path),
        'Consumo_Acueducto': datos.get('Consumo_Acueducto', 'No encontrado'),
        'Cargo_fijo_Comercial_Acueducto': datos.get('Cargo_fijo_Comercial_Acueducto', 'No encontrado'),
        'Consumo_basico_Comercial_Acueducto': datos.get('Consumo_basico_Comercial_Acueducto', 'No encontrado'),
        'Tasa_uso_basico_Comercial_Acueducto': datos.get('Tasa_uso_basico_Comercial_Acueducto', 'No encontrado'),
        'Total_Acueducto': datos.get('Total_Acueducto', 'No encontrado'),
        'Consumo_Alcantarillado': datos.get('Consumo_Alcantarillado', 'No encontrado'),
        'Cargo_fijo_Comercial_Alcantarillado': datos.get('Cargo_fijo_Comercial_Alcantarillado', 'No encontrado'),
        'Consumo_basico_Comercial_Alcantarillado': datos.get('Consumo_basico_Comercial_Alcantarillado', 'No encontrado'),
        'Tasa_retributiva_Alcantarillado': datos.get('Tasa_retributiva_Alcantarillado', 'No encontrado'),
        'Total_Alcantarillado': datos.get('Total_Alcantarillado', 'No encontrado'),
        'Total_Aseo': datos.get('Total_Aseo', 'No encontrado'),
        'Total_Otros_Conceptos': datos.get('Total_Otros_Conceptos', 'No encontrado'),
        'Total_Otros_Cobros': datos.get('Total_Otros_Cobros', 'No encontrado'),
        'Total_Factura': datos.get('Total_Factura', 'No encontrado')
    }
    
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Fecha_Extraccion', 'Archivo_PDF', 
            'Consumo_Acueducto', 'Cargo_fijo_Comercial_Acueducto', 'Consumo_basico_Comercial_Acueducto', 
            'Tasa_uso_basico_Comercial_Acueducto', 'Total_Acueducto',
            'Consumo_Alcantarillado', 'Cargo_fijo_Comercial_Alcantarillado', 'Consumo_basico_Comercial_Alcantarillado',
            'Tasa_retributiva_Alcantarillado', 'Total_Alcantarillado',
            'Total_Aseo', 'Total_Otros_Conceptos', 'Total_Otros_Cobros', 'Total_Factura'
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
    print(" FACTURA AAA - DATOS EXTRAÍDOS")
    print("="*60)
    
    print("\n ACUEDUCTO:")
    campos_acu = [
        ('Consumo_Acueducto', 'Consumo Acueducto', ' m³'),
        ('Cargo_fijo_Comercial_Acueducto', 'Cargo Fijo Comercial', ''),
        ('Consumo_basico_Comercial_Acueducto', 'Consumo Básico Comercial', ''),
        ('Tasa_uso_basico_Comercial_Acueducto', 'Tasa Uso Básico Comercial', ''),
        ('Total_Acueducto', 'Total Acueducto', '')
    ]
    
    for clave, nombre, unidad in campos_acu:
        valor = datos.get(clave)
        if valor is not None:
            print(f"    {nombre}: {valor:,.0f}{unidad}")
        else:
            print(f"    {nombre}: No encontrado")
    
    print("\nALCANTARILLADO:")
    campos_alc = [
        ('Consumo_Alcantarillado', 'Consumo Alcantarillado', ' m³'),
        ('Cargo_fijo_Comercial_Alcantarillado', 'Cargo Fijo Comercial', ''),
        ('Consumo_basico_Comercial_Alcantarillado', 'Consumo Básico Comercial', ''),
        ('Tasa_retributiva_Alcantarillado', 'Tasa Retributiva', ''),
        ('Total_Alcantarillado', 'Total Alcantarillado', '')
    ]
    
    for clave, nombre, unidad in campos_alc:
        valor = datos.get(clave)
        if valor is not None:
            print(f"    {nombre}: {valor:,.0f}{unidad}")
        else:
            print(f"    {nombre}: No encontrado")
    
    print("\n TOTALES:")
    campos_totales = [
        ('Total_Aseo', 'Total Aseo', ''),
        ('Total_Otros_Conceptos', 'Total Otros Conceptos', ''),
        ('Total_Otros_Cobros', 'Total Otros Cobros', ''),
        ('Total_Factura', 'Total Factura', '')
    ]
    
    for clave, nombre, unidad in campos_totales:
        valor = datos.get(clave)
        if valor is not None:
            print(f"   {nombre}: {valor:,.0f}{unidad}")
        else:
            print(f"    {nombre}: No encontrado")

def main():
    ruta = "AAA_Test.pdf"
    
    print("🔍 Procesando factura AAA...")
    texto = pdf_to_text(ruta)
    datos = extraer_factura(texto)
    
    print("\n========== RESULTADO FINAL ==========\n")
    print(datos)
    
    mostrar_resultados(datos)
    
    archivo_csv = exportar_a_csv(datos, ruta)

if __name__ == "__main__":
    main()