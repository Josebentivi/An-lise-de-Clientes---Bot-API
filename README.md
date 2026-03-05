# Analise de Clientes - JurisAI

Dashboard Streamlit para analisar a base de usuarios e os eventos de uso da plataforma JurisAI.

## O que o app entrega

- filtros globais por periodo, feature, status e segmento de usuario
- visao geral com crescimento, base acumulada e creditos por cohort/segmento
- analise de retencao com distribuicao por usuario e heatmap de cohorts mensais
- adocao por feature com usuarios unicos, volume de eventos e taxa de falha
- jornada com funil de engajamento, metricas de sessao e transicoes entre features
- quadro de qualidade dos dados com duplicatas, datas invalidas e amostras recentes
- exportacao de apresentacao `.pptx` com narrativa promocional baseada nos filtros atuais

## Estrutura principal

- `visualizardados.py`: app Streamlit e renderizacao dos paineis
- `analytics.py`: camada analitica reutilizavel, sem dependencias de UI
- `tests/test_analytics.py`: testes unitarios da logica de classificacao e agregacao

## Como executar

1. Instale as dependencias:

```bash
python -m pip install -r requirements.txt
```

2. Configure a chave da API:

- em `Settings > Secrets`, com a chave `CHAVE`
- ou por variavel de ambiente `CHAVE`

Variaveis opcionais:

- `JURISAI_API_URL`: endpoint da API
- `JURISAI_TIMEOUT_SECONDS`: timeout de requisicao

3. Rode o app:

```bash
streamlit run visualizardados.py
```

## Validacao local

```bash
python -m unittest discover -s tests -v
python -c "import analytics, visualizardados; print('imports ok')"
```
