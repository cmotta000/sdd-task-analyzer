# TaskAnalyzer — SDD (Spec-Driven Development)

![status](https://img.shields.io/badge/pytest-27%20passed-brightgreen) ![python](https://img.shields.io/badge/python-3.11%2B-blue)

Módulo de análise de tarefas e métricas de produtividade, desenvolvido seguindo o paradigma **Spec-Driven Development (SDD)**: a especificação técnica é o contrato executável que guia a geração de código assistida por IA. A IA é a executora; o desenvolvedor é o arquiteto e o homologador.

## Sobre o projeto

O TaskAnalyzer analisa um conjunto de tarefas executadas por um time ou indivíduo e produz indicadores objetivos de desempenho:

- Tempo médio de conclusão por prioridade e geral
- Taxa de atraso (tarefas concluídas após o prazo)
- Quantidade de tarefas por prioridade
- Indicadores agrupados por prioridade (baixa, média, alta)

A especificação completa do contrato de negócio e dos cenários de aceite está em [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md). As regras de governança para agentes de IA estão em [`CONTEXT_RULES.md`](CONTEXT_RULES.md).

## Como executar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -v
```

### Executar com Docker (Fase 3)

```bash
docker compose run --rm tests
```

Ou, sem o Compose: `docker build -t sdd-task-analyzer . && docker run --rm sdd-task-analyzer`. A imagem usa `python:3.11-slim` e o `CMD` executa `pytest tests/test_harness.py -v`.

### Integração contínua

O workflow `.github/workflows/ci.yml` roda em `push` e `pull_request` nas branches `main` e `develop` (ubuntu-latest, Python 3.11): instala `requirements.txt` e executa `pytest tests/test_harness.py -v`.

Uso do módulo (Python 3.11+, somente biblioteca padrão):

```python
from datetime import datetime, timezone
from src.task_analyzer import analyze_tasks, TaskValidationError

tarefas = [{
    "id_tarefa": 1, "prioridade": "alta", "status": "concluída",
    "data_criacao": datetime(2026, 1, 1, 8, tzinfo=timezone.utc),
    "data_inicio": datetime(2026, 1, 1, 9, tzinfo=timezone.utc),
    "data_conclusao": datetime(2026, 1, 1, 10, tzinfo=timezone.utc),
    "prazo": datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
}]
print(analyze_tasks(tarefas))
```

### Decisões de interpretação do contrato

- `quantidade_tarefas` = tarefas **concluídas e válidas** efetivamente consideradas no cálculo.
- Registro concluído com datas ausentes ou inconsistentes (`data_conclusao` < `data_inicio` ou < `data_criacao`) é descartado com log `WARNING` (nota de reconciliação, item a).
- Lote sem nenhuma tarefa concluída válida (inclui lote vazio) dispara `TaskValidationError` (item b / Cenário 2).
- Prioridade sem tarefas concluídas retorna `0.0 / 0.0 / 0` sem exceção.
- Campo ausente, tipo, enum ou `id_tarefa <= 0` inválidos disparam `TaskValidationError`. `datetime` sem fuso é tratado como UTC.

## Estrutura do repositório

```
sdd-task-analyzer/
├── README.md              # Este arquivo
├── CONTEXT_RULES.md       # Regras persistentes de governança para agentes de IA
├── .github/
│   └── workflows/
│       └── ci.yml         # Pipeline CI (GitHub Actions)
├── Dockerfile             # Imagem python:3.11-slim que executa o pytest
├── docker-compose.yml     # Serviço "tests" (docker compose run --rm tests)
├── .dockerignore
├── specs/
│   └── task_analyzer_spec.md   # Especificação SDD (contrato de negócio + cenários de aceite)
├── tests/
│   └── test_harness.py    # Testes automatizados (pytest) — Cenários 1 e 2 + casos de borda
├── src/
│   └── task_analyzer.py   # analyze_tasks e TaskValidationError (gerado via IA e homologado)
├── .gitignore
└── requirements.txt
```

## Status do projeto (cumulativo em 3 fases)

| Fase | Descrição | Status |
|---|---|---|
| 1 — Especificação e Governança (SDD & AI Harness) | Contrato executável, cenários de aceite, CONTEXT_RULES, estrutura do repositório | ✅ Concluída |
| 2 — Implementação com IA e Versionamento | Geração de código via IA, test harness, Pull Requests no GitHub | ✅ Concluída |
| 3 — DevOps, Testes e Revisão Ética | CI/CD (GitHub Actions), Docker, testes automatizados, revisão de ética/segurança | ✅ Concluída |

## Como este repositório foi usado na Fase 2

1. Ler integralmente `specs/task_analyzer_spec.md` antes de solicitar geração de código a um assistente de IA.
2. Fornecer o `CONTEXT_RULES.md` como contexto persistente para o agente de IA.
3. Implementar `src/task_analyzer.py` e os testes em `tests/test_harness.py`, cobrindo todos os casos de teste derivados dos cenários de aceite (seção 2.1 da especificação).
4. Submeter todo código gerado ao Plano de Homologação Humana abaixo antes do merge.

## Plano de Homologação Humana

Todo código gerado pela IA será submetido a uma revisão crítica humana antes de ser aceito e versionado, seguindo estes passos, em ordem:

1. Executar a suíte de testes automatizados (pytest) e verificar a cobertura dos cenários de aceite;
2. Revisar a conformidade do código com o Contrato Executável de Interface e com o `CONTEXT_RULES.md`;
3. Analisar a qualidade do código: legibilidade, tratamento de erros, aderência a PEP 8, type hints e docstrings;
4. Validar que não há violação de nenhuma das Proibições Explícitas (`CONTEXT_RULES.md`, seção 2);
5. Executar testes manuais complementares em casos de borda não cobertos automaticamente;
6. Somente após aprovação em todos os itens acima, o código é commitado e versionado no repositório.

Esse processo garante que a IA seja uma ferramenta produtiva, mas que a decisão final e a responsabilidade técnica permaneçam humanas.

## Estratégia de Versionamento

- Git Flow simplificado: branches `main`, `develop` e `feature/*`;
- Commits pequenos e descritivos, seguindo mensagens no padrão imperativo (ex.: "adiciona cálculo de taxa de atraso");
- Pull Requests obrigatórios para revisão e aprovação antes do merge;
- Revisões obrigatórias (homologação humana, seção acima) antes de qualquer merge para `develop`/`main`;
- Tags de versão (ex.: `v0.1.0`) para releases importantes.
