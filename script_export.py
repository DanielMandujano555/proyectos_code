import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from dateutil.relativedelta import relativedelta
from unidecode import unidecode
import hubspot
import time
from dateutil import parser
from pprint import pprint
from hubspot.crm.contacts import PublicObjectSearchRequest, ApiException
from google.oauth2 import service_account
import gspread

# Autenticación con Google Drive
def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service-account-file.json'  # Ruta al archivo JSON de tus credenciales

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(credentials)

# Guardar el DataFrame en un archivo Excel en Google Drive
def save_to_drive(df, filename):
    gc = authenticate_google_drive()
    sh = gc.open_by_key('1fe1-7213tl_6fezmAwWf3O2b8SdMuwlH')  # ID de tu Google Sheet
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

# Configuración del cliente de HubSpot
apikey = "pat-na1-b6f1defa-7ddb-410c-9dd5-911fa8a5c22e"
api_client = hubspot.Client.create(access_token=apikey)

# Función para sumar meses a una fecha
def sum_date(codmes, months):
    temp = datetime.strptime(codmes, '%Y%m') + relativedelta(months=months)
    return datetime.strftime(temp, '%Y%m')

# Obtener datos de negocios de HubSpot
after = 0
deals_results = []
while True:
    public_object_search_request = PublicObjectSearchRequest(
        properties=[
            "hs_object_id",  # ID del objeto negocio
            "dealname",  # Nombre del negocio
            "dealstage",  # Etapa del negocio
            "hubspot_owner_id",
            'area__m2_',
            'amount'
        ], limit=50, after=after
    )
    try:
        api_response = api_client.crm.deals.search_api.do_search(public_object_search_request=public_object_search_request)
        deals_result = api_response
        deals_results.extend(deals_result.results)
        if not deals_result.paging:
            break
        after = deals_result.paging.next.after
    except ApiException as e:
        print("Exception when calling search_api->do_search: %s\n" % e)
    time.sleep(0.15)

# Convertir los resultados en un DataFrame de pandas
deals_data = []
for deal in deals_results:
    deal_info = {
        "hs_object_id": deal.properties.get("hs_object_id", ""),
        "dealname": deal.properties.get("dealname", ""),
        "dealstage": deal.properties.get("dealstage", ""),
        "hubspot_owner_id": deal.properties.get("hubspot_owner_id", ""),
        "area__m2_": deal.properties.get("area__m2_", ""),
        "amount": deal.properties.get("amount", "")
    }
    deals_data.append(deal_info)

df = pd.DataFrame(deals_data)

# Guardar el DataFrame en Google Drive
save_to_drive(df, 'Identidad_Visual.xlsx')
