import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import time

# Configuração da página
st.set_page_config(
    page_title="Análise de Faturamento",
    page_icon="📊",
    layout="wide"
)

# Título do aplicativo
st.title("📊 Análise de Faturamento Mensal")

# Nome do arquivo de dados
DATA_FILE = "data/faturamento.csv"

# Função para carregar dados
def load_data():
    os.makedirs("data", exist_ok=True)
    try:
        data = pd.read_csv(DATA_FILE, parse_dates=["Data"])
    except:
        data = pd.DataFrame(columns=["Data", "Faturamento", "Custo", "Clientes"])
    
    if not all(col in data.columns for col in ["Data", "Faturamento", "Custo", "Clientes"]):
        if not data.empty:
            st.error("O arquivo de dados não tem o formato esperado.")
        data = pd.DataFrame(columns=["Data", "Faturamento", "Custo", "Clientes"])
    
    return data

def save_data(data):
    data.to_csv(DATA_FILE, index=False)

def format_currency(value):
    return f"R$ {value:,.2f}"

def create_plot(df, y_column, title, y_title):
    fig = px.line(
        df, 
        x="Data", 
        y=y_column,
        title=title,
        markers=True
    )
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title=y_title,
        hovermode="x unified"
    )
    return fig

# Cria abas principais
tab_analise, tab_atual, tab_comparacao, tab_dados = st.tabs([
    "📈 Análise Geral", 
    "📅 Ano Atual", 
    "🔄 Comparação Anual",
    "📝 Edição de Dados"
])

# Sidebar comum
with st.sidebar:
    st.header("Configurações")
    auto_refresh = st.checkbox("Atualização automática", value=True)
    refresh_interval = st.slider("Intervalo de atualização (segundos)", 1, 60, 5)
    
    st.header("Filtros Gerais")
    df = load_data()
    
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
            df_filtered = df[(df["Data"] >= pd.to_datetime(start_date)) & 
                             (df["Data"] <= pd.to_datetime(end_date))]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

# Função para análise básica
def render_basic_analysis(df, title):
    if df.empty:
        st.warning(f"Nenhum dado disponível para {title}")
        return
    
    # Calcula as métricas derivadas
    df["Lucro"] = df["Faturamento"] - df["Custo"]
    df["Margem"] = (df["Lucro"] / df["Faturamento"]) * 100
    df["Faturamento_por_Cliente"] = df["Faturamento"] / df["Clientes"]
    
    st.subheader(f"Indicadores Chave - {title}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Faturamento Total", format_currency(df["Faturamento"].sum()))
        st.metric("Média Mensal", format_currency(df["Faturamento"].mean()))
    with col2:
        st.metric("Custo Total", format_currency(df["Custo"].sum()))
        st.metric("Custo Médio", format_currency(df["Custo"].mean()))
    with col3:
        st.metric("Lucro Total", format_currency(df["Lucro"].sum()))
        st.metric("Margem Média", f"{df['Margem'].mean():.1f}%")
    with col4:
        st.metric("Total Clientes", f"{df['Clientes'].sum():,}")
        st.metric("Ticket Médio", format_currency(df["Faturamento_por_Cliente"].mean()))
    
    # Gráficos
    charts = [
        ("Faturamento", "Evolução do Faturamento"),
        ("Custo", "Evolução do Custo"),
        ("Lucro", "Evolução do Lucro"),
        ("Clientes", "Evolução de Clientes")
    ]
    
    for col, title_suffix in charts:
        fig = create_plot(df, col, f"{title_suffix} - {title}", col)
        st.plotly_chart(fig, use_container_width=True)

# ABA: ANÁLISE GERAL
with tab_analise:
    render_basic_analysis(df_filtered, "Período Selecionado")

# ABA: ANO ATUAL
with tab_atual:
    current_year = datetime.now().year
    df_current_year = df_filtered[df_filtered["Data"].dt.year == current_year]
    
    if df_current_year.empty:
        st.warning(f"Nenhum dado disponível para o ano atual ({current_year})")
    else:
        st.header(f"Análise do Ano Atual ({current_year})")
        render_basic_analysis(df_current_year, f"Ano {current_year}")
        
        # Análise mensal comparativa
        st.subheader("Comparativo Mensal")
        df_monthly = df_current_year.copy()
        df_monthly["Mês"] = df_monthly["Data"].dt.month_name(locale='pt_BR')
        
        fig = px.bar(
            df_monthly,
            x="Mês",
            y=["Faturamento", "Custo", "Lucro"],
            title=f"Comparativo Mensal - {current_year}",
            barmode="group",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

# ABA: COMPARAÇÃO ANUAL
with tab_comparacao:
    st.header("Comparação Ano a Ano")
    
    if df.empty:
        st.warning("Nenhum dado disponível para comparação")
    else:
        # Processamento dos dados anuais
        df_yearly = df_filtered.copy()
        df_yearly["Ano"] = df_yearly["Data"].dt.year
        
        # Garante que temos a coluna Lucro calculada antes de agrupar
        df_yearly["Lucro"] = df_yearly["Faturamento"] - df_yearly["Custo"]
        
        df_yearly = df_yearly.groupby("Ano").agg({
            "Faturamento": "sum",
            "Custo": "sum",
            "Clientes": "sum",
            "Lucro": "sum"
        }).reset_index()
        
        df_yearly["Margem"] = (df_yearly["Lucro"] / df_yearly["Faturamento"]) * 100
        df_yearly["Faturamento_por_Cliente"] = df_yearly["Faturamento"] / df_yearly["Clientes"]
        
        available_years = sorted(df_yearly["Ano"].unique())
        selected_years = st.multiselect(
            "Selecione os anos para comparar",
            options=available_years,
            default=available_years
        )
        
        if selected_years:
            df_selected = df_yearly[df_yearly["Ano"].isin(selected_years)]
            
            # Gráfico comparativo
            fig = px.line(
                df_selected,
                x="Ano",
                y=["Faturamento", "Custo", "Lucro"],
                title="Comparativo Anual",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de crescimento
            st.subheader("Taxa de Crescimento Anual")
            df_growth = df_selected.sort_values("Ano").set_index("Ano")
            df_growth = df_growth.pct_change() * 100
            df_growth = df_growth.round(2).fillna(0)
            
            # Formata a tabela
            styled_df = df_growth.style.format({
                "Faturamento": "{:.2f}%",
                "Custo": "{:.2f}%", 
                "Lucro": "{:.2f}%",
                "Margem": "{:.2f}%",
                "Faturamento_por_Cliente": "{:.2f}%"
            })
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Gráfico de barras comparativo
            st.subheader("Comparação Direta entre Anos")
            fig = px.bar(
                df_selected.melt(id_vars=["Ano"], 
                               value_vars=["Faturamento", "Custo", "Lucro"]),
                x="Ano",
                y="value",
                color="variable",
                barmode="group",
                title="Comparação Detalhada por Ano",
                labels={"value": "Valor (R$)", "variable": "Métrica"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Selecione pelo menos um ano para comparação")

# ABA: EDIÇÃO DE DADOS
with tab_dados:
    st.subheader("Editor de Dados")

    # Formulário para adicionar novo registro
    with st.expander("Adicionar Novo Registro", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_date = st.date_input("Data", datetime.now())
            with col2:
                new_faturamento = st.number_input("Faturamento (R$)", min_value=0.0, step=100.0)
            with col3:
                new_custo = st.number_input("Custo (R$)", min_value=0.0, step=100.0)
            with col4:
                new_clientes = st.number_input("Clientes", min_value=0, step=1)
            
            submitted = st.form_submit_button("Adicionar Registro")
            if submitted:
                new_row = {
                    "Data": pd.to_datetime(new_date),
                    "Faturamento": new_faturamento,
                    "Custo": new_custo,
                    "Clientes": new_clientes
                }
                df = load_data()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("Registro adicionado com sucesso!")
                time.sleep(1)

    # Tabela editável
    st.subheader("Editar/Remover Registros Existentes")
    df = load_data()
    
    if not df.empty:
        edited_df = st.data_editor(
            df.sort_values("Data", ascending=False),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="YYYY-MM-DD"),
                "Faturamento": st.column_config.NumberColumn("Faturamento (R$)", format="R$ %.2f"),
                "Custo": st.column_config.NumberColumn("Custo (R$)", format="R$ %.2f"),
                "Clientes": st.column_config.NumberColumn("Clientes")
            },
            key="data_editor"
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("💾 Salvar Alterações"):
                df = edited_df.sort_values("Data").reset_index(drop=True)
                save_data(df)
                st.success("Dados salvos com sucesso!")
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button("↩️ Descartar Alterações"):
                st.rerun()
        with col3:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📤 Exportar Dados",
                data=csv,
                file_name="faturamento_exportado.csv",
                mime="text/csv"
            )
        with col4:
            if st.button("⚠️ Limpar Todos os Dados", type="primary"):
                if st.checkbox("Confirmar limpeza total dos dados"):
                    df = pd.DataFrame(columns=["Data", "Faturamento", "Custo", "Clientes"])
                    save_data(df)
                    st.success("Dados limpos com sucesso!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("Nenhum dado disponível para edição.")

# Lógica de atualização automática
if auto_refresh:
    while True:
        df = load_data()
        
        if not df.empty and 'date_range' in locals():
            if len(date_range) == 2:
                start_date, end_date = date_range
                df_filtered = df[(df["Data"] >= pd.to_datetime(start_date)) & 
                                 (df["Data"] <= pd.to_datetime(end_date))]
            else:
                df_filtered = df.copy()
        else:
            df_filtered = df.copy()
        
        time.sleep(refresh_interval)
        st.rerun()