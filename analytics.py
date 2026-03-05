from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import pandas as pd


USER_RAW_COLUMNS = [
    "Usuario",
    "Data",
    "Fonte",
    "Obs",
    "Creditos_Chat",
    "Creditos_Consulta",
]

EVENT_RAW_COLUMNS = ["Usuario", "Acao", "Data"]

FEATURE_RULES = [
    ("jurisbrasil", "Consulta JurisBrasil"),
    ("doutrina", "Consulta Doutrina"),
    ("vade", "Consulta Vade"),
    ("servidor", "Consulta Servidor"),
    ("bibliografia", "Bibliografia"),
    ("cgu", "CGU"),
    ("leis", "Consulta Leis"),
    ("pdf", "Consulta PDF"),
    ("documentacao", "Documentacao"),
    ("bateria", "Bateria"),
    ("consulta", "Consulta"),
    ("papo", "Chat"),
    ("chat", "Chat"),
    ("audio", "Audio"),
    ("voz", "Audio"),
    ("imagem", "Imagem"),
    ("loja", "Loja"),
]

FAILURE_TERMS = ("falhou", "falha", "erro", "timeout")
SUCCESS_TERMS = ("concluida", "concluido", "sucesso", "finalizada", "finalizado")
USAGE_TERMS = (
    "utilizada",
    "utilizado",
    "visualizada",
    "visualizado",
    "carregada",
    "carregado",
    "enviada",
    "enviado",
    "adicionada",
    "adicionado",
    "removida",
    "removido",
)


def _as_dataframe(rows_or_df: Iterable[object] | pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if isinstance(rows_or_df, pd.DataFrame):
        return rows_or_df.copy()
    return pd.DataFrame(list(rows_or_df), columns=columns)


def _slugify(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text)
    return text


def _title_from_slug(slug: str) -> str:
    if not slug:
        return "Acao desconhecida"
    return slug.title()


def classify_action(action: object) -> dict[str, object]:
    slug = _slugify(action)
    feature = "Outros"
    for token, label in FEATURE_RULES:
        if token in slug:
            feature = label
            break

    if any(term in slug for term in FAILURE_TERMS):
        status = "Falha"
    elif any(term in slug for term in SUCCESS_TERMS):
        status = "Sucesso"
    elif any(term in slug for term in USAGE_TERMS):
        status = "Uso"
    else:
        status = "Outro"

    return {
        "AcaoOriginal": str(action or "").strip() or "Acao desconhecida",
        "AcaoNormalizada": _title_from_slug(slug),
        "Feature": feature,
        "Status": status,
        "TemFalha": status == "Falha",
        "TemSucesso": status == "Sucesso",
    }


def profile_user_quality(rows_or_df: Iterable[object] | pd.DataFrame) -> dict[str, int]:
    df = _as_dataframe(rows_or_df, USER_RAW_COLUMNS)
    duplicated = int(df.duplicated().sum())
    invalid_dates = int(pd.to_datetime(df.get("Data"), format="%Y/%m/%d %H:%M:%S", errors="coerce").isna().sum())
    missing_users = int(df.get("Usuario").isna().sum()) if "Usuario" in df else len(df)
    return {
        "linhas_brutas": int(len(df)),
        "linhas_duplicadas": duplicated,
        "datas_invalidas": invalid_dates,
        "usuarios_vazios": missing_users,
    }


def profile_event_quality(rows_or_df: Iterable[object] | pd.DataFrame) -> dict[str, int]:
    df = _as_dataframe(rows_or_df, EVENT_RAW_COLUMNS)
    duplicated = int(df.duplicated().sum())
    invalid_dates = int(pd.to_datetime(df.get("Data"), format="%Y/%m/%d %H:%M:%S", errors="coerce").isna().sum())
    missing_users = int(df.get("Usuario").isna().sum()) if "Usuario" in df else len(df)
    missing_actions = int(df.get("Acao").isna().sum()) if "Acao" in df else len(df)
    return {
        "linhas_brutas": int(len(df)),
        "linhas_duplicadas": duplicated,
        "datas_invalidas": invalid_dates,
        "usuarios_vazios": missing_users,
        "acoes_vazias": missing_actions,
    }


def build_user_registry(rows_or_df: Iterable[object] | pd.DataFrame) -> pd.DataFrame:
    df = _as_dataframe(rows_or_df, USER_RAW_COLUMNS)
    df = df[["Usuario", "Data", "Creditos_Chat", "Creditos_Consulta"]].copy()
    df["Data"] = pd.to_datetime(df["Data"], format="%Y/%m/%d %H:%M:%S", errors="coerce")
    df["Usuario"] = pd.to_numeric(df["Usuario"], errors="coerce")
    df["Creditos_Chat"] = pd.to_numeric(df["Creditos_Chat"], errors="coerce")
    df["Creditos_Consulta"] = pd.to_numeric(df["Creditos_Consulta"], errors="coerce")
    df = df.dropna(subset=["Usuario", "Data"]).drop_duplicates()
    df["Usuario"] = df["Usuario"].astype("int64")
    df = df.sort_values(["Usuario", "Data"]).reset_index(drop=True)
    df["DataDia"] = df["Data"].dt.date
    df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
    return df


def build_event_frame(
    rows_or_df: Iterable[object] | pd.DataFrame,
    session_timeout_minutes: int = 30,
) -> pd.DataFrame:
    df = _as_dataframe(rows_or_df, EVENT_RAW_COLUMNS)
    df["Data"] = pd.to_datetime(df["Data"], format="%Y/%m/%d %H:%M:%S", errors="coerce")
    df["Usuario"] = pd.to_numeric(df["Usuario"], errors="coerce")
    df["Acao"] = df["Acao"].astype("string").str.strip()
    df = df.dropna(subset=["Usuario", "Acao", "Data"]).drop_duplicates().copy()
    df["Usuario"] = df["Usuario"].astype("int64")
    df = df.sort_values(["Usuario", "Data", "Acao"]).reset_index(drop=True)

    meta = pd.DataFrame(df["Acao"].apply(classify_action).tolist())
    df = pd.concat([df, meta], axis=1)

    df["DataDia"] = df["Data"].dt.date
    df["Ano"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month
    df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
    df["Hora"] = df["Data"].dt.hour
    df["DiaSemanaEng"] = df["Data"].dt.day_name()
    df["DiaSemana"] = df["DiaSemanaEng"].map(
        {
            "Monday": "Segunda",
            "Tuesday": "Terca",
            "Wednesday": "Quarta",
            "Thursday": "Quinta",
            "Friday": "Sexta",
            "Saturday": "Sabado",
            "Sunday": "Domingo",
        }
    )

    gap_seconds = df.groupby("Usuario")["Data"].diff().dt.total_seconds()
    df["TempoDesdeAnteriorSegundos"] = gap_seconds
    df["NovaSessao"] = gap_seconds.isna() | (gap_seconds > session_timeout_minutes * 60)
    df["SessaoNumero"] = df.groupby("Usuario")["NovaSessao"].cumsum().astype("int64")
    df["SessaoId"] = df["Usuario"].astype(str) + "-" + df["SessaoNumero"].astype(str)
    df["IndiceNaSessao"] = df.groupby("SessaoId").cumcount() + 1

    same_session_next = df["SessaoId"].eq(df["SessaoId"].shift(-1))
    df["ProximaFeature"] = df["Feature"].shift(-1).where(same_session_next)
    df["ProximaAcao"] = df["AcaoOriginal"].shift(-1).where(same_session_next)
    df["TempoAteProximaSegundos"] = (
        df["Data"].shift(-1).sub(df["Data"]).dt.total_seconds().where(same_session_next)
    )
    return df


def latest_user_snapshot(user_registry_df: pd.DataFrame) -> pd.DataFrame:
    if user_registry_df.empty:
        return user_registry_df.copy()
    latest = (
        user_registry_df.sort_values(["Usuario", "Data"])
        .groupby("Usuario", as_index=False)
        .tail(1)
        .sort_values("Data", ascending=False)
        .reset_index(drop=True)
    )
    return latest


def build_user_stats(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        columns = [
            "Usuario",
            "PrimeiroEvento",
            "UltimoEvento",
            "TotalAcoes",
            "DiasAtivos",
            "FeaturesUnicas",
            "TotalSessoes",
            "RetencaoDias",
            "Retido7D",
            "Segmento",
        ]
        return pd.DataFrame(columns=columns)

    stats = (
        event_df.groupby("Usuario")
        .agg(
            PrimeiroEvento=("Data", "min"),
            UltimoEvento=("Data", "max"),
            TotalAcoes=("AcaoOriginal", "size"),
            DiasAtivos=("DataDia", "nunique"),
            FeaturesUnicas=("Feature", "nunique"),
            TotalSessoes=("SessaoId", "nunique"),
        )
        .reset_index()
    )
    stats["RetencaoDias"] = (stats["UltimoEvento"] - stats["PrimeiroEvento"]).dt.days
    stats["Retido7D"] = stats["RetencaoDias"] >= 7

    def _segment(row: pd.Series) -> str:
        if row["TotalAcoes"] >= 40 or row["DiasAtivos"] >= 5 or row["FeaturesUnicas"] >= 5:
            return "Power user"
        if row["TotalAcoes"] >= 12 or row["DiasAtivos"] >= 3 or row["TotalSessoes"] >= 4:
            return "Recorrente"
        if row["TotalAcoes"] >= 4 or row["TotalSessoes"] >= 2:
            return "Explorador"
        return "Novo"

    stats["Segmento"] = stats.apply(_segment, axis=1)
    stats["CohortMes"] = stats["PrimeiroEvento"].dt.to_period("M").astype(str)
    return stats.sort_values("TotalAcoes", ascending=False).reset_index(drop=True)


def growth_from_events(event_df: pd.DataFrame, days: int = 30) -> dict[str, pd.DataFrame]:
    stats = build_user_stats(event_df)
    if stats.empty:
        empty = pd.DataFrame(columns=["Periodo", "Usuarios"])
        return {"novos_mes": empty, "acumulado_mes": empty, "novos_dia": empty}

    first_events = stats[["Usuario", "PrimeiroEvento"]].copy()
    first_events["AnoMes"] = first_events["PrimeiroEvento"].dt.to_period("M").astype(str)
    novos_mes = (
        first_events.groupby("AnoMes")
        .size()
        .reset_index(name="Usuarios")
        .rename(columns={"AnoMes": "Periodo"})
    )
    acumulado = novos_mes.copy()
    acumulado["Usuarios"] = acumulado["Usuarios"].cumsum()

    reference_day = event_df["Data"].max().normalize()
    cutoff = reference_day - pd.Timedelta(days=days - 1)
    recentes = first_events[first_events["PrimeiroEvento"] >= cutoff].copy()
    recentes["DataDia"] = recentes["PrimeiroEvento"].dt.normalize()
    novos_dia = (
        recentes.groupby("DataDia")
        .size()
        .reset_index(name="Usuarios")
        .rename(columns={"DataDia": "Periodo"})
    )
    if not novos_dia.empty:
        full_range = pd.date_range(start=cutoff, end=reference_day, freq="D")
        novos_dia = (
            novos_dia.set_index("Periodo")
            .reindex(full_range, fill_value=0)
            .rename_axis("Periodo")
            .reset_index()
        )
    return {"novos_mes": novos_mes, "acumulado_mes": acumulado, "novos_dia": novos_dia}


def retention_distribution(event_df: pd.DataFrame) -> pd.DataFrame:
    stats = build_user_stats(event_df)
    if stats.empty:
        return stats
    return stats.sort_values("RetencaoDias", ascending=False).reset_index(drop=True)


def cohort_retention_matrix(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame()

    active = event_df[["Usuario", "Data"]].copy()
    active["PeriodoAtivo"] = active["Data"].dt.to_period("M")
    cohort = active.groupby("Usuario")["PeriodoAtivo"].min().rename("Cohort")
    active = active.join(cohort, on="Usuario")

    active["PeriodoIndex"] = (
        (active["PeriodoAtivo"].dt.year - active["Cohort"].dt.year) * 12
        + (active["PeriodoAtivo"].dt.month - active["Cohort"].dt.month)
    )
    cohort_users = (
        active.drop_duplicates(["Usuario", "PeriodoIndex"])
        .groupby(["Cohort", "PeriodoIndex"])["Usuario"]
        .nunique()
        .reset_index(name="UsuariosAtivos")
    )
    sizes = cohort_users[cohort_users["PeriodoIndex"] == 0][["Cohort", "UsuariosAtivos"]].rename(
        columns={"UsuariosAtivos": "TamanhoCohort"}
    )
    cohort_users = cohort_users.merge(sizes, on="Cohort", how="left")
    cohort_users["Retencao"] = cohort_users["UsuariosAtivos"] / cohort_users["TamanhoCohort"]
    pivot = cohort_users.pivot(index="Cohort", columns="PeriodoIndex", values="Retencao")
    pivot.index = pivot.index.astype(str)
    pivot = pivot.sort_index()
    return pivot.fillna(0.0)


def feature_adoption(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame(columns=["Feature", "UsuariosAtivos", "Eventos", "EventosPorUsuario", "TaxaAdocao"])

    total_users = event_df["Usuario"].nunique()
    adoption = (
        event_df.groupby("Feature")
        .agg(UsuariosAtivos=("Usuario", "nunique"), Eventos=("AcaoOriginal", "size"))
        .reset_index()
    )
    adoption["EventosPorUsuario"] = adoption["Eventos"] / adoption["UsuariosAtivos"]
    adoption["TaxaAdocao"] = adoption["UsuariosAtivos"] / total_users
    return adoption.sort_values(["UsuariosAtivos", "Eventos"], ascending=False).reset_index(drop=True)


def failure_by_feature(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame(columns=["Feature", "Falhas", "Sucessos", "Tentativas", "TaxaFalha"])

    status_df = event_df[event_df["Status"].isin(["Falha", "Sucesso"])].copy()
    if status_df.empty:
        return pd.DataFrame(columns=["Feature", "Falhas", "Sucessos", "Tentativas", "TaxaFalha"])

    summary = (
        status_df.pivot_table(index="Feature", columns="Status", values="Usuario", aggfunc="count", fill_value=0)
        .rename_axis(columns=None)
        .reset_index()
    )
    if "Falha" not in summary:
        summary["Falha"] = 0
    if "Sucesso" not in summary:
        summary["Sucesso"] = 0

    summary = summary.rename(columns={"Falha": "Falhas", "Sucesso": "Sucessos"})
    summary["Tentativas"] = summary["Falhas"] + summary["Sucessos"]
    summary["TaxaFalha"] = summary["Falhas"] / summary["Tentativas"]
    summary = summary[summary["Tentativas"] > 0]
    return summary.sort_values(["TaxaFalha", "Tentativas"], ascending=[False, False]).reset_index(drop=True)


def engagement_funnel(event_df: pd.DataFrame) -> pd.DataFrame:
    stats = build_user_stats(event_df)
    if stats.empty:
        return pd.DataFrame(columns=["Etapa", "Usuarios", "ConversaoVsAnterior", "ConversaoVsTotal"])

    steps = [
        ("Primeiro evento", len(stats)),
        ("2+ acoes", int((stats["TotalAcoes"] >= 2).sum())),
        ("2+ sessoes", int((stats["TotalSessoes"] >= 2).sum())),
        ("2+ dias ativos", int((stats["DiasAtivos"] >= 2).sum())),
        ("Retidos 7 dias", int(stats["Retido7D"].sum())),
    ]
    total = steps[0][1]
    previous = total
    rows = []
    for label, users in steps:
        rows.append(
            {
                "Etapa": label,
                "Usuarios": users,
                "ConversaoVsAnterior": users / previous if previous else 0.0,
                "ConversaoVsTotal": users / total if total else 0.0,
            }
        )
        previous = users
    return pd.DataFrame(rows)


def session_metrics(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame(columns=["SessaoId", "Usuario", "Inicio", "Fim", "Acoes", "Features", "DuracaoMinutos"])

    sessions = (
        event_df.groupby("SessaoId")
        .agg(
            Usuario=("Usuario", "first"),
            Inicio=("Data", "min"),
            Fim=("Data", "max"),
            Acoes=("AcaoOriginal", "size"),
            Features=("Feature", "nunique"),
        )
        .reset_index()
    )
    sessions["DuracaoMinutos"] = (sessions["Fim"] - sessions["Inicio"]).dt.total_seconds() / 60.0
    return sessions.sort_values("Inicio", ascending=False).reset_index(drop=True)


def transition_summary(event_df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    if event_df.empty:
        return pd.DataFrame(columns=["FeatureOrigem", "FeatureDestino", "Transicoes", "Usuarios", "TempoMedioSegundos"])

    transitions = event_df.dropna(subset=["ProximaFeature"]).copy()
    transitions = transitions[transitions["Feature"] != transitions["ProximaFeature"]]
    if transitions.empty:
        return pd.DataFrame(columns=["FeatureOrigem", "FeatureDestino", "Transicoes", "Usuarios", "TempoMedioSegundos"])

    summary = (
        transitions.groupby(["Feature", "ProximaFeature"])
        .agg(
            Transicoes=("Usuario", "size"),
            Usuarios=("Usuario", "nunique"),
            TempoMedioSegundos=("TempoAteProximaSegundos", "median"),
        )
        .reset_index()
        .rename(columns={"Feature": "FeatureOrigem", "ProximaFeature": "FeatureDestino"})
        .sort_values(["Transicoes", "Usuarios"], ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return summary


def credit_views(user_registry_df: pd.DataFrame, event_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    latest = latest_user_snapshot(user_registry_df)
    stats = build_user_stats(event_df)
    if latest.empty:
        empty = pd.DataFrame()
        return {"latest": empty, "por_segmento": empty, "por_cohort": empty}

    merged = latest.merge(stats[["Usuario", "Segmento", "CohortMes"]], on="Usuario", how="left")
    merged["Segmento"] = merged["Segmento"].fillna("Sem atividade no recorte")
    merged["CohortMes"] = merged["CohortMes"].fillna("Sem atividade no recorte")

    by_segment = (
        merged.groupby("Segmento")
        .agg(
            Usuarios=("Usuario", "nunique"),
            CreditosChatMedios=("Creditos_Chat", "mean"),
            CreditosConsultaMedios=("Creditos_Consulta", "mean"),
        )
        .reset_index()
        .sort_values("Usuarios", ascending=False)
    )
    by_cohort = (
        merged.groupby("CohortMes")
        .agg(
            Usuarios=("Usuario", "nunique"),
            CreditosChatMedios=("Creditos_Chat", "mean"),
            CreditosConsultaMedios=("Creditos_Consulta", "mean"),
        )
        .reset_index()
        .sort_values("CohortMes")
    )
    return {"latest": merged, "por_segmento": by_segment, "por_cohort": by_cohort}
