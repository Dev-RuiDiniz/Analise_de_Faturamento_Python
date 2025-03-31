import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Análise de Faturamento",
    page_icon="📊",
    layout="wide"
)

# Título do aplicativo
st.title("📊 Análise de Faturamento Mensal")

# Carregar dados
@st.cache_data
def load_data():
    try:
        # Tenta carregar de um arquivo CSV
        data = pd.read_csv("data/faturamento.csv", parse_dates=["Data"])
    except:
        try:
            # Se não encontrar CSV, tenta carregar de Excel
            data = pd.read_excel("data/faturamento.xlsx", parse_dates=["Data"])
        except:
            # Se não encontrar dados, cria um dataframe vazio
            data = pd.DataFrame(columns=["Data", "Faturamento", "Custo", "Clientes"])
    
    # Garante que temos colunas necessárias
    if not all(col in data.columns for col in ["Data", "Faturamento"]):
        if not data.empty:
            st.error("O arquivo de dados não tem o formato esperado. Deve conter colunas 'Data' e 'Faturamento'.")
        data = pd.DataFrame(columns=["Data", "Faturamento", "Custo", "Clientes"])
    
    return data

df = load_data()

# Sidebar para upload e configurações
with st.sidebar:
    st.header("Configurações")
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "Carregar arquivo de faturamento (CSV ou Excel)",
        type=["csv", "xlsx"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                new_data = pd.read_csv(uploaded_file, parse_dates=["Data"])
            else:
                new_data = pd.read_excel(uploaded_file, parse_dates=["Data"])
            
            if all(col in new_data.columns for col in ["Data", "Faturamento"]):
                df = new_data
                st.success("Dados carregados com sucesso!")
            else:
                st.error("O arquivo não contém as colunas necessárias ('Data' e 'Faturamento').")
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
    
    # Filtros
    st.header("Filtros")
    if not df.empty:
        min_date = df["Data"].min()
        max_date = df["Data"].max()
        
        date_range = st.date_input(
            "Período de análise",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["Data"] >= pd.to_datetime(start_date)) & 
                    (df["Data"] <= pd.to_datetime(end_date))]
        else:
            st.warning("Selecione um intervalo de datas válido.")

# Seção principal
if df.empty:
    st.warning("Nenhum dado disponível. Carregue um arquivo com dados de faturamento.")
else:
    # Métricas resumidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Período analisado", f"{len(df)} meses")
    with col2:
        total = df["Faturamento"].sum()
        st.metric("Faturamento total", f"R$ {total:,.2f}")
    with col3:
        avg = df["Faturamento"].mean()
        st.metric("Média mensal", f"R$ {avg:,.2f}")

    # Gráfico de evolução do faturamento
    st.subheader("Evolução do Faturamento")
    fig = px.line(
        df, 
        x="Data", 
        y="Faturamento",
        title="Faturamento Mensal",
        markers=True
    )
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Faturamento (R$)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Análise comparativa
    st.subheader("Análise Comparativa")
    
    # Adiciona colunas de mês e ano para análise
    df["Ano"] = df["Data"].dt.year
    df["Mês"] = df["Data"].dt.month
    
    # Comparação anual
    annual_comparison = df.groupby("Ano")["Faturamento"].sum().reset_index()
    fig_annual = px.bar(
        annual_comparison,
        x="Ano",
        y="Faturamento",
        title="Comparação Anual de Faturamento",
        text_auto=True
    )
    fig_annual.update_layout(
        xaxis_title="Ano",
        yaxis_title="Faturamento Total (R$)"
    )
    st.plotly_chart(fig_annual, use_container_width=True)

    # Comparação mensal (média por mês)
    monthly_avg = df.groupby("Mês")["Faturamento"].mean().reset_index()
    fig_monthly = px.bar(
        monthly_avg,
        x="Mês",
        y="Faturamento",
        title="Média de Faturamento por Mês",
        text_auto=True
    )
    fig_monthly.update_layout(
        xaxis_title="Mês",
        yaxis_title="Faturamento Médio (R$)"
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Tabela com dados detalhados
    st.subheader("Dados Detalhados")
    st.dataframe(df.sort_values("Data", ascending=False), use_container_width=True)

    # Opção para exportar dados
    st.download_button(
        label="Exportar dados como CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="faturamento_analisado.csv",
        mime="text/csv"
    )