import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import warnings
import requests
import matplotlib.pyplot as plt
from time import sleep
import os
import threading
#estilos = [ 'dark_background', 'fast', 'fivethirtyeight','Solarize_Light2', '_classic_test_patch', '_mpl-gallery', '_mpl-gallery-nogrid', 'bmh', 'classic', 'ggplot', 'grayscale', 'seaborn-v0_8', 'seaborn-v0_8-bright', 'seaborn-v0_8-colorblind', 'seaborn-v0_8-dark', 'seaborn-v0_8-dark-palette', 'seaborn-v0_8-darkgrid', 'seaborn-v0_8-deep', 'seaborn-v0_8-muted', 'seaborn-v0_8-notebook', 'seaborn-v0_8-paper', 'seaborn-v0_8-pastel', 'seaborn-v0_8-poster', 'seaborn-v0_8-talk', 'seaborn-v0_8-ticks', 'seaborn-v0_8-white', 'seaborn-v0_8-whitegrid', 'tableau-colorblind10']
plt.style.use('seaborn-v0_8-pastel')
#plt.style.use('dark_background') 

#atualizado em 18/08/2025
ads=332 

def Carregando():
    porcentagem = 0
    cols = st.columns(3)
    with cols[1]:
        my_bar = st.progress(porcentagem, text="Aprimorando plataforma...")
        tempo=1
        sleep(1)
        CarregandoInicio = ["Carregando leis e jurisprudência...","Carregando doutrinas...","Finalizando melhoria...","Pronto!"]
        for texto in CarregandoInicio:
            porcentagem += 25
            my_bar.progress(porcentagem, text=texto)
            tempo+=0.25
            sleep(tempo)
        my_bar.empty()

#x = threading.Thread(target=alarme, args=())
#x.start()

# Suppress Streamlit's ScriptRunContext warning
warnings.filterwarnings("ignore", message="missing ScriptRunContext")

# Configuração inicial da página
st.set_page_config(page_title="Visualização dos Clientes JurisAI", layout="wide")
#Carregando()
#chave_secreta = st.text_input("Senha de acesso", type="password")
chave_secreta = st.secrets["CHAVE"]
if not chave_secreta and False:
    st.info("Por favor, adicione a sua senha de acesso.", icon="🗝️")
else:    
    url = "http://52.2.202.37/streamlit/"
    data = {"cliente": chave_secreta,
            "produto": "jurisaiusuarios"}
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
    # Leitura dos dados
    #df = pd.read_csv(uploaded_file)
    df = pd.DataFrame(saida,columns=["Usuario","Data","Fonte","Obs","Créditos Função 1","Créditos Função 2"])
    df = df[["Usuario","Data","Créditos Função 1","Créditos Função 2"]]
    #df = df[~df["Data"].astype(str).str.contains("2025-04")]

    # Vimero de clientes
    total_clientes = df["Usuario"].nunique()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div style="background-color: #0e1117; padding: 10px; border-radius: 5px; text-align: center;">
                <p style="color: white; font-size: 18px; margin: 0;">Número de usuários</p>
                <p style="color: white; font-size: 32px; font-weight: bold; margin: 0;">{total_clientes}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="background-color: #0e1117; padding: 10px; border-radius: 5px; text-align: center;">
                <p style="color: white; font-size: 18px; margin: 0;">Acesso Orgânico</p>
                <p style="color: green; font-size: 32px; font-weight: bold; margin: 0;">{total_clientes-ads}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style="background-color: #0e1117; padding: 10px; border-radius: 5px; text-align: center;">
                <p style="color: white; font-size: 18px; margin: 0;">Acesso Ads</p>
                <p style="color: blue; font-size: 32px; font-weight: bold; margin: 0;">{ads}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.title("Análise de Log de Registro dos Clientes")
    #df = pd.read_csv(uploaded_file)
    df["Data"] = pd.to_datetime(df["Data"], format="%Y/%m/%d %H:%M:%S")
    st.header("Visualização dos Dados")
    st.write(df)

    # Plot do total de usuários por mês (cumulativo)
    df_first = df.sort_values("Data").drop_duplicates(subset="Usuario", keep="first")
    df_first["AnoMes"] = df_first["Data"].dt.to_period("M").astype(str)
    total_users_by_month = df_first.groupby("AnoMes").size().cumsum().reset_index(name="Total Usuários")
    fig, ax = plt.subplots()
    ax.plot(total_users_by_month["AnoMes"], total_users_by_month["Total Usuários"], marker="o", linestyle="-")
    ax.set_xlabel("Ano/Mês")
    ax.set_ylabel("Total de Usuários")
    ax.set_title("Total de Usuários por Mês")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("Crescimento de Usuários")
    # Considera o primeiro registro de cada usuário
    df_first = df.sort_values("Data").drop_duplicates(subset="Usuario", keep="first")
    df_first["AnoMes"] = df_first["Data"].dt.to_period("M").astype(str)
    crescimento = df_first.groupby("AnoMes").size().reset_index(name="Novos Usuários")
    fig1, ax1 = plt.subplots()
    ax1.plot(crescimento["AnoMes"], crescimento["Novos Usuários"], marker="o")
    ax1.set_xlabel("Ano/Mês")
    ax1.set_ylabel("Número de Usuários Novos")
    ax1.set_title("Crescimento de Usuários ao longo do tempo")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    # Crescimento Diário de Novos Usuários (Últimos 30 Dias)
    st.subheader("Crescimento Diário de Novos Usuários (Últimos 30 Dias)")
    hoje = pd.Timestamp.today()
    data_inicio = hoje - pd.Timedelta(days=30)
    # Considera o primeiro registro de cada usuário para identificar quando se cadastraram
    df_first = df.sort_values("Data").drop_duplicates(subset="Usuario", keep="first")
    # Filtra os novos usuários registrados nos últimos 30 dias
    novos_30dias = df_first[df_first["Data"] >= data_inicio].copy()
    novos_30dias["Data_Somente"] = novos_30dias["Data"].dt.date
    # Agrupa por dia e conta os novos usuários
    crescimento_diario = novos_30dias.groupby("Data_Somente").size().reset_index(name="Novos Usuários")
    fig_daily, ax_daily = plt.subplots(figsize=(10, 6))
    ax_daily.plot(crescimento_diario["Data_Somente"], crescimento_diario["Novos Usuários"], marker="o", linestyle="-")
    ax_daily.set_xlabel("Data")
    ax_daily.set_ylabel("Novos Usuários")
    ax_daily.set_title("Crescimento Diário de Novos Usuários (Últimos 30 Dias)")
    plt.xticks(rotation=45)
    st.pyplot(fig_daily)

    st.subheader("2. Análise de Disponibilidade de Créditos")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Créditos Chat")
        fig2, ax2 = plt.subplots()
        ax2.hist(df["Créditos Função 1"], bins=50, color="skyblue", edgecolor="black")
        ax2.set_xlabel("Créditos")
        ax2.set_ylabel("Frequência")
        ax2.set_title("Distribuição dos Créditos Chat")
        st.pyplot(fig2)
        media1 = df["Créditos Função 1"].mean()
        mediana1 = df["Créditos Função 1"].median()
        st.write(f"Média: {media1:.2f}, Mediana: {mediana1}")

    with col2:
        st.write("Créditos Consulta")
        fig3, ax3 = plt.subplots()
        ax3.hist(df["Créditos Função 2"], bins=50, color="salmon", edgecolor="black")
        ax3.set_xlabel("Créditos")
        ax3.set_ylabel("Frequência")
        ax3.set_title("Distribuição dos Créditos Consulta")
        st.pyplot(fig3)
        media2 = df["Créditos Função 2"].mean()
        mediana2 = df["Créditos Função 2"].median()
        st.write(f"Média: {media2:.2f}, Mediana: {mediana2}")

    
    #st.markdown("### Relatório Resumido")
    #st.write("O relatório evidencia o crescimento de usuários, a distribuição dos créditos disponíveis e a taxa de retenção dos clientes.")





    st.title("Dashboard de Visualização do comportamento de clientes - JurisAI")

    url = "http://52.2.202.37/streamlit/"
    data = {"cliente": chave_secreta,
            "produto": "jurisai"}
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
            st.subheader("Visualização das Ultimas Interações")
            st.dataframe(df.tail(100))

            st.subheader("Análise de Retenção de Usuários")    
            # Calcula a diferença entre o primeiro e o último acesso para cada usuário
            #df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
            
            # Cálculo da retenção: tempo entre o primeiro e o último acesso para cada usuário
            retencao = df.groupby("Usuario")["Data"].agg(["min", "max"]).reset_index()
            retencao["Retencao_Dias"] = (retencao["max"] - retencao["min"]).dt.days
            mediana_retencao_total = retencao["Retencao_Dias"].count()
            st.write(f"Número total de usuários analisados: {mediana_retencao_total}")
            st.write("Análise de Retenção de Usuários (em dias)")
            st.dataframe(retencao.sort_values("Retencao_Dias", ascending=False))

            # Visualização da distribuição de retenção
            fig_ret, ax_ret = plt.subplots(figsize=(10, 6))
            sns.histplot(retencao["Retencao_Dias"], bins=20, kde=True, ax=ax_ret, color='purple')
            ax_ret.set_title("Distribuição do Tempo de Retenção dos Usuários")
            ax_ret.set_xlabel("Tempo de retenção (dias)")
            ax_ret.set_ylabel("Número de Usuários")
            st.pyplot(fig_ret)
            plt.close(fig_ret)

            # Visualização da distribuição de retenção
            fig_ret, ax_ret = plt.subplots(figsize=(10, 6))
            sns.histplot(retencao[retencao["Retencao_Dias"] > 0]["Retencao_Dias"], bins=20, kde=True, ax=ax_ret, color='purple')
            ax_ret.set_title("Distribuição do Tempo de Retenção dos Usuários com Retenção Positiva")
            ax_ret.set_xlabel("Tempo de retenção (dias)")
            ax_ret.set_ylabel("Número de Usuários")
            st.pyplot(fig_ret)
            plt.close(fig_ret)

            # Estatísticas básicas de retenção
            media_retencao = retencao[retencao["Retencao_Dias"] > 0]["Retencao_Dias"].mean()
            mediana_retencao = retencao[retencao["Retencao_Dias"] > 0]["Retencao_Dias"].median()
            mediana_retencao_zero = retencao[retencao["Retencao_Dias"] == 0]["Retencao_Dias"].count()
            st.write(f"Tempo médio de retenção para usuários com retenção positiva: {media_retencao:.2f} dias")
            st.write(f"Mediana do tempo de retenção para usuários com retenção positiva: {mediana_retencao} dias")
            st.write(f"Número de usuários com retenção zero (Utilizaram apenas um dia): {mediana_retencao_zero}")
            st.write(f"Taxa de retenção: {(1-mediana_retencao_zero / mediana_retencao_total):.2%}")


            # 1. Frequência e Volume de Ações
            st.subheader("Contagem de Ações do Servidor")
            contagem_acoes = df['Acao_Agrupada'].value_counts().reset_index()
            contagem_acoes.columns = ['Acao', 'Contagem']
            st.dataframe(contagem_acoes)

            # Gráfico de barras para a frequência das ações do Servidor
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Contagem', y='Acao', data=contagem_acoes, ax=ax1)
            ax1.set_title("Frequência de Ações")
            ax1.set_xlabel("Interações")
            ax1.set_ylabel("Tipo de Ação")
            st.pyplot(fig1)
            plt.close(fig1)  # Fecha a figura para liberar memória

            # 1.5. Frequência e Volume de Ações do Usuário
            st.subheader("Contagem de Ações do Usuário")
            contagem_acoes = df['Acao_Agrupada'].value_counts().reset_index()
            contagem_acoes.columns = ['Acao', 'Contagem']
            #st.dataframe(contagem_acoes)

            ordered_actions = ['Consulra PDF chat utilizado', 'Consulta Vade utilizada', 'Consulta Servidor utilizada', 'Consulta Doutrina utilizada', 'Consulta JurisBrasil utilizada', 'Consulta Leis utilizada', 'Criar documentação utilizada', 'Audio utilizado', 'Voz utilizada', 'Imagem carregada', 'PDF enviada', 'PDF enviado', 'Papo utilizado', 'Consulta removida', 'Consulta adicionada', 'Bateria removida', 'Bateria adicionada', 'Documentação utilizada', 'Vade utilizado', 'CGU utilizada', 'Doutrina utilizada', 'Leis utilizada', 'Consulta PDF utilizada', 'Bibliografia utilizada']
            contagem_acoes = contagem_acoes.set_index("Acao").reindex(ordered_actions, fill_value=0).reset_index()
            contagem_acoes = contagem_acoes[contagem_acoes['Contagem'] > 0]
            contagem_acoes = contagem_acoes.sort_values("Contagem", ascending=False)

            # Gráfico de barras para a frequência das ações
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Contagem', y='Acao', data=contagem_acoes, ax=ax1)
            ax1.set_title("Frequência de Ações")
            ax1.set_xlabel("Interações")
            ax1.set_ylabel("Tipo de Ação")
            st.pyplot(fig1)
            plt.close(fig1)  # Fecha a figura para liberar memória

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
                #st.dataframe(resumo_juris)
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
            st.dataframe(usuarios_atividade.head(20))
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            sns.histplot(usuarios_atividade['Acoes'], bins=20, kde=True, ax=ax3)
            ax3.set_title("Distribuição do Número de Ações por Usuário")
            ax3.set_xlabel("Interações")
            ax3.set_ylabel("Usuários")
            st.pyplot(fig3)

            # 4.1. Análise de Comportamento do Usuário: Distribuição de Uso Ativo
            st.subheader("Distribuição de Uso Ativo dos Usuários")
            #st.dataframe(df[(df['Acao'] == 'Leis utilizada') | (df['Acao'] == 'Papo utilizado')])
            usuarios_atividade = df[(df['Acao'] == 'Bateria removida') | (df['Acao'] == 'Consulta removida')]['Usuario'].value_counts().reset_index()
            usuarios_atividade.columns = ['Usuario', 'Acoes']
            st.dataframe(usuarios_atividade)
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            sns.histplot(usuarios_atividade['Acoes'], bins=20, kde=True, ax=ax3)
            ax3.set_title("Distribuição do Número de Ações de Uso Ativo por Usuário")
            ax3.set_xlabel("Interações")
            ax3.set_ylabel("Usuários")
            st.pyplot(fig3)

            # 5. Heatmap: Atividade por Hora e Dia da Semana
            st.subheader("Heatmap de Atividade (Hora vs Dia da Semana)")
            pivot_table = df.pivot_table(index='Dia_da_Semana', columns='Hora', values='Acao', aggfunc='count').fillna(0)
            # Reordenar dias da semana
            ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_table = pivot_table.reindex(ordem_dias)

            pivot_table.index = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            fig4, ax4 = plt.subplots(figsize=(12, 6))
            sns.heatmap(pivot_table, cmap="YlGnBu", ax=ax4)
            ax4.set_title("Número de Ações por Hora e Dia da Semana")
            ax4.set_xlabel("Interações")
            ax4.set_ylabel("Dia da Semana")
            st.pyplot(fig4)
            
            # 6. Análise de Tempo entre Ações (para usuários individuais)
            st.subheader("Tempo entre Ações (Usuário Individual)")
            usuario_id = st.text_input("Digite o ID do Cliente (10 dígitos) para analisar o tempo entre ações")
            if usuario_id:
                df_usuario = df[df['Usuario'] == int(usuario_id)]
                if len(df_usuario) >= 2:
                    df_usuario = df_usuario.sort_values("Data")
                    df_usuario['Tempo_entre'] = df_usuario['Data'].diff().dt.total_seconds()
                    st.dataframe(df_usuario[['Data', 'Acao', 'Tempo_entre']])
                    st.write("Tempo médio entre ações (segundos): ", df_usuario['Tempo_entre'].mean())
                else:
                    st.info("O usuário possui poucas ações para análise.")
    else:
        st.info("Por favor, carregue um arquivo CSV para prosseguir.")
