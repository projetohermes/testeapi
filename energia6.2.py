import pandas as pd
import requests
import json
import os

BASE_URL = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
RESOURCE_ID = "b1bd71e7-d0ad-4214-9053-cbd58e9564a7"
OUTPUT_DIRECTORY = "C:\\Estudo\\API_ONS\\finalEnergia" #Atenção mudar o local para segurança!

params = {"resource_id": RESOURCE_ID, "limit": 200000, "offset": 50000}
all_data = []

# Create a session for reusing the connection
with requests.Session() as session:
    # Loop to fetch data in pages
    while True:
        try:
            response = session.get(BASE_URL, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Erro ao buscar os dados: {e}")
            break

        data = response.json()["result"]["records"]

        if not data:  # Exit the loop if no more data
            break

        all_data.extend(data)
        params["offset"] += params["limit"]

# Create a DataFrame with the data
df = pd.DataFrame(all_data)

# Check if the required columns exist
if 'MdaPotenciaInstaladaKW' in df.columns:
    df['MdaPotenciaInstaladaKW'] = df['MdaPotenciaInstaladaKW'].str.replace(',', '.').astype(float)

if 'DthAtualizaCadastralEmpreend' in df.columns:
    # Convert DthAtualizaCadastralEmpreend to datetime and extract year and month
    df['DthAtualizaCadastralEmpreend'] = pd.to_datetime(df['DthAtualizaCadastralEmpreend'], errors='coerce')
    df['periodo'] = df['DthAtualizaCadastralEmpreend'].dt.to_period("M").astype(str)

# Aggregate and create the tables
# Table 1: Total of developments by class, state, and reference period
table1 = df.groupby(['DscClasseConsumo', 'SigUF', 'SigTipoGeracao', 'periodo']).size().reset_index(name='TotalEmpreendimentos')

# Table 2: Installed power by state, type of generation and reference period
if 'MdaPotenciaInstaladaKW' in df.columns:
    table2 = df.groupby(['SigUF', 'SigTipoGeracao', 'periodo'])['MdaPotenciaInstaladaKW'].sum().reset_index(name='PotenciaInstaladaKW')

# Sort the tables by reference period
table1 = table1.sort_values(by='periodo')
if 'MdaPotenciaInstaladaKW' in df.columns:
    table2 = table2.sort_values(by='periodo')

# Export data to JSON files
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

with open(os.path.join(OUTPUT_DIRECTORY, 'tabela1.json'), 'w', encoding='utf-8') as file:
    json.dump(table1.to_dict(orient='records'), file, ensure_ascii=False)

if 'MdaPotenciaInstaladaKW' in df.columns:
    with open(os.path.join(OUTPUT_DIRECTORY, 'tabela2.json'), 'w', encoding='utf-8') as file:
        json.dump(table2.to_dict(orient='records'), file, ensure_ascii=False)

# Export data to CSV files
table1.to_csv(os.path.join(OUTPUT_DIRECTORY, 'tabela1.csv'), index=False, encoding='utf-8')
if 'MdaPotenciaInstaladaKW' in df.columns:
    table2.to_csv(os.path.join(OUTPUT_DIRECTORY, 'tabela2.csv'), index=False, encoding='utf-8')
