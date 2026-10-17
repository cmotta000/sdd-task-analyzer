# TaskAnalyzer — SDD (Spec-Driven Development)

Módulo de análise de tarefas e métricas de produtividade, desenvolvido seguindo o paradigma **Spec-Driven Development (SDD)**: a especificação técnica é o contrato executável que guia a geração de código assistida por IA. A IA é a executora; o desenvolvedor é o arquiteto e o homologador.

## Sobre o projeto

O TaskAnalyzer analisa um conjunto de tarefas executadas por um time ou indivíduo e produz indicadores objetivos de desempenho:

- Tempo médio de conclusão por prioridade e geral
- Taxa de atraso (tarefas concluídas após o prazo)
- Quantidade de tarefas por prioridade
- Indicadores agrupados por prioridade (baixa, média, alta)

A especificação completa do contrato de negócio e dos cenários de aceite está em [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md). As regras de governança para agentes de IA estão em [`CONTEXT_RULES.md`](CONTEXT_RULES.md).

## Estrutura do repositório

```
sdd-task-analyzer/
├── README.md              # Este arquivo
├── CONTEXT_RULES.md       # Regras persistentes de governança para agentes de IA
├── specs/
│   └── task_analyzer_spec.md   # Especificação SDD (contrato de negócio + cenários de aceite)
├── tests/
│   └── test_harness.py    # Testes automatizados (pytest) — implementados na Fase 2
├── src/
│   └── task_analyzer.py   # Código gerado via IA e homologado — implementado na Fase 2
├── .gitignore
└── requirements.txt
```

## Status do projeto (cumulativo em 3 fases)

| Fase | Descrição | Status |
|---|---|---|
| 1 — Especificação e Governança (SDD & AI Harness) | Contrato executável, cenários de aceite, CONTEXT_RULES, estrutura do repositório | ✅ Concluída |
| 2 — Implementação com IA e Versionamento | Geração de código via IA, test harness, Pull Requests no GitHub | ⬜ Próxima etapa |
| 3 — DevOps, Testes e Revisão Ética | CI/CD, Docker, testes automatizados, revisão de ética/segurança | ⬜ Pendente |

## Como este repositório deve ser usado na Fase 2

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
