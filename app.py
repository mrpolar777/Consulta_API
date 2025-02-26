import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Configuração da API
API_BASE_URL = "https://teresinagps.rastrosystem.com.br/api_v2"
HEADERS = {"Content-Type": "application/json"}

# Função para realizar login
def login(username, password):
    url = f"{API_BASE_URL}/login/"
    data = {"login": username, "senha": password, "app": 4}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get("token")
    return None

# Função para obter a lista de veículos
def get_vehicles(user_id, token):
    url = f"{API_BASE_URL}/veiculos/{user_id}/"
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json().get("dispositivos", [])

# Função para obter o histórico de um veículo
def get_vehicle_history(vehicle_id, date, token):
    url = f"{API_BASE_URL}/veiculo/historico/"
    data = {
        "data": date,
        "hora_fim": "23:59:00",
        "hora_ini": "00:00:00",
        "veiculo": vehicle_id
    }
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response.json().get("veiculos", [])

# Gerar relatório em DataFrame com a coluna de Ignição atualizada
def generate_report(user_id, date, token, preco_combustivel, consumo_medio):
    vehicles = get_vehicles(user_id, token)
    report_data = []
    
    for vehicle in vehicles:
        vehicle_id = vehicle.get("veiculo_id")
        history = get_vehicle_history(vehicle_id, date, token)
        
        for entry in history:
            km_rodado = float(entry.get("velocidade", "0"))  # Supondo que seja a distância percorrida
            consumo_litros = km_rodado / consumo_medio if consumo_medio > 0 else 0
            valor_gasto = consumo_litros * preco_combustivel
            
            # Verifica o status de ignição e converte para "ligado" ou "desligado"
            ignition = entry.get("ignition")
            status_ignicao = "ligado" if ignition else "desligado"

            report_data.append({
                "Nome do Veículo": entry.get("name"),
                "Kilometragem": km_rodado,
                "Consumo por L": round(consumo_litros, 2),
                "Valor Gasto": round(valor_gasto, 2),
                "Latitude": entry.get("latitude"),
                "Longitude": entry.get("longitude"),
                "Data e Hora": entry.get("server_time"),
                "Ignição": status_ignicao
            })
    
    df = pd.DataFrame(report_data)
    return df

# Interface Streamlit
st.title("Relatório de Veículos")

# Inicializa session_state para o token
if "token" not in st.session_state:
    st.session_state.token = None

# Campos de login
username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")
if st.button("Login"):
    token = login(username, password)
    if token:
        st.session_state.token = token
        st.success("Login realizado com sucesso!")
    else:
        st.error("Falha no login. Verifique suas credenciais.")

# Verifica se o usuário está autenticado
if st.session_state.token:
    report_date = st.date_input("Selecione a Data do Relatório").strftime('%d/%m/%Y')
    
    # Inputs para preço do combustível e consumo médio
    preco_combustivel = st.number_input("Preço do Combustível (R$/L)", min_value=0.0, value=5.50, step=0.1)
    consumo_medio = st.number_input("Consumo Médio do Veículo (Km/L)", min_value=0.1, value=10.0, step=0.1)
    
    if st.button("Gerar Relatório"):
        df = generate_report(2044, report_date, st.session_state.token, preco_combustivel, consumo_medio)
        st.write("### Relatório Gerado")
        st.dataframe(df)

        # Criar botão para baixar CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Baixar CSV", data=csv_data, file_name="relatorio_veiculos.csv", mime="text/csv")
