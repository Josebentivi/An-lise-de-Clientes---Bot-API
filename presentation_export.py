from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from analytics import (
    build_user_stats,
    cohort_retention_matrix,
    credit_views,
    engagement_funnel,
    failure_by_feature,
    feature_adoption,
    growth_from_events,
    session_metrics,
    transition_summary,
)


SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
COLOR_NAVY = RGBColor(12, 33, 58)
COLOR_BLUE = RGBColor(42, 93, 163)
COLOR_CYAN = RGBColor(62, 173, 207)
COLOR_GOLD = RGBColor(236, 180, 56)
COLOR_SOFT = RGBColor(240, 245, 250)
COLOR_TEXT = RGBColor(34, 52, 74)
COLOR_MUTED = RGBColor(103, 120, 138)
COLOR_WHITE = RGBColor(255, 255, 255)


def _format_int(value: float | int) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def _format_pct(value: float) -> str:
    return f"{value:.1%}"


def _date_label(start_date: pd.Timestamp, end_date: pd.Timestamp) -> str:
    return f"{start_date:%d/%m/%Y} a {end_date:%d/%m/%Y}"


def _figure_to_png(fig: plt.Figure) -> BytesIO:
    image = BytesIO()
    fig.tight_layout()
    fig.savefig(image, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    image.seek(0)
    return image


def _build_growth_funnel_chart(growth: dict[str, pd.DataFrame], funnel: pd.DataFrame) -> BytesIO:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    monthly = growth["novos_mes"]
    if monthly.empty:
        axes[0].text(0.5, 0.5, "Sem dados de crescimento", ha="center", va="center", fontsize=14)
        axes[0].axis("off")
    else:
        axes[0].plot(monthly["Periodo"], monthly["Usuarios"], marker="o", color="#2A5DA3", linewidth=2.5)
        axes[0].set_title("Novos usuarios por mes", fontsize=14)
        axes[0].set_xlabel("Periodo")
        axes[0].set_ylabel("Usuarios")
        axes[0].tick_params(axis="x", rotation=45)

    if funnel.empty:
        axes[1].text(0.5, 0.5, "Sem dados de funil", ha="center", va="center", fontsize=14)
        axes[1].axis("off")
    else:
        sns.barplot(data=funnel, x="Usuarios", y="Etapa", ax=axes[1], color="#2A5DA3")
        axes[1].set_title("Funil de engajamento", fontsize=14)
        axes[1].set_xlabel("Usuarios")
        axes[1].set_ylabel("")
    return _figure_to_png(fig)


def _build_feature_chart(adoption: pd.DataFrame, failures: pd.DataFrame) -> BytesIO:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    top_adoption = adoption.head(6).sort_values("UsuariosAtivos", ascending=True)
    if top_adoption.empty:
        axes[0].text(0.5, 0.5, "Sem dados de adocao", ha="center", va="center", fontsize=14)
        axes[0].axis("off")
    else:
        sns.barplot(data=top_adoption, x="UsuariosAtivos", y="Feature", ax=axes[0], color="#2A5DA3")
        axes[0].set_title("Features com maior adocao", fontsize=14)
        axes[0].set_xlabel("Usuarios ativos")
        axes[0].set_ylabel("")

    top_failures = failures.head(6).sort_values("TaxaFalha", ascending=True).copy()
    if top_failures.empty:
        axes[1].text(0.5, 0.5, "Sem dados de falha/sucesso", ha="center", va="center", fontsize=14)
        axes[1].axis("off")
    else:
        top_failures["TaxaFalhaPct"] = top_failures["TaxaFalha"] * 100
        sns.barplot(data=top_failures, x="TaxaFalhaPct", y="Feature", ax=axes[1], color="#D46A6A")
        axes[1].set_title("Taxa de falha por feature", fontsize=14)
        axes[1].set_xlabel("Taxa de falha (%)")
        axes[1].set_ylabel("")
    return _figure_to_png(fig)


def _build_retention_chart(cohort: pd.DataFrame, segment_counts: pd.DataFrame) -> BytesIO:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    if cohort.empty:
        axes[0].text(0.5, 0.5, "Sem cohort suficiente", ha="center", va="center", fontsize=14)
        axes[0].axis("off")
    else:
        sns.heatmap(cohort.mul(100), annot=True, fmt=".0f", cmap="YlGnBu", ax=axes[0], cbar=False)
        axes[0].set_title("Retencao por cohort (%)", fontsize=14)
        axes[0].set_xlabel("Meses desde o primeiro uso")
        axes[0].set_ylabel("Cohort")

    if segment_counts.empty:
        axes[1].text(0.5, 0.5, "Sem segmentacao disponivel", ha="center", va="center", fontsize=14)
        axes[1].axis("off")
    else:
        sns.barplot(data=segment_counts, x="Usuarios", y="Segmento", ax=axes[1], color="#3EADCF")
        axes[1].set_title("Perfil de usuarios", fontsize=14)
        axes[1].set_xlabel("Usuarios")
        axes[1].set_ylabel("")
    return _figure_to_png(fig)


def _set_background(slide, color: RGBColor) -> None:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _add_title(slide, title: str, subtitle: str | None = None, dark: bool = False) -> None:
    title_box = slide.shapes.add_textbox(Inches(0.7), Inches(0.4), Inches(8.8), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.clear()
    title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE if dark else COLOR_TEXT
    if subtitle:
        subtitle_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.0), Inches(8.8), Inches(0.45))
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.clear()
        p = subtitle_frame.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_WHITE if dark else COLOR_MUTED


def _add_metric_card(slide, left: float, top: float, label: str, value: str) -> None:
    card = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(2.35),
        Inches(1.25),
    )
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_WHITE
    card.line.color.rgb = COLOR_SOFT

    text_box = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.18), Inches(2.0), Inches(0.9))
    frame = text_box.text_frame
    frame.clear()
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    p1 = frame.paragraphs[0]
    p1.text = label
    p1.font.size = Pt(11)
    p1.font.color.rgb = COLOR_MUTED

    p2 = frame.add_paragraph()
    p2.text = value
    p2.font.size = Pt(23)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_TEXT


def _add_bullets(slide, title: str, bullets: list[str], left: float, top: float, width: float, height: float) -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True

    p = frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT

    for bullet in bullets:
        pb = frame.add_paragraph()
        pb.text = bullet
        pb.level = 0
        pb.font.size = Pt(12)
        pb.font.color.rgb = COLOR_TEXT
        pb.space_before = Pt(6)


def _add_picture(slide, image: BytesIO, left: float, top: float, width: float, height: float) -> None:
    slide.shapes.add_picture(image, Inches(left), Inches(top), width=Inches(width), height=Inches(height))


def _build_context(event_df: pd.DataFrame, user_registry_df: pd.DataFrame) -> dict[str, object]:
    user_stats = build_user_stats(event_df)
    growth = growth_from_events(event_df)
    adoption = feature_adoption(event_df)
    failures = failure_by_feature(event_df)
    funnel = engagement_funnel(event_df)
    sessions = session_metrics(event_df)
    transitions = transition_summary(event_df)
    cohort = cohort_retention_matrix(event_df)
    credits = credit_views(user_registry_df, event_df)

    segment_counts = user_stats["Segmento"].value_counts().reset_index()
    segment_counts.columns = ["Segmento", "Usuarios"]

    latest_credits = credits["latest"]
    top_feature = adoption.iloc[0]["Feature"] if not adoption.empty else "Sem destaque"
    top_feature_users = int(adoption.iloc[0]["UsuariosAtivos"]) if not adoption.empty else 0
    retention_7d = float(user_stats["Retido7D"].mean()) if not user_stats.empty else 0.0
    actions_per_user = float(user_stats["TotalAcoes"].mean()) if not user_stats.empty else 0.0
    avg_session_minutes = float(sessions["DuracaoMinutos"].mean()) if not sessions.empty else 0.0
    avg_consultation_credits = (
        float(latest_credits["Creditos_Consulta"].mean()) if not latest_credits.empty else 0.0
    )
    power_share = (
        float((user_stats["Segmento"] == "Power user").mean()) if not user_stats.empty else 0.0
    )
    recurring_share = (
        float(user_stats["Segmento"].isin(["Recorrente", "Power user"]).mean()) if not user_stats.empty else 0.0
    )
    top_transition = transitions.iloc[0] if not transitions.empty else None

    return {
        "user_stats": user_stats,
        "growth": growth,
        "adoption": adoption,
        "failures": failures,
        "funnel": funnel,
        "sessions": sessions,
        "cohort": cohort,
        "credits": credits,
        "segment_counts": segment_counts,
        "top_feature": top_feature,
        "top_feature_users": top_feature_users,
        "retention_7d": retention_7d,
        "actions_per_user": actions_per_user,
        "avg_session_minutes": avg_session_minutes,
        "avg_consultation_credits": avg_consultation_credits,
        "power_share": power_share,
        "recurring_share": recurring_share,
        "top_transition": top_transition,
    }


def build_presentation_bytes(
    event_df: pd.DataFrame,
    user_registry_df: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> bytes:
    presentation = Presentation()
    presentation.slide_width = SLIDE_W
    presentation.slide_height = SLIDE_H
    blank = presentation.slide_layouts[6]

    context = _build_context(event_df, user_registry_df)
    active_users = event_df["Usuario"].nunique()
    total_events = len(event_df)
    total_sessions = event_df["SessaoId"].nunique()
    period_label = _date_label(start_date, end_date)

    slide = presentation.slides.add_slide(blank)
    _set_background(slide, COLOR_NAVY)
    accent = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, Inches(0.0), Inches(0.28), SLIDE_H)
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_GOLD
    accent.line.fill.background()
    _add_title(
        slide,
        "JurisAI | Panorama para promocao",
        f"Recorte analisado: {period_label}",
        dark=True,
    )
    hero = slide.shapes.add_textbox(Inches(0.7), Inches(1.55), Inches(6.1), Inches(1.0))
    hero_frame = hero.text_frame
    hero_frame.clear()
    p = hero_frame.paragraphs[0]
    p.text = "Dados reais de uso para apoiar divulgacao comercial, demos e parcerias."
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    _add_metric_card(slide, 0.7, 3.0, "Usuarios ativos", _format_int(active_users))
    _add_metric_card(slide, 3.2, 3.0, "Eventos", _format_int(total_events))
    _add_metric_card(slide, 5.7, 3.0, "Retencao 7D", _format_pct(context["retention_7d"]))
    _add_metric_card(slide, 8.2, 3.0, "Feature lider", context["top_feature"])
    _add_bullets(
        slide,
        "Mensagem-chave",
        [
            f"{_format_int(total_sessions)} sessoes geradas no periodo analisado.",
            f"{context['top_feature']} lidera adocao com {_format_int(context['top_feature_users'])} usuarios ativos.",
            f"{_format_pct(context['recurring_share'])} da base ja se comporta como recorrente ou power user.",
        ],
        7.1,
        1.5,
        5.2,
        2.2,
    )

    slide = presentation.slides.add_slide(blank)
    _add_title(slide, "Crescimento e engajamento", "Como a base avanca no recorte atual")
    growth_chart = _build_growth_funnel_chart(context["growth"], context["funnel"])
    _add_picture(slide, growth_chart, 0.7, 1.45, 7.2, 4.95)
    funnel = context["funnel"]
    second_step = int(funnel.iloc[1]["Usuarios"]) if len(funnel) > 1 else 0
    third_step = int(funnel.iloc[2]["Usuarios"]) if len(funnel) > 2 else 0
    _add_bullets(
        slide,
        "Destaques para venda",
        [
            f"{_format_int(second_step)} usuarios ja deram o segundo passo de uso.",
            f"{_format_int(third_step)} usuarios avancaram para 2+ sessoes.",
            f"Media de {context['actions_per_user']:.1f} acoes por usuario no periodo.",
        ],
        8.25,
        1.55,
        4.3,
        4.7,
    )

    slide = presentation.slides.add_slide(blank)
    _add_title(slide, "Features que mais puxam valor", "Adocao e confiabilidade para promocao")
    feature_chart = _build_feature_chart(context["adoption"], context["failures"])
    _add_picture(slide, feature_chart, 0.7, 1.45, 7.2, 4.95)
    failure_notes = context["failures"]
    failure_line = "Sem eventos classificados como sucesso/falha no recorte."
    if not failure_notes.empty:
        row = failure_notes.iloc[0]
        failure_line = (
            f"Maior taxa de falha observada: {row['Feature']} com {_format_pct(float(row['TaxaFalha']))}."
        )
    _add_bullets(
        slide,
        "Leituras comerciais",
        [
            f"{context['top_feature']} e a principal vitrine funcional do app.",
            f"Ha {context['adoption'].shape[0]} features com uso registrado no recorte.",
            failure_line,
        ],
        8.25,
        1.55,
        4.3,
        4.7,
    )

    slide = presentation.slides.add_slide(blank)
    _add_title(slide, "Retencao e perfil da base", "Recorrencia, cohort e perfil de uso")
    retention_chart = _build_retention_chart(context["cohort"], context["segment_counts"])
    _add_picture(slide, retention_chart, 0.7, 1.45, 7.2, 4.95)
    _add_bullets(
        slide,
        "Base pronta para escalar",
        [
            f"Retencao D+7 em {_format_pct(context['retention_7d'])}.",
            f"{_format_pct(context['power_share'])} da base no perfil power user.",
            f"Media de {context['avg_session_minutes']:.1f} min por sessao.",
            f"Saldo medio de {context['avg_consultation_credits']:.1f} creditos de consulta.",
        ],
        8.25,
        1.55,
        4.3,
        4.9,
    )

    slide = presentation.slides.add_slide(blank)
    _set_background(slide, COLOR_SOFT)
    _add_title(slide, "Narrativa sugerida para promover o aplicativo", "Resumo executivo pronto para apresentar")
    closing_bullets = [
        f"O JurisAI ativou {_format_int(active_users)} usuarios e gerou {_format_int(total_events)} eventos no recorte.",
        f"A adocao e liderada por {context['top_feature']}, com sinal claro de demanda funcional.",
        f"A recorrencia ja aparece em {_format_pct(context['recurring_share'])} da base filtrada.",
    ]
    if context["top_transition"] is not None:
        transition = context["top_transition"]
        closing_bullets.append(
            f"A jornada mais frequente vai de {transition['FeatureOrigem']} para {transition['FeatureDestino']}."
        )
    _add_bullets(slide, "Pontos para pitch", closing_bullets, 0.9, 1.4, 7.5, 3.6)

    quote = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(8.55),
        Inches(1.55),
        Inches(3.9),
        Inches(3.2),
    )
    quote.fill.solid()
    quote.fill.fore_color.rgb = COLOR_BLUE
    quote.line.fill.background()
    quote_text = slide.shapes.add_textbox(Inches(8.85), Inches(1.9), Inches(3.3), Inches(2.6))
    frame = quote_text.text_frame
    frame.clear()
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.text = "Use este deck em reunioes comerciais, demonstracoes e atualizacoes para parceiros."
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

    out = BytesIO()
    presentation.save(out)
    return out.getvalue()
