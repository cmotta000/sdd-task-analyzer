# CONTEXT_RULES.md

> Regras persistentes de governança fornecidas a qualquer agente de IA (coding agent) que gerar ou alterar código neste repositório. Definem **como** o código deve ser escrito — para o contrato de **o que** o código deve fazer, ver [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md).

## 1. Diretrizes Arquiteturais (Obrigatórias)

- Python 3.11+ como versão mínima obrigatória.
- Utilizar type hints (anotações de tipo) em todas as funções e métodos.
- Seguir o princípio Single Responsibility (SRP) e código limpo (PEP 8).
- Documentação formal no padrão Google style docstrings para módulos, classes, funções e parâmetros.
- Funções devem ser pequenas, coesas e com um único propósito.
- Tratamento de exceções específico e com mensagens claras.
- Logs estruturados utilizando o módulo padrão `logging`.
- Código legível, manutenível e com nomes de variáveis e funções descritivos.

## 2. Proibições Explícitas (Regras Restritivas)

- Não utilizar bibliotecas externas não autorizadas (apenas biblioteca padrão do Python).
- Não alterar, remover ou adaptar os cenários de teste fornecidos.
- Não modificar a estrutura de pastas definida nesta especificação.
- Não persistir dados em arquivos ou bancos de dados.
- Não alterar a assinatura (nome e parâmetros) das funções públicas sem autorização.
- Não gerar código sem os testes correspondentes para as novas funcionalidades.
- Não inserir código duplicado ou sem necessidade.
- Não comentar código em excesso (apenas o necessário).
- Não assumir comportamentos não especificados no contrato de negócio.
- Não retornar valores diferentes do contrato de saída definido na seção 1.2.2 de `specs/task_analyzer_spec.md`.

## 3. Regras de Interação com a IA

- Fornecer sempre o contrato completo (`specs/task_analyzer_spec.md`, seções 1 e 2) antes de solicitar geração de código.
- Validar se a IA compreendeu o contrato antes de gerar o código (ex.: solicitando um resumo do entendimento).
- Solicitar explicações quando houver dúvidas sobre a saída gerada.
- Revisar criticamente todo código gerado antes de aceitá-lo.
- Rejeitar respostas que violem as proibições explícitas (seção 2 deste arquivo) ou o contrato de negócio (seção 1.2 de `specs/task_analyzer_spec.md`).

---

**Importante:** este arquivo é a fonte da verdade de governança para os agentes de IA durante a Fase 2 (Implementação). Qualquer código que viole estas regras deve ser rejeitado na homologação humana (ver `README.md`).
