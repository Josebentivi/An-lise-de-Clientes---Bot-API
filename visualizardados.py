import streamlit as st
from BancoDadosconstituicaoai import BD
import pandas as pd
import numpy as np
import seaborn as sns
import warnings
import requests
import matplotlib.pyplot as plt

# Suppress Streamlit's ScriptRunContext warning
warnings.filterwarnings("ignore", message="missing ScriptRunContext")

# Configuração inicial da página
st.set_page_config(page_title="Visualização dos Clientes JurisAI", layout="wide")
st.title("Dashboard de Visualização dos Dados")

# Autenticação: Solicita a chave secreta
st.sidebar.header("Autenticação")
chave_secreta = st.sidebar.text_input("Insira sua chave", type="password")

url = "http://52.2.202.37/streamlit/"
data = {"cliente": chave_secreta}
response = requests.post(url, json=data, timeout=5*60)
if response.status_code == 200:  
    saida = response.json()["saida"]
    print(saida)
    erro = response.json()["erro"]
    print(erro)
else:  
    print("Erro na requisição")
    print(response.status_code)
    print(response.text)
    st.stop()    

# Upload do arquivo CSV
#st.sidebar.header("Carregar arquivo CSV")
#uploaded_file = st.sidebar.file_uploader("Escolha um arquivo CSV", type="csv")

#if uploaded_file is not None:
if True:
    # Leitura dos dados
    #df = pd.read_csv(uploaded_file)
    df = pd.DataFrame(saida,columns=["Usuario","Acao","Data"])

    # Verificação dos campos esperados
    expected_columns = {'Usuario', 'Acao', 'Data'}
    if not expected_columns.issubset(df.columns):
        st.error("O arquivo CSV deve conter as colunas: Usuario, Acao, Data")
    else:
        # Conversão da coluna Data para datetime
        df['Data'] = pd.to_datetime(df['Data'], format="%Y/%m/%d %H:%M:%S", errors="coerce")
        df.dropna(subset=['Data'], inplace=True)

        # Enriquecimento dos dados com extração de variáveis temporais
        df['Ano'] = df['Data'].dt.year
        df['Mes'] = df['Data'].dt.month
        df['Dia'] = df['Data'].dt.day
        df['Hora'] = df['Data'].dt.hour
        df['Dia_da_Semana'] = df['Data'].dt.day_name()

        # Remoção de duplicidades
        df.drop_duplicates(inplace=True)

        # Agrupamento de ações relacionadas
        def agrupar_acoes(acao):
            if acao in ["Consulta JurisBrasil falhou", "Consulta JurisBrasil Concluida", "Consulta JurisBrasil utilizada"]:
                return "Consulta JurisBrasil"
            return acao

        df['Acao_Agrupada'] = df['Acao'].apply(agrupar_acoes)

        # Exibição dos dados carregados
        st.subheader("Visualização dos Dados")
        st.dataframe(df.head(10))

        # 1. Frequência e Volume de Ações
        st.subheader("Contagem de Ações")
        contagem_acoes = df['Acao_Agrupada'].value_counts().reset_index()
        contagem_acoes.columns = ['Acao', 'Contagem']
        st.dataframe(contagem_acoes)

        # Gráfico de barras para a frequência das ações
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='Contagem', y='Acao', data=contagem_acoes, ax=ax1)
        ax1.set_title("Frequência de Ações")
        st.pyplot(fig1)

        # 2. Evolução Temporal das Ações (Diária)
        st.subheader("Evolução Temporal das Ações")
        df['Data_Somente'] = df['Data'].dt.date
        acao_selecionada = st.selectbox("Selecione uma ação para analisar a evolução temporal", df['Acao_Agrupada'].unique())
        df_acao = df[df['Acao_Agrupada'] == acao_selecionada]
        serie_temporal = df_acao.groupby("Data_Somente").size()
        st.line_chart(serie_temporal)

        # 3. Análise de Sucesso vs Falhas para Consulta JurisBrasil
        st.subheader("Sucesso vs. Falhas - Consulta JurisBrasil")
        df_juris = df[df['Acao'].isin(["Consulta JurisBrasil Concluida", "Consulta JurisBrasil falhou"])]
        if not df_juris.empty:
            resumo_juris = df_juris['Acao'].value_counts().reset_index()
            resumo_juris.columns = ['Acao', 'Contagem']
            st.dataframe(resumo_juris)
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.barplot(x='Acao', y='Contagem', data=resumo_juris, ax=ax2)
            ax2.set_title("Consulta JurisBrasil: Concluída vs. Falhou")
            st.pyplot(fig2)
        else:
            st.info("Não há dados suficientes para análise de 'Consulta JurisBrasil'.")

        # 4. Análise de Comportamento do Usuário: Distribuição de Atividade
        st.subheader("Distribuição de Atividade dos Usuários")
        usuarios_atividade = df['Usuario'].value_counts().reset_index()
        usuarios_atividade.columns = ['Usuario', 'Acoes']
        st.dataframe(usuarios_atividade.head(10))
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        sns.histplot(usuarios_atividade['Acoes'], bins=20, kde=True, ax=ax3)
        ax3.set_title("Distribuição do Número de Ações por Usuário")
        st.pyplot(fig3)

        # 5. Heatmap: Atividade por Hora e Dia da Semana
        st.subheader("Heatmap de Atividade (Hora vs Dia da Semana)")
        pivot_table = df.pivot_table(index='Dia_da_Semana', columns='Hora', values='Acao', aggfunc='count').fillna(0)
        # Reordenar dias da semana
        ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(ordem_dias)
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        sns.heatmap(pivot_table, cmap="YlGnBu", ax=ax4)
        ax4.set_title("Número de Ações por Hora e Dia da Semana")
        st.pyplot(fig4)
        
        # 6. Análise de Tempo entre Ações (para usuários individuais)
        st.subheader("Tempo entre Ações (Usuário Individual)")
        usuario_id = st.text_input("Digite o ID do Cliente (10 dígitos) para analisar o tempo entre ações")
        if usuario_id:
            df_usuario = df[df['Usuario'] == int(usuario_id)]
            if len(df_usuario) >= 2:
                df_usuario = df_usuario.sort_values("Data")
                df_usuario['Tempo_entre'] = df_usuario['Data'].diff().dt.total_seconds()
                st.dataframe(df_usuario[['Data', 'Acao', 'Tempo_entre']].head(10))
                st.write("Tempo médio entre ações (segundos): ", df_usuario['Tempo_entre'].mean())
            else:
                st.info("O usuário possui poucas ações para análise.")
else:
    st.info("Por favor, carregue um arquivo CSV para prosseguir.")
