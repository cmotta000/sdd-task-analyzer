# Especificação SDD — TaskAnalyzer

**Módulo:** Análise de Tarefas e Métricas de Produtividade
**Versão da especificação:** 1.0.0

> Esta especificação é o contrato executável que guia a geração de código assistida por IA. Toda implementação em `src/task_analyzer.py` e todos os testes em `tests/test_harness.py` devem derivar estritamente deste documento. As regras sobre **como** codar (não o que fazer) estão em [`CONTEXT_RULES.md`](../CONTEXT_RULES.md).

## 1. Visão Geral e Contrato de Negócio

### 1.1 Propósito do Módulo TaskAnalyzer

O TaskAnalyzer é um módulo avançado de métricas e produtividade que analisa um conjunto de tarefas executadas por um time ou indivíduo e produz indicadores objetivos de desempenho:

- Analisar tarefas executadas e gerar métricas de produtividade;
- Calcular o tempo médio de conclusão por tipo/prioridade;
- Identificar a taxa de atraso (tarefas concluídas após o prazo);
- Gerar indicadores por prioridade (baixa, média, alta);
- Fornecer métricas objetivas para tomada de decisão e melhoria contínua do processo.

### 1.2 Contrato Executável de Interface

O contrato abaixo é normativo: toda geração de código pela IA deve respeitar estritamente os tipos, obrigatoriedade e restrições descritos. Qualquer alteração de assinatura, tipos ou nomes de campos exige nova aprovação do homologador humano.

#### 1.2.1 Entradas (Inputs)

| Campo | Tipo | Obrigatório | Descrição / Restrições |
|---|---|---|---|
| `id_tarefa` | int | Sim | Identificador único da tarefa (> 0) |
| `data_criacao` | datetime | Sim | Data/hora de criação da tarefa (UTC) |
| `data_inicio` | datetime | Não | Data/hora de início da execução |
| `data_conclusao` | datetime | Não | Data/hora de conclusão da execução |
| `prazo` | datetime | Sim | Data/hora limite para conclusão |
| `prioridade` | str (enum) | Sim | Valores permitidos: `baixa`, `média`, `alta` |
| `status` | str (enum) | Sim | Valores permitidos: `concluída`, `pendente`, `cancelada` |

#### 1.2.2 Saídas (Outputs)

| Campo | Tipo | Descrição |
|---|---|---|
| `tempo_medio_conclusao_min` | float | Tempo médio de conclusão em minutos (por prioridade e geral) |
| `taxa_atraso_percentual` | float | Percentual de tarefas concluídas após o prazo (por prioridade e geral) |
| `quantidade_tarefas` | int | Total de tarefas consideradas na análise (por prioridade e geral) |
| `indicadores_por_prioridade` | dict | Estrutura com as métricas acima agrupadas por prioridade (baixa, média, alta) |

#### 1.2.3 Regras de Negócio e Restrições

- Considerar apenas tarefas com `status = "concluída"` para o cálculo de tempo médio e taxa de atraso;
- Tempo de conclusão = `data_conclusao − data_inicio` (expresso em minutos);
- Uma tarefa é considerada em atraso quando `data_conclusao > prazo`;
- Tarefas com datas inconsistentes no registro individual (ex.: `data_conclusao` anterior a `data_inicio`) devem ser ignoradas no cálculo agregado e contabilizadas separadamente como registros descartados — ver nota de reconciliação abaixo;
- A divisão por zero (ausência de tarefas concluídas no conjunto de entrada) deve ser tratada explicitamente, sem interromper a aplicação de forma não controlada;
- O fuso horário de referência é sempre UTC;
- Arredondamento: 2 casas decimais para tempos (minutos) e percentuais.

> **Nota de reconciliação (Regra de Negócio × Cenário de Exceção):** a especificação distingue dois níveis de invalidade. (a) Inconsistência pontual em um registro dentro de um lote válido (ex.: uma tarefa com `data_conclusao < data_inicio`) é uma questão de qualidade de dado e deve ser ignorada silenciosamente, sendo excluída do cálculo e registrada em log (nível `WARNING`). (b) Entrada estruturalmente inválida para a operação como um todo — ex.: o lote inteiro sem nenhuma tarefa concluída (divisão por zero) — é uma condição excepcional e deve resultar no disparo de uma exceção específica e tratada (ver Cenário 2, seção 2.1), pois nesse caso não há base de dados suficiente para produzir uma métrica confiável.

## 2. Especificação de Cenários de Aceite e Test Harness

### 2.1 Cenários de Aceite (Dado – Quando – Então)

#### Cenário 1 – Sucesso (Métricas corretas)

- **Dado** um conjunto de tarefas válidas, com diferentes prioridades, prazos e status (concluídas e pendentes)
- **Quando** o analisador de tarefas for executado
- **Então** as métricas retornadas devem estar corretas, incluindo: tempo médio de conclusão por prioridade e geral; taxa de atraso correta por prioridade e geral; quantidade de tarefas correta por prioridade

#### Cenário 2 – Exceção / Erro (Entradas inválidas)

- **Dado** uma entrada com datas inválidas (ex.: lote sem nenhuma tarefa concluída válida) ou ausência de tarefas concluídas (divisão por zero)
- **Quando** o analisador de tarefas for executado
- **Então** deve disparar uma exceção específica e tratada, com mensagem clara e objetiva ao usuário

### Casos de teste derivados (mapeamento cenário → caso de teste)

| ID | Caso de Teste (pytest) | Cenário |
|---|---|---|
| CT-01 | `test_calcula_tempo_medio_conclusao_geral` | 1 |
| CT-02 | `test_calcula_tempo_medio_conclusao_por_prioridade` | 1 |
| CT-03 | `test_calcula_taxa_atraso_geral` | 1 |
| CT-04 | `test_calcula_taxa_atraso_por_prioridade` | 1 |
| CT-05 | `test_quantidade_tarefas_por_prioridade` | 1 |
| CT-06 | `test_ignora_tarefas_pendentes_no_calculo_de_tempo` | 1 |
| CT-07 | `test_ignora_tarefa_com_datas_inconsistentes_no_lote` | 1 |
| CT-08 | `test_arredondamento_duas_casas_decimais` | 1 |
| CT-09 | `test_lanca_excecao_sem_tarefas_concluidas` | 2 |
| CT-10 | `test_mensagem_de_excecao_e_clara_e_especifica` | 2 |

### 2.2 Planejamento do Test Harness

1. **Cenários de Aceite** (este documento) — descrevem o comportamento esperado do sistema e servem como referência única para os testes;
2. **Casos de Teste** (derivados dos cenários) — decompõem cada cenário em casos específicos, definindo dados de entrada e resultados esperados (ver tabela acima);
3. **Testes Automatizados (pytest)** — implementação dos testes com pytest, uso de fixtures para preparar massas de dados e validação de outputs, tipos e exceções;
4. **Execução e Validação Contínua** — os testes são executados automaticamente a cada geração de código; qualquer falha bloqueia o avanço para a próxima etapa;
5. **Relatórios e Evidências** — geração de relatórios de cobertura e resultados, garantindo rastreabilidade individual para cada cenário.

> **Objetivo desta seção:** garantir que o código gerado por IA esteja correto, em conformidade com o contrato de negócio (seção 1.2) e com os cenários de aceite definidos acima.
