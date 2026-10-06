"""PolicyMind D&O — Comparador Inteligente de Apólices (interface Streamlit).

Execute com:  streamlit run app.py
"""

from __future__ import annotations

import json
from html import escape
import logging

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.config import PROJECT_ROOT, get_settings
from src.orchestrator import OrchestratorAgent
from src.schemas import (
    RESSALVA_PADRAO,
    ApoliceExtraida,
    DocumentoProcessado,
    Etapa,
    ResultadoPipeline,
    StatusCampo,
    StatusEtapa,
    StatusItem,
)
from src.storage import PolicyStore
from src.text_utils import format_date_br, format_money_br

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="PolicyMind D&O", page_icon="📑", layout="wide", initial_sidebar_state="collapsed")


# Estilos restritos aos componentes da etapa 1; os resultados mantêm sua apresentação.
st.markdown("""
<style>
.pm-hero {background:#10233f;color:#fff;border-radius:18px;padding:26px 32px;margin:0 0 22px;border:1px solid #213b60;}
.pm-hero .pm-eyebrow {color:#8fb9ff;font-size:11px;letter-spacing:.15em;text-transform:uppercase;font-weight:700;}
.pm-hero h1 {color:#fff;font-size:36px;letter-spacing:-1.3px;padding:5px 0 3px;line-height:1.2;}
.pm-hero h2 {color:#dce8fb;font-size:19px;font-weight:500;padding:0 0 10px;}
.pm-hero p {color:#b9c9df;font-size:14px;max-width:740px;margin:0 0 15px;line-height:1.6;}
.pm-hero footer {color:#8ea5c2;font-size:11px;border-top:1px solid #2a3e59;padding-top:12px;}
.st-key-pm_upload_a,.st-key-pm_upload_b {background:#fff;border:1px solid #dce4ee!important;border-radius:15px!important;box-shadow:0 3px 12px #132b4b06;padding:18px!important;}
.pm-upload-heading {display:flex;align-items:center;gap:12px;margin-bottom:8px;}
.pm-letter {background:#edf4ff;color:#2563eb;width:36px;height:36px;display:grid;place-items:center;border-radius:10px;font-weight:700;}
.pm-upload-heading strong {display:block;color:#142c4b;font-size:17px;}
.pm-upload-heading small {display:block;color:#718097;font-size:12px;}
.st-key-pm_upload_a [data-testid="stFileUploaderDropzone"],.st-key-pm_upload_b [data-testid="stFileUploaderDropzone"] {min-height:78px;padding:10px 12px;border-radius:10px;background:#f8fafc;}
.st-key-pm_upload_a [data-testid="stFileUploaderDropzoneInstructions"] > div,.st-key-pm_upload_b [data-testid="stFileUploaderDropzoneInstructions"] > div {font-size:12px;}
.pm-upload-state {font-size:12px;color:#718097;padding:8px 0 0;overflow-wrap:anywhere;}
.pm-upload-state.ready {color:#15805b;}
.pm-bridge {text-align:center;color:#6b7c94;font-size:10px;font-weight:700;letter-spacing:.06em;padding-top:66px;line-height:1.8;}
.pm-bridge span {display:block;color:#2563eb;font-size:23px;}
.st-key-pm_cta button {width:100%;min-height:48px;background:#2563eb;border:1px solid #2563eb;border-radius:11px;font-weight:600;transition:background .18s,box-shadow .18s;}
.st-key-pm_cta button:not(:disabled):hover {background:#1e54c7;border-color:#1e54c7;box-shadow:0 4px 12px #2563eb20;}
.st-key-pm_cta button:disabled {background:#e4eaf3;border-color:#e4eaf3;color:#79879d;}
.pm-pipeline {border:1px solid #e0e6ef;border-radius:14px;background:#f9fbfe;padding:18px 20px;overflow-x:auto;}
.pm-track {display:flex;list-style:none;padding:0!important;margin:0!important;min-width:650px;}
.pm-step {flex:1;position:relative;padding:0 10px 0 0;color:#778398;--state:#8793a5;}
.pm-step:not(:last-child):after {content:"";position:absolute;top:15px;left:42px;right:12px;height:2px;background:#dce4ef;}
.pm-badge {display:grid;place-items:center;width:32px;height:32px;border-radius:50%;border:1px solid var(--state);color:var(--state);background:#fff;font-size:12px;font-weight:700;margin-bottom:10px;}
.pm-step strong {display:block;color:#193353;font-size:13px;}
.pm-step small {display:block;font-size:10px;line-height:1.7;overflow-wrap:anywhere;}
.pm-step .pm-state {color:var(--state);font-size:11px;margin-top:5px;}
.pm-step.sucesso {--state:#16835d;}.pm-step.alerta {--state:#b77910;}.pm-step.erro {--state:#c83943;}.pm-step.executando {--state:#2563eb;}
.pm-step.executando .pm-badge {animation:pm-pulse 1.8s ease-in-out infinite;background:#edf4ff;}
.pm-orchestrator {font-size:11px;color:#64748b;padding-top:14px;margin-top:14px;border-top:1px solid #e1e8f1;}
@keyframes pm-pulse {50% {box-shadow:0 0 0 5px #2563eb16;}}
@media(prefers-reduced-motion:reduce) {.pm-step.executando .pm-badge {animation:none;}}
[data-testid="stSidebar"] {background:#f7f9fc;border-right:1px solid #e0e6ef;}
[data-testid="stSidebar"] h2 {color:#193353;font-size:20px;}
[data-testid="stSidebar"] h3 {color:#193353;font-size:14px;}
.pm-sidebar-brand {color:#2563eb;font-size:11px;font-weight:700;letter-spacing:.12em;margin-bottom:12px;}
.pm-ai {border:1px solid #dce5ef;border-radius:10px;background:#fff;padding:12px;font-size:12px;color:#49617d;margin-bottom:10px;}
.pm-ai strong {display:block;color:#15805b;margin-bottom:4px;}.pm-ai.off strong {color:#b77910;}
@media(max-width:700px) {.pm-hero {padding:22px;}.pm-hero h1 {font-size:30px;}.pm-hero h2 {font-size:16px;}.pm-bridge {padding-top:0;}.pm-bridge span {display:inline;margin:0 8px;}}

.pm-hero {display:grid;grid-template-columns:minmax(0,1fr) 235px;gap:24px;padding:18px 24px;margin-bottom:8px;border-radius:14px;max-width:1120px;margin-inline:auto;}
.pm-hero h1 {font-size:30px;padding:2px 0;letter-spacing:-1px;}
.pm-hero h2 {font-size:16px;padding:0 0 6px;line-height:1.3;}
.pm-hero p {max-width:590px;font-size:12px;line-height:1.5;margin-bottom:8px;}
.pm-hero footer {padding-top:7px;font-size:10px;}
.pm-indicators {display:flex;flex-direction:column;justify-content:center;gap:8px;border-left:1px solid #2c405d;padding-left:22px;color:#d5e3f7;font-size:12px;}
.pm-indicators div {display:flex;align-items:center;gap:9px;}.pm-indicators i {width:6px;height:6px;border-radius:50%;background:#5e9aff;flex-shrink:0;}
.st-key-pm_inputs {max-width:1120px;margin-inline:auto;}
.st-key-pm_inputs [data-testid="stHorizontalBlock"] {gap:12px;}
.st-key-pm_upload_a,.st-key-pm_upload_b {padding:12px!important;border-radius:12px!important;}
.st-key-pm_upload_a [data-testid="stVerticalBlock"],.st-key-pm_upload_b [data-testid="stVerticalBlock"] {gap:6px;}
.pm-upload-heading {gap:9px;margin-bottom:0;}.pm-letter {width:30px;height:30px;border-radius:8px;font-size:13px;}
.pm-upload-heading strong {font-size:20px;line-height:1.2;font-weight:700;}
.pm-upload-heading small {display:inline-block;border:1px solid #dce6f3;background:#f2f6fc;border-radius:5px;padding:2px 6px;margin-top:4px;font-size:10px;color:#536985;}
.st-key-pm_upload_a [data-testid="stFileUploaderDropzone"],.st-key-pm_upload_b [data-testid="stFileUploaderDropzone"] {min-height:54px;padding:6px 9px;}
.st-key-pm_upload_a [data-testid="stFileUploaderDropzone"] svg,.st-key-pm_upload_b [data-testid="stFileUploaderDropzone"] svg {width:20px;height:20px;}
.pm-upload-state {padding:2px 0 0;font-size:10px;}.pm-upload-state.ready {background:#f0f8f5;border:1px solid #d4e9df;border-radius:8px;padding:7px 9px;display:flex;align-items:center;justify-content:space-between;gap:8px;}
.pm-upload-state.ready strong {font-size:12px;color:#164b3a;}.pm-file-size {white-space:nowrap;color:#35765e;font-size:10px;}
.pm-bridge {padding:0;font-size:10px;letter-spacing:0;white-space:nowrap;line-height:1;}.pm-bridge span {display:inline;font-size:17px;margin:0 5px;vertical-align:middle;}
.st-key-pm_cta {max-width:1120px;margin-inline:auto;}
.st-key-pm_cta button {min-height:40px;height:40px;border-radius:9px;background:#155eef!important;border-color:#155eef!important;color:#fff!important;}
.st-key-pm_cta button p {color:#fff!important;font-size:14px;}
.st-key-pm_cta button:not(:disabled):hover {background:#124fc6!important;border-color:#124fc6!important;box-shadow:0 2px 8px #155eef22;}
.st-key-pm_cta button:disabled {background:#467be1!important;border-color:#467be1!important;color:#fff!important;opacity:.68;}
.pm-pipeline {max-width:1120px;margin-inline:auto;padding:0;border-radius:11px;}
.pm-orchestrator {padding:7px 14px;margin:0;border-top:0;border-bottom:1px solid #dce5f1;background:#edf3fb;color:#35577e;font-size:10px;}
.pm-orchestrator strong {color:#17395f;font-weight:600;}
.pm-track {padding:12px 16px!important;min-width:590px;}
.pm-step {padding-right:8px;}.pm-step:not(:last-child):after {top:13px;left:34px;right:8px;height:2px;background:#b8c9df;}
.pm-badge {width:27px;height:27px;margin-bottom:6px;font-size:11px;}
.pm-step strong {font-size:13px;font-weight:700;color:#10233f;line-height:1.25;}
.pm-step .pm-state {font-size:10px;margin-top:3px;line-height:1.3;}
@media(max-width:700px) {.pm-hero {grid-template-columns:1fr;gap:10px;padding:16px;}.pm-indicators {border-left:0;border-top:1px solid #2c405d;padding:9px 0 0;flex-direction:row;flex-wrap:wrap;gap:12px;font-size:10px;}.pm-hero h1 {font-size:27px;}.pm-bridge {padding:3px 0;}}


/* Leitura confortável; apenas tipografia e adaptação dos componentes existentes. */
[data-testid="stAppViewContainer"] {font-size:16px;line-height:1.55;}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p {font-size:16px;line-height:1.55;}
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {font-size:15px;color:#4b5e76;line-height:1.5;}
[data-testid="stMain"] h4 {font-size:28px;line-height:1.25;}
.pm-hero {grid-template-columns:minmax(0,1fr) minmax(240px,.42fr);}
.pm-hero h1 {font-size:36px;line-height:1.2;}
.pm-hero h2 {font-size:22px;line-height:1.35;}
[data-testid="stMain"] .pm-hero p {font-size:17px;line-height:1.55;color:#d1ddef;}
.pm-hero .pm-eyebrow {font-size:14px;letter-spacing:.08em;}
.pm-hero footer {font-size:14px;color:#b7c9e2;line-height:1.5;}
.pm-indicators {font-size:15px;line-height:1.5;color:#e1ebfa;}
.pm-upload-heading strong {font-size:24px;line-height:1.25;}
.pm-upload-heading small {font-size:14px;color:#425875;line-height:1.5;}
.pm-letter {font-size:16px;}
.pm-upload-state {font-size:15px;color:#4b5e76;line-height:1.5;}
.pm-upload-state.ready {flex-wrap:wrap;}
.pm-upload-state.ready strong {font-size:16px;min-width:0;overflow-wrap:anywhere;}
.pm-file-size {font-size:14px;color:#286448;}
.st-key-pm_inputs [data-testid="stColumn"] {min-width:0;}
.st-key-pm_inputs [data-testid="stColumn"]:has(.pm-bridge) {flex:0 0 165px;}
.pm-bridge {font-size:14px;color:#425875;line-height:1.5;white-space:normal;}
.pm-bridge span {font-size:20px;}
.st-key-pm_upload_a [data-testid="stFileUploaderDropzoneInstructions"] *,
.st-key-pm_upload_b [data-testid="stFileUploaderDropzoneInstructions"] * {font-size:14px!important;line-height:1.5;overflow-wrap:anywhere;}
.st-key-pm_inputs [data-testid="stFileUploaderDropzone"] {flex-wrap:wrap;gap:8px;}
.st-key-pm_inputs [data-testid="stFileUploaderDropzone"] button p {font-size:15px;}
.st-key-pm_cta button {min-height:44px;height:auto;}
.st-key-pm_cta button p {font-size:16px!important;}
.pm-pipeline {overflow:visible;}
.pm-track {min-width:0;gap:10px;}
.pm-step {min-width:0;--state:#526278;}
.pm-step strong {font-size:17px;line-height:1.35;overflow-wrap:anywhere;}
.pm-step .pm-state {font-size:14px;line-height:1.5;}
.pm-step small {font-size:14px;line-height:1.5;color:#4b5e76;}
.pm-step .pm-technical {margin-top:5px;overflow-wrap:anywhere;}
.pm-step.alerta {--state:#895809;}.pm-step.sucesso {--state:#126844;}.pm-step.erro {--state:#b62b37;}
.pm-badge {font-size:14px;width:30px;height:30px;}
.pm-step:not(:last-child):after {top:14px;left:38px;right:4px;}
.pm-orchestrator {font-size:14px;line-height:1.5;overflow-wrap:anywhere;}
[data-testid="stSidebar"] h2 {font-size:20px;line-height:1.35;}
[data-testid="stSidebar"] h3 {font-size:19px;line-height:1.35;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-baseweb="select"] {font-size:16px;line-height:1.5;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#455b75;}
.pm-sidebar-brand {font-size:14px;}.pm-ai {font-size:16px;line-height:1.5;}
@media(max-width:1000px) {
.pm-hero {grid-template-columns:1fr;gap:14px;}
.pm-indicators {border-left:0;border-top:1px solid #2c405d;padding:12px 0 0;flex-direction:row;flex-wrap:wrap;gap:16px;font-size:15px;}
.pm-track {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 16px;}
.pm-step:nth-child(2n):after {display:none;}
}
@media(max-width:700px) {
[data-testid="stMainBlockContainer"] {padding-left:16px;padding-right:16px;}
.pm-hero {padding:18px;min-width:0;}
.pm-hero h1 {font-size:32px;}.pm-hero h2 {font-size:21px;}
[data-testid="stMain"] .pm-hero p {font-size:17px;}
.pm-indicators {font-size:15px;gap:12px;}
.st-key-pm_inputs [data-testid="stHorizontalBlock"] {flex-direction:column;align-items:stretch;gap:12px;}
.st-key-pm_inputs [data-testid="stColumn"],.st-key-pm_inputs [data-testid="stColumn"]:has(.pm-bridge) {width:100%!important;flex:1 1 auto!important;min-width:0!important;}
.pm-bridge {font-size:15px;padding:4px 0;text-align:center;}
.pm-upload-heading strong {font-size:23px;}
.pm-track {display:flex;flex-direction:column;gap:0;padding:16px!important;}
.pm-step {padding:0 0 18px 44px;min-height:64px;}
.pm-badge {position:absolute;left:0;top:0;margin:0;}
.pm-step:not(:last-child):after,.pm-step:nth-child(2n):after {display:block;left:14px;top:36px;bottom:6px;width:2px;height:auto;right:auto;}
.pm-step:last-child {padding-bottom:0;}
.pm-step strong {font-size:17px;}.pm-step .pm-state {font-size:15px;}
.pm-orchestrator {font-size:14px;padding:9px 12px;}
.st-key-pm_cta,.st-key-pm_cta button {width:100%;}
}


/* Dashboard de resultados: estilos isolados da entrada de documentos. */
.st-key-pm_results {max-width:1120px;margin-inline:auto;}
.st-key-pm_results h3 {font-size:28px;color:#142c4b;line-height:1.3;}
.pm-kpis {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:8px 0 16px;}
.pm-kpi {background:#fff;border:1px solid #dce5f0;border-radius:12px;padding:16px;box-shadow:0 2px 8px #132b4b05;min-width:0;}
.pm-kpi span {display:block;font-size:14px;color:#4b5e76;line-height:1.5;}
.pm-kpi strong {display:block;font-size:24px;color:#152e4e;line-height:1.3;margin-top:5px;overflow-wrap:anywhere;}
.pm-kpi.positive {background:#f1faf6;border-color:#c9e8d9;}.pm-kpi.positive strong {color:#146b49;}
.pm-kpi.attention {background:#fff9ef;border-color:#efdfbf;}.pm-kpi.attention strong {color:#865609;}
.st-key-pm_analysis,[class*="st-key-pm_summary_"] {border:1px solid #dce5f0;border-radius:12px;background:#fff;padding:18px;}
[class*="st-key-pm_summary_"] h4 {font-size:20px;}
.pm-detail {border:1px solid #dce5f0;border-radius:10px;padding:14px;margin:8px 0;background:#fff;}
.pm-detail-head {display:flex;justify-content:space-between;align-items:start;gap:12px;flex-wrap:wrap;color:#142c4b;font-size:17px;font-weight:600;}
.pm-detail-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:10px;}
.pm-detail-value {min-width:0;overflow-wrap:anywhere;white-space:pre-wrap;font-size:16px;line-height:1.5;color:#203b5a;}
.pm-detail-value small {display:block;font-size:14px;color:#4b5e76;margin-bottom:3px;}
.pm-status {display:inline-block;font-size:14px;font-weight:500;padding:3px 9px;border-radius:6px;background:#edf2f8;color:#405674;}
.pm-status.positive {background:#eaf7f0;color:#146b49;}.pm-status.attention {background:#fff3dc;color:#865609;}.pm-status.loss {background:#fcebee;color:#a52c40;}.pm-status.info {background:#eaf1ff;color:#2052a2;}
.st-key-pm_results [data-testid="stMarkdownContainer"] {overflow-wrap:anywhere;}
.st-key-pm_results [data-testid="stExpander"] summary p {font-size:15px;}
@media(max-width:700px) {
.pm-kpis {grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;}.pm-kpi {padding:12px;}.pm-kpi strong {font-size:21px;}
.pm-detail-grid {grid-template-columns:1fr;}.st-key-pm_results h3 {font-size:26px;}
.st-key-pm_results [data-testid="stHorizontalBlock"] {flex-direction:column;}
.st-key-pm_results [data-testid="stColumn"] {width:100%!important;flex:1 1 auto!important;min-width:0!important;}
.st-key-pm_results [data-baseweb="tab-list"] {flex-wrap:wrap;gap:4px;}
.st-key-pm_results [data-baseweb="tab"] {white-space:normal;height:auto;padding:8px;font-size:15px;}
}
@media(max-width:380px) {.pm-kpis {grid-template-columns:1fr;}}


.pm-kpis {grid-template-columns:repeat(auto-fit,minmax(165px,1fr));}
.pm-kpi {padding:12px 14px;box-shadow:none;}.pm-kpi strong {font-size:22px;}
.st-key-pm_results h3 {margin-top:26px;margin-bottom:12px;}
.st-key-pm_analysis,[class*="st-key-pm_summary_"] {border:0;padding:10px 0;background:transparent;}
.pm-detail {border:0;border-bottom:1px solid #e5ebf3;border-radius:0;padding:10px 0;box-shadow:none;}
.pm-detail-grid {margin-top:6px;gap:8px;}
.pm-notice {background:#f6f1e6;color:#765318;border-left:3px solid #ba8730;padding:8px 12px;border-radius:5px;font-size:15px;line-height:1.5;}
@media(max-width:700px) {.pm-kpis {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media(max-width:380px) {.pm-kpis {grid-template-columns:1fr;}}

</style>
""", unsafe_allow_html=True)

DATA_DIR = PROJECT_ROOT / "data"
EXTENSOES_ACEITAS = ["pdf", "png", "jpg", "jpeg", "tif", "tiff"]

ICONE_ETAPA = {
    StatusEtapa.PENDENTE: "⏸️",
    StatusEtapa.EXECUTANDO: "⏳",
    StatusEtapa.SUCESSO: "✅",
    StatusEtapa.ALERTA: "⚠️",
    StatusEtapa.ERRO: "❌",
}
ROTULO_STATUS_CAMPO = {
    StatusCampo.IGUAL: "🟢 igual",
    StatusCampo.ALTERADO: "🟡 alterado",
    StatusCampo.SOMENTE_A: "🔵 só em A",
    StatusCampo.SOMENTE_B: "🟣 só em B",
    StatusCampo.NAO_IDENTIFICADO: "Não identificado",
}
ROTULO_STATUS_ITEM = {
    StatusItem.MANTIDO: "🟢 mantido",
    StatusItem.ALTERADO: "🟡 alterado",
    StatusItem.ADICIONADO: "🟣 adicionado (só em B)",
    StatusItem.REMOVIDO: "🔴 removido (só em A)",
    StatusItem.SEM_BASE: "⚪ sem base de comparação",
}
CAMPOS_DATA = {"vigencia_inicio", "vigencia_fim"}
CAMPOS_MOEDA = {"premio_liquido", "iof", "premio_total", "lmg", "lmi"}


# ============================================================ helpers de exibição
def md_seguro(texto: str) -> str:
    """Escapa '$' para o Streamlit não interpretar 'R$ ... R$' como fórmula LaTeX."""
    return texto.replace("$", "\\$")


def fmt_valor(campo: str, valor, texto: str | None) -> str:
    if valor is None:
        return texto or "não identificado"
    if campo in CAMPOS_DATA:
        return format_date_br(valor)
    if campo in CAMPOS_MOEDA and isinstance(valor, (int, float)):
        return format_money_br(valor)
    return str(valor)


ROTULO_ETAPA = {
    StatusEtapa.PENDENTE: "aguardando",
    StatusEtapa.EXECUTANDO: "executando...",
    StatusEtapa.SUCESSO: "concluído",
    StatusEtapa.ALERTA: "concluído com alerta",
    StatusEtapa.ERRO: "erro",
}


def render_etapas(container, etapas: list[Etapa]) -> None:
    """Trilha visual dos estados recebidos do orquestrador, sem mudar o pipeline."""
    titulos = {
        "DocumentAgent": "Documento", "PolicyExtractionAgent": "Extração IA",
        "NormalizationAgent": "Normalização", "ComparisonAgent": "Comparação",
        "AnalysisAgent": "Síntese IA",
    }
    passos = []
    for numero, e in enumerate(etapas, 1):
        dur = f" · {e.duracao_s:.1f}s" if e.duracao_s is not None else ""
        passos.append(
            f'<li class="pm-step {escape(e.status.value)}" tabindex="0" title="{escape(e.agente + " · " + e.descricao)}">'
            f'<span class="pm-badge">{numero}</span>'
            f'<strong>{escape(titulos.get(e.agente, e.agente))}</strong>'
            f'<small class="pm-state">{escape(ROTULO_ETAPA[e.status] + dur)}</small>'
            f'<small class="pm-technical">{escape(e.agente)} · {escape(e.descricao)}</small></li>'
        )
    with container.container():
        st.markdown(
            '<div class="pm-pipeline"><div class="pm-orchestrator"><strong>OrchestratorAgent</strong> · Orquestrando o pipeline</div><ol class="pm-track" aria-label="Etapas dos agentes">'
            + "".join(passos)
            + '</ol></div>',
            unsafe_allow_html=True,
        )
        for e in etapas:
            if e.status == StatusEtapa.ALERTA and e.mensagem:
                pass  # Mensagens de alerta preservadas no log técnico.
            elif e.status == StatusEtapa.ERRO and e.mensagem:
                st.caption(f"{e.agente}: etapa interrompida. Consulte os detalhes técnicos.")


def render_arquivo(nome: str | None, tamanho: int | None) -> None:
    """Confirmação visual do arquivo selecionado ou do exemplo."""
    if nome is not None and tamanho is not None:
        st.markdown(
            f'<div class="pm-upload-state ready"><strong>✓ {escape(nome)}</strong>'
            f'<span class="pm-file-size">{tamanho / 1024:,.0f} KB</span></div>', unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="pm-upload-state">Aguardando documento · PDF ou imagem</div>', unsafe_allow_html=True)


def log_etapas(etapas: list[Etapa]) -> None:
    with st.expander("🗒️ Log do OrchestratorAgent"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Agente": e.agente,
                        "Status": e.status.value,
                        "Início": e.inicio.strftime("%H:%M:%S") if e.inicio else "—",
                        "Duração (s)": e.duracao_s,
                        "Mensagem": e.mensagem or "",
                    }
                    for e in etapas
                ]
            ),
            width="stretch",
            hide_index=True,
        )


def resumo_documento(col, rotulo: str, doc: DocumentoProcessado | None, ap: ApoliceExtraida | None) -> None:
    col.subheader(rotulo)
    if doc is None or ap is None:
        col.info("Documento não processado.")
        return
    metodo = {"llm": f"🤖 IA generativa ({ap.modelo_llm})", "regras": "📐 Regras (SEM IA)", "nenhum": "—"}
    col.caption(
        f"📄 {doc.nome_arquivo} · {doc.num_paginas} pág. · leitura: **{doc.metodo_extracao}** · "
        f"extração: **{metodo[ap.metodo_extracao]}**"
    )
    c1, c2 = col.columns(2)
    c1.metric("Seguradora", ap.seguradora.valor or "não identificado")
    c2.metric("Prêmio total", fmt_valor("premio_total", ap.premio_total.valor, ap.premio_total.texto_original))
    c1.metric("Início de vigência", format_date_br(ap.vigencia_inicio.valor))
    c2.metric("Fim de vigência", format_date_br(ap.vigencia_fim.valor))
    c1.metric("Prêmio líquido", fmt_valor("premio_liquido", ap.premio_liquido.valor, ap.premio_liquido.texto_original))
    c2.metric("LMG", fmt_valor("lmg", ap.lmg.valor, ap.lmg.texto_original))
    col.caption(
        f"Segurado: {ap.segurado.valor or 'não identificado'} · Tipo: {ap.tipo_documento.valor or 'não identificado'} · "
        f"{len(ap.coberturas)} coberturas · {len(ap.extensoes)} extensões · "
        f"{len(ap.clausulas_relevantes)} cláusulas · {len(ap.exclusoes)} exclusões"
    )
    if ap.observacoes or ap.avisos or doc.avisos:
        with col.expander(f"Observações e avisos ({len(ap.observacoes) + len(ap.avisos) + len(doc.avisos)})"):
            for o in ap.observacoes:
                st.markdown(f"- 📝 {o}")
            for a in doc.avisos + ap.avisos:
                st.markdown(f"- ⚠️ {a}")


def tabela_campos(res: ResultadoPipeline, secao: str) -> pd.DataFrame:
    comp = res.comparacao
    linhas = []
    for d in comp.campos:
        if d.secao != secao:
            continue
        var = ""
        if d.variacao_percentual is not None:
            var = f"{d.variacao_percentual:+.2f}%".replace(".", ",")
        linhas.append(
            {
                "Campo": d.rotulo,
                comp.rotulo_a: fmt_valor(d.campo, d.valor_a, d.texto_a),
                comp.rotulo_b: fmt_valor(d.campo, d.valor_b, d.texto_b),
                "Status": ROTULO_STATUS_CAMPO[d.status],
                "Variação": var,
                f"Fonte ({comp.rotulo_a})": d.fonte_a or "—",
                f"Fonte ({comp.rotulo_b})": d.fonte_b or "—",
            }
        )
    return pd.DataFrame(linhas)


def tabela_itens(res: ResultadoPipeline, secoes: list[str]) -> pd.DataFrame:
    comp = res.comparacao
    linhas = []
    for i in comp.itens:
        if i.secao not in secoes:
            continue
        ausente = "não identificado" if i.status == StatusItem.SEM_BASE else "ausente"
        linhas.append(
            {
                "Item (padronizado)": i.nome,
                "Seção": i.secao,
                f"Limite {comp.rotulo_a}": i.limite_a or ("—" if i.nome_a else ausente),
                f"Limite {comp.rotulo_b}": i.limite_b or ("—" if i.nome_b else ausente),
                "Status": ROTULO_STATUS_ITEM[i.status],
                f"Nome original ({comp.rotulo_a})": i.nome_a or "—",
                f"Nome original ({comp.rotulo_b})": i.nome_b or "—",
                f"Fonte ({comp.rotulo_a})": i.fonte_a or "—",
                f"Fonte ({comp.rotulo_b})": i.fonte_b or "—",
            }
        )
    return pd.DataFrame(linhas)


def badge_status(texto: str) -> str:
    """Traduz apenas os rótulos visuais; não modifica os estados do pipeline."""
    rotulos = {
        "🟢 igual": ("Igual", "positive"), "🟢 mantido": ("Igual · mantido", "positive"),
        "🟡 alterado": ("Alterado", "attention"), "🔵 só em A": ("Somente A", "info"),
        "🟣 só em B": ("Somente B", "info"), "🟣 adicionado (só em B)": ("Adicionado", "info"),
        "🔴 removido (só em A)": ("Removido", "loss"), "⚪ sem base de comparação": ("Sem base", "attention"),
        "Não identificado": ("Não identificado", ""),
    }
    nome, cor = rotulos.get(texto, (texto, ""))
    return f'<span class="pm-status {cor}">{escape(nome)}</span>'


def mostrar_tabela(df: pd.DataFrame, vazio: str, resultado: ResultadoPipeline) -> None:
    """Filtra apenas a apresentação; mantém os campos ausentes acessíveis."""
    if df.empty:
        st.caption(vazio)
        return
    ausentes = df[df["Status"] == "Não identificado"]
    visiveis = df[df["Status"] != "Não identificado"]
    if visiveis.empty:
        st.caption(vazio)
    for linha in visiveis.to_dict(orient="records"):
        titulo = linha.get("Campo", linha.get("Item (padronizado)", "Comparação"))
        valores = "".join(
            f'<div class="pm-detail-value"><small>{escape(str(k))}</small>{escape(str(v))}</div>'
            for k, v in linha.items()
            if v != "" and k not in {"Campo", "Item (padronizado)", "Status"} and not k.startswith(("Fonte (", "Nome original ("))
        )
        st.markdown(
            f'<article class="pm-detail"><div class="pm-detail-head">{escape(str(titulo))}'
            + badge_status(str(linha.get("Status", "")))
            + f'</div><div class="pm-detail-grid">{valores}</div></article>', unsafe_allow_html=True,
        )
        if "Campo" in linha:
            nomes = [d.campo for d in resultado.comparacao.campos if d.rotulo == titulo]
            render_evidencias(resultado, nomes)
        else:
            render_evidencias(resultado, [], item_nome=str(titulo), secao=str(linha.get("Seção", "")))
    if not ausentes.empty:
        with st.expander("Ver campos não identificados"):
            for linha in ausentes.to_dict(orient="records"):
                st.markdown(f"- {md_seguro(str(linha.get('Campo', 'Campo')))} · A e B não identificados")


def render_evidencias(res: ResultadoPipeline, campos: list[str] | None = None,
                       item_nome: str | None = None, secao: str | None = None) -> None:
    """Somente evidência contextual; nunca percorre o texto completo do documento."""
    with st.expander("Ver evidência"):
        encontrou = False
        for indice, ap in enumerate(res.apolices):
            if ap is None:
                continue
            doc = res.documentos[indice] if indice < len(res.documentos) else None
            nome_doc = doc.nome_arquivo if doc else (res.comparacao.rotulo_a if indice == 0 else res.comparacao.rotulo_b) if res.comparacao else f"Documento {'A' if indice == 0 else 'B'}"
            evidencias = []
            for nome in campos or []:
                campo = getattr(ap, nome, None)
                if campo is not None:
                    evidencias.append((nome, campo, campo.texto_original))
            if item_nome and res.comparacao:
                for d in res.comparacao.itens:
                    if d.nome != item_nome or d.secao != secao:
                        continue
                    for lista in (ap.coberturas, ap.extensoes, ap.exclusoes, ap.clausulas_relevantes):
                        for item in lista:
                            if item.chave == d.chave or item.nome == (d.nome_a if indice == 0 else d.nome_b):
                                original = " · ".join(str(v) for v in (item.nome, item.descricao, item.limite, item.franquia) if v)
                                evidencias.append((item.nome, item, original))
            for titulo, valor, original in evidencias:
                encontrou = True
                st.markdown(f"**{md_seguro(nome_doc)} · {md_seguro(titulo)}**")
                if valor.pagina is None and not valor.trecho:
                    st.caption("Evidência não disponível para este campo.")
                    continue
                st.caption(f"Página: {valor.pagina if valor.pagina is not None else 'não disponível'}")
                st.text(f"Trecho de origem: {valor.trecho or 'Não disponível'}")
                st.text(f"Texto original extraído: {original or 'Não disponível'}")
        if not encontrou:
            st.caption("Evidência não disponível para este campo.")


def render_visao_executiva(res: ResultadoPipeline) -> None:
    st.markdown("### Visão executiva da renovação")
    a = res.apolices[0] if len(res.apolices) > 0 else None
    b = res.apolices[1] if len(res.apolices) > 1 else None
    def valor(ap, nome):
        campo = getattr(ap, nome) if ap else None
        return fmt_valor(nome, campo.valor, campo.texto_original) if campo else "Não identificado"
    premio = next((d for d in res.comparacao.campos if d.campo == "premio_total"), None) if res.comparacao else None
    variacao = premio.variacao_percentual if premio else None
    cor = "positive" if variacao is not None and variacao < 0 else "attention" if variacao is not None and variacao > 0 else ""
    kpis = []
    for ap, titulo, nome in ((a, "Seguradora anterior", "seguradora"), (b, "Nova seguradora", "seguradora"),
                              (a, "Prêmio anterior · total", "premio_total"), (b, "Novo prêmio · total", "premio_total")):
        if ap and getattr(ap, nome).encontrado:
            kpis.append((titulo, valor(ap, nome), ""))
    if variacao is not None:
        kpis.append(("Variação do prêmio total", f"{variacao:+.2f}%".replace(".", ","), cor))
    elif a and b and (a.premio_total.encontrado != b.premio_total.encontrado):
        kpis.append(("Variação do prêmio total", "Sem base suficiente", ""))
    if len(kpis) < 5 and any(ap and ap.lmg.encontrado for ap in (a, b)):
        limites = " · ".join(f"{lado}: {valor(ap, 'lmg')}" for ap, lado in ((a, "A"), (b, "B")) if ap and ap.lmg.encontrado)
        kpis.append(("LMG", limites, ""))
    st.markdown('<div class="pm-kpis">' + "".join(
        f'<div class="pm-kpi {cor}"><span>{escape(titulo)}</span><strong>{escape(str(v))}</strong></div>'
        for titulo, v, cor in kpis
    ) + '</div>', unsafe_allow_html=True)
    if any(ap and ap.premio_total.encontrado for ap in (a, b)):
        st.caption("Redução de preço, por si só, não significa melhora de cobertura.")
    if kpis:
        render_evidencias(res, ["seguradora", "premio_total", "lmg"])
    metricas = [(nome, titulo) for nome, titulo in (("premio_liquido", "Prêmio líquido"), ("iof", "IOF"), ("premio_total", "Prêmio total"))
                if a and b and isinstance(getattr(a, nome).valor, (int, float)) and not isinstance(getattr(a, nome).valor, bool)
                and isinstance(getattr(b, nome).valor, (int, float)) and not isinstance(getattr(b, nome).valor, bool)]
    if not any(ap and (ap.premio_total.encontrado or ap.premio_liquido.encontrado or ap.iof.encontrado) for ap in (a, b)):
        st.caption("Dados financeiros não identificados nos documentos analisados.")
    elif metricas:
        st.markdown("### Comparativo financeiro")
        fig = go.Figure()
        for ap, lado, cor_barra in ((a, "A · Anterior", "#8095b2"), (b, "B · Renovação", "#155eef")):
            valores = [getattr(ap, nome).valor for nome, _ in metricas]
            fig.add_bar(name=lado, x=[titulo for _, titulo in metricas], y=valores, marker_color=cor_barra,
                        customdata=[format_money_br(v) for v in valores], hovertemplate='%{x}<br>%{customdata}<extra>%{fullData.name}</extra>')
        fig.update_layout(barmode="group", height=330, margin=dict(l=10,r=10,t=15,b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(size=15,color="#203b5a"), legend=dict(orientation="h",y=-.2,x=0),
                          yaxis=dict(title="Valor (R$)",gridcolor="#e7edf5",zeroline=False),xaxis=dict(fixedrange=True))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar":False,"responsive":True,"scrollZoom":False})
        render_evidencias(res, [nome for nome, _ in metricas])


def render_analise(res: ResultadoPipeline) -> None:
    an = res.analise
    with st.container(key="pm_analysis"):
        st.markdown("### Análise executiva")
        if an and an.gerado_por_ia:
            st.caption(f"Análise gerada por IA · modelo {an.modelo_llm or 'não identificado'}")
            st.markdown(md_seguro(an.sintese or "Síntese não identificada."))
        else:
            st.caption("IA generativa indisponível. Abaixo estão apenas os fatos objetivos identificados pelo sistema.")
    blocos = []
    if an and an.gerado_por_ia:
        blocos.extend([("Ganhos comprovados", an.ganhos or ["Nenhum ganho informado pelo AnalysisAgent."], "ganhos"),
                       ("Pontos de atenção", an.pontos_atencao or ["Nenhum ponto informado pelo AnalysisAgent."], "atencao")])
        if an.perdas:
            blocos.append(("Perdas identificadas", an.perdas, "perdas"))
    if an and an.destaques_regras:
        blocos.append(("Fatos objetivos da comparação", an.destaques_regras, "fatos"))
    if res.comparacao:
        sem_base = [f"{d.rotulo}: identificado somente no documento {'A' if d.status == StatusCampo.SOMENTE_A else 'B'}" for d in res.comparacao.campos
                    if d.status in (StatusCampo.SOMENTE_A, StatusCampo.SOMENTE_B)]
        sem_base.extend(f"{i.secao} · {i.nome}: sem base de comparação" for i in res.comparacao.itens if i.status == StatusItem.SEM_BASE)
        if sem_base:
            blocos.append(("Sem base suficiente", sem_base, "sem_base"))
    for inicio in range(0, len(blocos), 2):
        cols = st.columns(2)
        for col, (titulo, textos, chave) in zip(cols, blocos[inicio:inicio + 2]):
            with col, st.container(key=f"pm_summary_{chave}"):
                st.markdown(f"#### {titulo}")
                if chave == "ganhos":
                    st.caption("Conclusões reportadas pelo AnalysisAgent; confira as evidências disponíveis.")
                limite = 5 if chave == "atencao" else 4
                for texto in textos[:limite]:
                    st.markdown(f"- {md_seguro(texto)}")
                if len(textos) > limite:
                    with st.expander("Ver demais pontos"):
                        for texto in textos[limite:]:
                            st.markdown(f"- {md_seguro(texto)}")
    st.caption(an.ressalva if an else RESSALVA_PADRAO)


# ===================================================================== sidebar
settings = get_settings()
with st.sidebar:
    st.markdown('<div class="pm-sidebar-brand">POLICYMIND D&amp;O</div>', unsafe_allow_html=True)
    st.header("Configuração")
    st.subheader("Status da IA")
    if settings.llm_available:
        st.markdown('<div class="pm-ai"><strong>Chave configurada</strong>IA generativa disponível na configuração.</div>', unsafe_allow_html=True)
    else:
        st.caption("IA generativa indisponível.")
    st.subheader("Modelo")
    st.caption(f"`{settings.openai_model}`")
    st.caption(f"OCR (fallback): {'ativado' if settings.ocr_enabled else 'desativado'} · idioma `{settings.ocr_lang}`")

    st.divider()
    st.subheader("Exemplos")
    exemplos = sorted(p for p in DATA_DIR.glob("*") if p.suffix.lower().lstrip(".") in EXTENSOES_ACEITAS)
    usar_exemplos = st.toggle("Usar arquivos da pasta data/", value=False, disabled=not exemplos)
    sel_a = sel_b = None
    if usar_exemplos and exemplos:
        nomes = [p.name for p in exemplos]
        idx_a = next((i for i, n in enumerate(nomes) if "TOKYO" in n.upper()), 0)
        idx_b = next((i for i, n in enumerate(nomes) if "SUMITOMO" in n.upper()), min(1, len(nomes) - 1))
        sel_a = st.selectbox("Apólice A (referência)", nomes, index=idx_a)
        sel_b = st.selectbox("Apólice B (comparada)", nomes, index=idx_b)

    st.divider()
    st.subheader("Cache")
    st.caption(f"Cache SQLite: {'ativado' if settings.cache_enabled else 'desativado'}")
    if settings.cache_enabled:
        with st.expander("Apólices armazenadas (SQLite)"):
            try:
                hist = PolicyStore(settings.cache_path).list_all()
                st.dataframe(pd.DataFrame(hist), hide_index=True) if hist else st.caption("Nenhuma ainda.")
            except Exception as exc:
                st.caption(f"Indisponível: {exc}")

# ===================================================================== cabeçalho
st.markdown("""
<section class="pm-hero"><div class="pm-hero-copy">
<div class="pm-eyebrow">Comparação inteligente de apólices</div>
<h1>PolicyMind D&amp;O</h1>
<h2>Inteligência aplicada à comparação de apólices</h2>
<p>Analise duas apólices D&amp;O, identifique diferenças relevantes e gere uma síntese executiva com rastreabilidade.</p>
<footer>Insight Builders · InsurMinds / I2A2</footer></div>
<div class="pm-indicators" aria-label="Recursos"><div><i aria-hidden="true"></i>Comparação lado a lado</div><div><i aria-hidden="true"></i>Evidências por página</div><div><i aria-hidden="true"></i>Síntese com IA</div></div>
</section>
""", unsafe_allow_html=True)

with st.container(key="pm_inputs"):
    col_a, ponte, col_b = st.columns([1, 0.23, 1], gap="small", vertical_alignment="center")
    with ponte:
        st.markdown('<div class="pm-bridge">Anterior <span>→</span> Renovação</div>', unsafe_allow_html=True)
    with col_a, st.container(border=True, key="pm_upload_a"):
        st.markdown('<div class="pm-upload-heading"><span class="pm-letter">A</span><div><strong>Apólice A</strong><small>Anterior / referência</small></div></div>', unsafe_allow_html=True)
        up_a = st.file_uploader("Apólice A (referência / anterior)", type=EXTENSOES_ACEITAS, disabled=usar_exemplos, label_visibility="collapsed")
        render_arquivo(sel_a, (DATA_DIR / sel_a).stat().st_size) if usar_exemplos and sel_a else render_arquivo(up_a.name if up_a else None, up_a.size if up_a else None)
    with col_b, st.container(border=True, key="pm_upload_b"):
        st.markdown('<div class="pm-upload-heading"><span class="pm-letter">B</span><div><strong>Apólice B</strong><small>Nova / renovação</small></div></div>', unsafe_allow_html=True)
        up_b = st.file_uploader("Apólice B (comparada / renovação)", type=EXTENSOES_ACEITAS, disabled=usar_exemplos, label_visibility="collapsed")
        render_arquivo(sel_b, (DATA_DIR / sel_b).stat().st_size) if usar_exemplos and sel_b else render_arquivo(up_b.name if up_b else None, up_b.size if up_b else None)

arquivos: list[tuple[str, bytes]] = []
if usar_exemplos and sel_a and sel_b:
    arquivos = [(sel_a, (DATA_DIR / sel_a).read_bytes()), (sel_b, (DATA_DIR / sel_b).read_bytes())]
elif up_a and up_b:
    arquivos = [(up_a.name, up_a.getvalue()), (up_b.name, up_b.getvalue())]

with st.container(key="pm_cta"):
    executar = st.button("Analisar apólices", type="primary", disabled=len(arquivos) < 2, width="stretch")

st.markdown("#### Etapas dos agentes")
painel_etapas = st.empty()

if executar:
    orq = OrchestratorAgent(settings=settings, on_update=lambda etapas: render_etapas(painel_etapas, etapas))
    with st.spinner("Processando documentos..."):
        st.session_state["resultado"] = orq.run(arquivos)

res: ResultadoPipeline | None = st.session_state.get("resultado")
if res is None:
    from src.orchestrator import ETAPAS

    render_etapas(painel_etapas, [Etapa(agente=a, descricao=d) for a, d in ETAPAS])
    st.info(
        "Envie duas apólices (PDF ou imagem) ou selecione os exemplos na barra lateral e clique em **Analisar apólices**."
    )
    st.stop()

render_etapas(painel_etapas, res.etapas)
if res.erro_fatal:
    st.error("O processamento foi interrompido. Consulte os detalhes técnicos da execução.")

# ===================================================================== resultados
with st.container(key="pm_results"):
    contingencia = bool(
        any(ap and ap.metodo_extracao == "regras" for ap in res.apolices)
        or (res.analise and not res.analise.gerado_por_ia
            and (res.analise.erro or res.analise.destaques_regras))
    )
    if contingencia:
        st.markdown('<div class="pm-notice">Execução em modo de contingência — sem IA generativa.</div>', unsafe_allow_html=True)
    if res.erro_fatal or not res.sucesso:
        st.warning("Pipeline incompleto. Os resultados parciais abaixo não representam uma análise concluída.")
    if res.apolices or res.comparacao:
        render_visao_executiva(res)
    if res.analise or res.comparacao:
        render_analise(res)
    if res.apolices:
        with st.expander("Resumo completo dos documentos"):
            rot = [res.comparacao.rotulo_a, res.comparacao.rotulo_b] if res.comparacao else ["Apólice A", "Apólice B"]
            cols = st.columns(2)
            for i in range(2):
                doc = res.documentos[i] if i < len(res.documentos) else None
                ap = res.apolices[i] if i < len(res.apolices) else None
                resumo_documento(cols[i], f"{'A' if i == 0 else 'B'} · {rot[i]}", doc, ap)
    if res.comparacao:
        st.markdown("### Comparação detalhada")
        abas = st.tabs(
            ["Dados Gerais", "Limites", "Prêmio", "Franquias", "Coberturas", "Extensões", "Exclusões", "Pontos de Atenção"]
        )
        with abas[0]:
            mostrar_tabela(tabela_campos(res, "Dados Gerais"), "Sem dados gerais.", res)
        with abas[1]:
            mostrar_tabela(tabela_campos(res, "Limites"), "Sem limites identificados.", res)
        with abas[2]:
            mostrar_tabela(tabela_campos(res, "Prêmio"), "Sem dados de prêmio.", res)
        with abas[3]:
            mostrar_tabela(tabela_campos(res, "Franquias"), "Sem dados de franquia.", res)
        with abas[4]:
            mostrar_tabela(tabela_itens(res, ["Coberturas"]), "Nenhuma cobertura identificada.", res)
        with abas[5]:
            mostrar_tabela(
                tabela_itens(res, ["Extensões", "Cláusulas relevantes"]),
                "Nenhuma extensão ou cláusula identificada.", res,
            )
        with abas[6]:
            mostrar_tabela(tabela_itens(res, ["Exclusões"]), "Nenhuma exclusão identificada.", res)
        with abas[7]:
            an = res.analise
            pontos = []
            if an and an.gerado_por_ia:
                pontos.extend(("Pontos de atenção (IA generativa)", x) for x in an.pontos_atencao)
            if an:
                pontos.extend(("Fatos objetivos da comparação (calculados por regras, sem IA)", x) for x in an.destaques_regras)
            def exibir_pontos(itens):
                origem_anterior = None
                for origem, texto in itens:
                    if origem != origem_anterior:
                        st.markdown(f"**{origem}**")
                        origem_anterior = origem
                    st.markdown(f"- {md_seguro(texto)}")
            exibir_pontos(pontos[:5])
            if len(pontos) > 5:
                with st.expander("Ver demais pontos"):
                    exibir_pontos(pontos[5:])
            st.caption(f"⚖️ {RESSALVA_PADRAO}")

        ausentes = [d for d in res.comparacao.campos if d.status in (StatusCampo.NAO_IDENTIFICADO, StatusCampo.SOMENTE_A, StatusCampo.SOMENTE_B)]
        if ausentes:
            with st.expander("Informações não identificadas"):
                for d in ausentes:
                    lado = "A e B" if d.status == StatusCampo.NAO_IDENTIFICADO else "B" if d.status == StatusCampo.SOMENTE_A else "A"
                    st.markdown(f"- {md_seguro(d.rotulo)} · não identificado em {lado}")
    with st.expander("Detalhes técnicos da execução"):
        if not settings.llm_available:
            st.caption("OPENAI_API_KEY não configurada. A extração e a síntese por IA ficam indisponíveis.")
        if res.erro_fatal:
            st.text(res.erro_fatal)
        if res.analise and res.analise.erro:
            st.text(res.analise.erro)
        if res.comparacao:
            for aviso in res.comparacao.avisos:
                st.text(aviso)
        st.markdown("**JSON extraído e metadados**")
        log_etapas(res.etapas)
        for i, ap in enumerate(res.apolices):
            st.markdown(f"**Apólice {'A' if i == 0 else 'B'}**")
            if ap:
                st.caption(f"Modelo de IA: {ap.modelo_llm or 'não identificado'} · Método de extração: {ap.metodo_extracao} · Normalizado: {ap.normalizado}")
            doc = res.documentos[i] if i < len(res.documentos) else None
            if doc:
                st.caption(f"Leitura: {doc.metodo_extracao} · {doc.num_paginas} páginas · SHA-256: {doc.hash_sha256}")
            st.json(ap.model_dump(mode="json") if ap else {}, expanded=False)
        if res.analise:
            st.caption(f"Modelo da análise: {res.analise.modelo_llm or 'não identificado'}")
        if res.comparacao:
            st.markdown("**Comparação**")
            st.json(res.comparacao.model_dump(mode="json"), expanded=False)
        st.download_button(
            "Baixar resultado completo (JSON)",
            data=json.dumps(res.model_dump(mode="json"), ensure_ascii=False, indent=2),
            file_name="policymind_resultado.json", mime="application/json",
        )
