from __future__ import annotations

import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
import streamlit as st

from analytics import (
    build_event_frame,
    build_user_registry,
    build_user_stats,
    cohort_retention_matrix,
    credit_views,
    engagement_funnel,
    failure_by_feature,
    feature_adoption,
    growth_from_events,
    profile_event_quality,
    profile_user_quality,
    retention_distribution,
    session_metrics,
    transition_summary,
)


API_URL = os.getenv("JURISAI_API_URL", "http://52.2.202.37/streamlit/")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("JURISAI_TIMEOUT_SECONDS", "30"))

plt.style.use("seaborn-v0_8-pastel")
sns.set_theme(style="whitegrid")


def obter_chave_secreta() -> str:
    try:
        chave = st.secrets.get("CHAVE", "")
    except Exception:
        chave = ""
    return chave or os.getenv("CHAVE", "")


@st.cache_data(ttl=600, show_spinner=False)
def carregar_saida(produto: str, chave: str) -> tuple[list[object], object]:
    response = requests.post(
        API_URL,
        json={"cliente": chave, "produto": produto},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    payload = response.json()
    if "saida" not in payload:
        raise ValueError("Resposta da API sem o campo 'saida'.")

    return payload["saida"], payload.get("erro")


@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_brutos(chave: str) -> tuple[list[object], list[object]]:
    usuarios_raw, _ = carregar_saida("jurisaiusuarios", chave)
    eventos_raw, _ = carregar_saida("jurisai", chave)
    return usuarios_raw, eventos_raw


@st.cache_data(ttl=600, show_spinner=False)
def preparar_modelos(
    usuarios_raw: list[object], eventos_raw: list[object]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int], dict[str, int]]:
    user_registry = build_user_registry(usuarios_raw)
    event_df = build_event_frame(eventos_raw)
    return (
        user_registry,
        event_df,
        profile_user_quality(usuarios_raw),
        profile_event_quality(eventos_raw),
    )


def filtrar_eventos(
    event_df: pd.DataFrame,
    segmentos_base: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    features: list[str],
    statuses: list[str],
    segmentos: list[str],
) -> pd.DataFrame:
    allowed_users = segmentos_base[segmentos_base["Segmento"].isin(segmentos)]["Usuario"]
    mask = (
        event_df["Data"].between(start_date, end_date)
        & event_df["Feature"].isin(features)
        & event_df["Status"].isin(statuses)
        & event_df["Usuario"].isin(allowed_users)
    )
    return event_df.loc[mask].copy()


def _plot_month_series(data: pd.DataFrame, title: str, y_label: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data["Periodo"], data["Usuarios"], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Periodo")
    ax.set_ylabel(y_label)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    plt.close(fig)


def _plot_histogram(series: pd.Series, title: str, x_label: str, color: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(series.dropna(), bins=20, kde=True, ax=ax, color=color)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Usuarios")
    st.pyplot(fig)
    plt.close(fig)


def _plot_bar(data: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x=x, y=y, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    st.pyplot(fig)
    plt.close(fig)


def _render_overview(event_df: pd.DataFrame, user_registry_df: pd.DataFrame) -> None:
    user_stats = build_user_stats(event_df)
    growth = growth_from_events(event_df)
    credit_data = credit_views(user_registry_df, event_df)

    active_users = event_df["Usuario"].nunique()
    total_events = len(event_df)
    total_sessions = event_df["SessaoId"].nunique()
    actions_per_user = user_stats["TotalAcoes"].mean() if not user_stats.empty else 0.0
    retention_7d = user_stats["Retido7D"].mean() if not user_stats.empty else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Usuarios ativos", f"{active_users:,}".replace(",", "."))
    col2.metric("Eventos", f"{total_events:,}".replace(",", "."))
    col3.metric("Sessoes", f"{total_sessions:,}".replace(",", "."))
    col4.metric("Acoes por usuario", f"{actions_per_user:.1f}")
    col5.metric("Retencao 7D", f"{retention_7d:.1%}")

    st.caption("Todos os indicadores abaixo respeitam o recorte definido na barra lateral.")

    growth_col1, growth_col2 = st.columns(2)
    with growth_col1:
        st.subheader("Novos usuarios por mes")
        if growth["novos_mes"].empty:
            st.info("Nao ha usuarios suficientes para montar a serie mensal.")
        else:
            _plot_month_series(growth["novos_mes"], "Novos usuarios por mes", "Usuarios")
    with growth_col2:
        st.subheader("Base acumulada por mes")
        if growth["acumulado_mes"].empty:
            st.info("Nao ha usuarios suficientes para montar a serie acumulada.")
        else:
            _plot_month_series(growth["acumulado_mes"], "Base acumulada por mes", "Usuarios")

    daily_col, credit_col = st.columns(2)
    with daily_col:
        st.subheader("Novos usuarios nos ultimos 30 dias do recorte")
        if growth["novos_dia"].empty:
            st.info("Nao ha novos usuarios no periodo recente do recorte.")
        else:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(growth["novos_dia"]["Periodo"], growth["novos_dia"]["Usuarios"], marker="o")
            ax.set_title("Novos usuarios por dia")
            ax.set_xlabel("Data")
            ax.set_ylabel("Usuarios")
            plt.xticks(rotation=45)
            st.pyplot(fig)
            plt.close(fig)
    with credit_col:
        st.subheader("Saldo atual de creditos por usuario")
        latest = credit_data["latest"]
        if latest.empty:
            st.info("Nao ha snapshots de credito para os usuarios filtrados.")
        else:
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.histplot(latest["Creditos_Consulta"].dropna(), bins=20, kde=True, ax=ax, color="salmon")
            ax.set_title("Distribuicao de creditos de consulta")
            ax.set_xlabel("Creditos")
            ax.set_ylabel("Usuarios")
            st.pyplot(fig)
            plt.close(fig)

    segment_col, cohort_col = st.columns(2)
    with segment_col:
        st.subheader("Creditos medios por segmento")
        segment_table = credit_data["por_segmento"]
        if segment_table.empty:
            st.info("Nao ha dados de credito por segmento para o recorte atual.")
        else:
            st.dataframe(segment_table, use_container_width=True)
    with cohort_col:
        st.subheader("Creditos medios por cohort")
        cohort_table = credit_data["por_cohort"]
        if cohort_table.empty:
            st.info("Nao ha dados de credito por cohort para o recorte atual.")
        else:
            st.dataframe(cohort_table, use_container_width=True)


def _render_retention(event_df: pd.DataFrame) -> None:
    user_stats = retention_distribution(event_df)
    if user_stats.empty:
        st.info("Nao ha dados suficientes para analise de retencao.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuicao da retencao")
        _plot_histogram(user_stats["RetencaoDias"], "Retencao em dias", "Dias", "steelblue")
    with col2:
        st.subheader("Usuarios com retencao positiva")
        positivos = user_stats.loc[user_stats["RetencaoDias"] > 0, "RetencaoDias"]
        if positivos.empty:
            st.info("Nenhum usuario retornou em outro dia no recorte atual.")
        else:
            _plot_histogram(positivos, "Retencao positiva", "Dias", "seagreen")

    st.subheader("Tabela de retencao por usuario")
    st.dataframe(user_stats, use_container_width=True)

    st.subheader("Retencao por cohort mensal")
    cohort_matrix = cohort_retention_matrix(event_df)
    if cohort_matrix.empty:
        st.info("Nao ha dados suficientes para cohorts.")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.heatmap(cohort_matrix.mul(100), annot=True, fmt=".1f", cmap="YlGnBu", ax=ax)
        ax.set_title("Retencao percentual por cohort (%)")
        ax.set_xlabel("Mes desde o primeiro uso")
        ax.set_ylabel("Cohort")
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Segmentacao de usuarios no recorte")
    segment_counts = user_stats["Segmento"].value_counts().reset_index()
    segment_counts.columns = ["Segmento", "Usuarios"]
    _plot_bar(segment_counts, "Usuarios", "Segmento", "Usuarios por segmento", "Usuarios", "Segmento")


def _render_features(event_df: pd.DataFrame) -> None:
    adoption = feature_adoption(event_df)
    failures = failure_by_feature(event_df)

    st.subheader("Adocao por feature")
    if adoption.empty:
        st.info("Nao ha uso de feature no recorte atual.")
    else:
        chart = adoption.sort_values("UsuariosAtivos", ascending=False)
        st.dataframe(chart, use_container_width=True)
        _plot_bar(chart, "UsuariosAtivos", "Feature", "Usuarios ativos por feature", "Usuarios", "Feature")

    st.subheader("Falhas por feature")
    if failures.empty:
        st.info("Nao ha eventos com status de sucesso ou falha no recorte atual.")
    else:
        st.dataframe(failures, use_container_width=True)
        failure_chart = failures.copy()
        failure_chart["TaxaFalhaPct"] = failure_chart["TaxaFalha"] * 100
        _plot_bar(failure_chart, "TaxaFalhaPct", "Feature", "Taxa de falha por feature", "Taxa de falha (%)", "Feature")

    st.subheader("Heatmap de atividade")
    if event_df.empty:
        st.info("Sem eventos para heatmap.")
        return

    heatmap = event_df.pivot_table(
        index="DiaSemana",
        columns="Hora",
        values="AcaoOriginal",
        aggfunc="count",
        fill_value=0,
    )
    ordered_days = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]
    heatmap = heatmap.reindex(ordered_days)
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(heatmap, cmap="YlGnBu", ax=ax)
    ax.set_title("Eventos por hora e dia da semana")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Dia da semana")
    st.pyplot(fig)
    plt.close(fig)


def _render_journey(event_df: pd.DataFrame) -> None:
    funnel = engagement_funnel(event_df)
    sessions = session_metrics(event_df)
    transitions = transition_summary(event_df)

    st.subheader("Funil de engajamento")
    if funnel.empty:
        st.info("Nao ha usuarios suficientes para montar o funil.")
    else:
        st.dataframe(funnel, use_container_width=True)
        _plot_bar(funnel, "Usuarios", "Etapa", "Usuarios por etapa do funil", "Usuarios", "Etapa")

    st.subheader("Metricas de sessao")
    if sessions.empty:
        st.info("Nao ha sessoes suficientes para analise.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Acoes medianas por sessao", f"{sessions['Acoes'].median():.1f}")
        col2.metric("Duracao media da sessao", f"{sessions['DuracaoMinutos'].mean():.1f} min")
        col3.metric("Features por sessao", f"{sessions['Features'].mean():.1f}")
        st.dataframe(sessions.head(50), use_container_width=True)

    st.subheader("Transicoes entre features")
    if transitions.empty:
        st.info("Nao ha transicoes entre features no recorte atual.")
    else:
        st.dataframe(transitions, use_container_width=True)
        origem = st.selectbox(
            "Filtrar transicoes por origem",
            options=["Todas"] + sorted(transitions["FeatureOrigem"].unique().tolist()),
        )
        filtered_transitions = transitions if origem == "Todas" else transitions[transitions["FeatureOrigem"] == origem]
        if filtered_transitions.empty:
            st.info("Nenhuma transicao para a feature selecionada.")
        else:
            _plot_bar(
                filtered_transitions,
                "Transicoes",
                "FeatureDestino",
                "Top proximas features",
                "Transicoes",
                "Destino",
            )

    st.subheader("Tempo entre acoes por usuario")
    selected_user = st.text_input("Digite um ID de usuario para inspecionar a jornada")
    if selected_user:
        try:
            user_id = int(selected_user)
        except ValueError:
            st.error("Informe um ID numerico.")
            return
        df_user = event_df[event_df["Usuario"] == user_id].sort_values("Data").copy()
        if len(df_user) < 2:
            st.info("O usuario possui poucas acoes para analise.")
            return
        df_user["TempoEntreSegundos"] = df_user["Data"].diff().dt.total_seconds()
        st.dataframe(
            df_user[["Data", "Feature", "AcaoOriginal", "SessaoId", "TempoEntreSegundos"]],
            use_container_width=True,
        )
        st.metric("Tempo medio entre acoes", f"{df_user['TempoEntreSegundos'].mean():.1f} s")


def _render_quality(
    event_df: pd.DataFrame,
    user_registry_df: pd.DataFrame,
    user_quality: dict[str, int],
    event_quality: dict[str, int],
) -> None:
    st.subheader("Saude do dataset")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Eventos brutos", f"{event_quality['linhas_brutas']:,}".replace(",", "."))
    col2.metric("Datas invalidas", f"{event_quality['datas_invalidas']:,}".replace(",", "."))
    col3.metric("Duplicatas de eventos", f"{event_quality['linhas_duplicadas']:,}".replace(",", "."))
    col4.metric("Acoes vazias", f"{event_quality['acoes_vazias']:,}".replace(",", "."))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Snapshots de usuarios", f"{user_quality['linhas_brutas']:,}".replace(",", "."))
    col6.metric("Datas invalidas usuarios", f"{user_quality['datas_invalidas']:,}".replace(",", "."))
    col7.metric("Duplicatas usuarios", f"{user_quality['linhas_duplicadas']:,}".replace(",", "."))
    col8.metric("Usuarios vazios", f"{user_quality['usuarios_vazios']:,}".replace(",", "."))

    table_col1, table_col2 = st.columns(2)
    with table_col1:
        st.subheader("Ultimas interacoes")
        st.dataframe(
            event_df.sort_values("Data", ascending=False).head(100),
            use_container_width=True,
        )
    with table_col2:
        st.subheader("Ultimos snapshots de usuarios")
        st.dataframe(
            user_registry_df.sort_values("Data", ascending=False).head(100),
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(page_title="JurisAI - Analise de Clientes", layout="wide")
    st.title("JurisAI - Analise de Clientes")
    st.caption("Dashboard com cohorts, segmentacao, funil e qualidade de eventos.")

    chave = obter_chave_secreta()
    if not chave:
        st.error("A secret CHAVE nao esta configurada no Streamlit.")
        st.caption("Defina CHAVE em Settings > Secrets ou como variavel de ambiente.")
        st.stop()

    with st.spinner("Carregando eventos e snapshots de usuarios..."):
        try:
            usuarios_raw, eventos_raw = carregar_dados_brutos(chave)
            user_registry_df, event_df, user_quality, event_quality = preparar_modelos(usuarios_raw, eventos_raw)
        except requests.RequestException as exc:
            st.error(f"Nao foi possivel acessar a API em {API_URL}.")
            st.exception(exc)
            st.stop()
        except ValueError as exc:
            st.error("A API retornou um formato inesperado.")
            st.exception(exc)
            st.stop()

    if event_df.empty:
        st.warning("A API nao retornou eventos validos para o dashboard.")
        st.stop()

    base_user_stats = build_user_stats(event_df)

    st.sidebar.header("Filtros globais")
    min_date = event_df["Data"].min().date()
    max_date = event_df["Data"].max().date()
    date_range = st.sidebar.date_input(
        "Periodo de eventos",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if len(date_range) != 2:
        st.sidebar.warning("Selecione uma data inicial e final.")
        st.stop()
    start_date = pd.Timestamp(date_range[0]).normalize()
    end_date = pd.Timestamp(date_range[1]).normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    feature_options = sorted(event_df["Feature"].dropna().unique().tolist())
    status_options = sorted(event_df["Status"].dropna().unique().tolist())
    segment_options = sorted(base_user_stats["Segmento"].dropna().unique().tolist())

    selected_features = st.sidebar.multiselect("Features", options=feature_options, default=feature_options)
    selected_statuses = st.sidebar.multiselect("Status", options=status_options, default=status_options)
    selected_segments = st.sidebar.multiselect("Segmentos", options=segment_options, default=segment_options)

    filtered_events = filtrar_eventos(
        event_df,
        base_user_stats,
        start_date,
        end_date,
        selected_features or feature_options,
        selected_statuses or status_options,
        selected_segments or segment_options,
    )
    filtered_users = user_registry_df[user_registry_df["Usuario"].isin(filtered_events["Usuario"].unique())].copy()

    st.sidebar.metric("Usuarios no recorte", filtered_events["Usuario"].nunique())
    st.sidebar.metric("Eventos no recorte", len(filtered_events))

    if filtered_events.empty:
        st.warning("Os filtros atuais nao retornaram eventos. Ajuste o recorte na barra lateral.")
        st.stop()

    overview_tab, retention_tab, feature_tab, journey_tab, quality_tab = st.tabs(
        ["Visao geral", "Retencao", "Features", "Jornada", "Qualidade"]
    )

    with overview_tab:
        _render_overview(filtered_events, filtered_users)
    with retention_tab:
        _render_retention(filtered_events)
    with feature_tab:
        _render_features(filtered_events)
    with journey_tab:
        _render_journey(filtered_events)
    with quality_tab:
        _render_quality(filtered_events, filtered_users, user_quality, event_quality)


if __name__ == "__main__":
    main()
