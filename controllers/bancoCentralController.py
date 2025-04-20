# controllers/bancoCentralController.py

import requests
import xml.etree.ElementTree as ET
from html import unescape  # Para desescapar entidades HTML

# Configuración de la API del Banco Central
BCCR_ENDPOINT = 'https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx'
EMAIL = 'diego.jimenez.monge@hotmail.com'
TOKEN = 'OO41MNEIMI'

def get_exchange_rate(fecha_inicio, fecha_final, indicador="317", nombre="Mi Nombre", sub_niveles="N"):
    """
    Realiza una solicitud SOAP al API del Banco Central para obtener el tipo de cambio.
    """
    xml_data = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ObtenerIndicadoresEconomicosXML xmlns="http://ws.sdde.bccr.fi.cr">
      <Indicador>{indicador}</Indicador>
      <FechaInicio>{fecha_inicio}</FechaInicio>
      <FechaFinal>{fecha_final}</FechaFinal>
      <Nombre>{nombre}</Nombre>
      <SubNiveles>{sub_niveles}</SubNiveles>
      <CorreoElectronico>{EMAIL}</CorreoElectronico>
      <Token>{TOKEN}</Token>
    </ObtenerIndicadoresEconomicosXML>
  </soap:Body>
</soap:Envelope>'''

    headers = {
        'Content-Type': 'text/xml',
        'SOAPAction': 'http://ws.sdde.bccr.fi.cr/ObtenerIndicadoresEconomicosXML'
    }
    
    try:
        response = requests.post(BCCR_ENDPOINT, data=xml_data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return None, f"Error en la solicitud HTTP: {e}"

    try:
        # Imprime el XML completo para depuración
        xml_completo = response.content.decode('utf-8')
        print("Respuesta XML completa:")
        print(xml_completo)
        
        # Parsear la respuesta SOAP
        root = ET.fromstring(response.content)
        ns = {"ns": "http://ws.sdde.bccr.fi.cr"}
        result_elem = root.find(".//ns:ObtenerIndicadoresEconomicosXMLResult", ns)
        if result_elem is None or not result_elem.text:
            return None, "No se encontró el resultado en la respuesta."
        
        # Desescapar el XML contenido (convertir entidades HTML a sus caracteres)
        inner_xml = unescape(result_elem.text)
        
        # Parsear el XML interno
        inner_root = ET.fromstring(inner_xml)
        num_valor_elem = inner_root.find(".//NUM_VALOR")
        if num_valor_elem is None or not num_valor_elem.text:
            return None, "No se encontró el valor en la respuesta interna."
        
        return num_valor_elem.text.strip(), None
    except Exception as e:
        return None, f"Error al parsear la respuesta XML: {e}"

from datetime import datetime
from controllers.bancoCentralController import get_exchange_rate  # si lo tienes separado

def get_exchange_rates(fecha_inicio, fecha_final, nombre="Mi Nombre", sub_niveles="N"):
    """
    Obtiene el tipo de cambio de venta (indicador 317) y de compra (indicador 318)
    """
    # Convertir fechas a formato requerido por BCCR: dd/mm/yyyy
    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
        fecha_final = datetime.strptime(fecha_final, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError as e:
        return None, f"Formato de fecha inválido: {e}"

    # Obtener tipo de cambio
    venta, error_venta = get_exchange_rate(fecha_inicio, fecha_final, indicador="317", nombre=nombre, sub_niveles=sub_niveles)
    compra, error_compra = get_exchange_rate(fecha_inicio, fecha_final, indicador="318", nombre=nombre, sub_niveles=sub_niveles)
    
    if error_venta or error_compra:
        error_msg = error_venta if error_venta else error_compra
        return None, error_msg
    
    return {"venta": venta, "compra": compra}, None




