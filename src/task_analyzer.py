"""TaskAnalyzer: métricas de produtividade a partir de um lote de tarefas.

Implementa o contrato definido em ``specs/task_analyzer_spec.md`` (seção 1.2)
sob as regras de ``CONTEXT_RULES.md``. Usa apenas a biblioteca padrão.

Exemplo:
    >>> resultado = analyze_tasks(tarefas)
    >>> resultado["quantidade_tarefas"]
    3
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PRIORIDADES: tuple[str, ...] = ("baixa", "média", "alta")
STATUS_VALIDOS: frozenset[str] = frozenset({"concluída", "pendente", "cancelada"})
STATUS_CONCLUIDA = "concluída"
CASAS_DECIMAIS = 2
SEGUNDOS_POR_MINUTO = 60

_CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "id_tarefa",
    "data_criacao",
    "prazo",
    "prioridade",
    "status",
)
_CAMPOS_DATETIME_OPCIONAIS: tuple[str, ...] = ("data_inicio", "data_conclusao")


class TaskValidationError(ValueError):
    """Entrada inválida para a análise de tarefas.

    Disparada quando um registro viola o contrato de entrada (campo ausente,
    tipo ou enum inválido) ou quando o lote não possui nenhuma tarefa
    concluída válida (divisão por zero evitada de forma explícita).
    """


@dataclass(frozen=True)
class _TarefaConcluida:
    """Tarefa concluída e válida, pronta para o cálculo agregado."""

    prioridade: str
    tempo_minutos: float
    em_atraso: bool


def _para_utc(valor: datetime) -> datetime:
    """Normaliza um datetime para UTC (datetime ingênuo é assumido como UTC).

    Args:
        valor: Data/hora a normalizar.

    Returns:
        Data/hora com fuso UTC.
    """
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _ler_datetime(registro: Mapping[str, Any], campo: str, obrigatorio: bool) -> datetime | None:
    """Lê e valida um campo datetime de um registro.

    Args:
        registro: Registro da tarefa.
        campo: Nome do campo.
        obrigatorio: Se o campo é obrigatório pelo contrato.

    Returns:
        O datetime em UTC, ou None se opcional e ausente.

    Raises:
        TaskValidationError: Se obrigatório e ausente, ou se não for datetime.
    """
    valor = registro.get(campo)
    if valor is None:
        if obrigatorio:
            raise TaskValidationError(f"Campo obrigatório ausente: '{campo}'.")
        return None
    if not isinstance(valor, datetime):
        raise TaskValidationError(f"Campo '{campo}' deve ser datetime, recebido {type(valor).__name__}.")
    return _para_utc(valor)


def _validar_registro(registro: Mapping[str, Any]) -> None:
    """Valida campos obrigatórios, tipos e enums de um registro.

    Args:
        registro: Registro da tarefa.

    Raises:
        TaskValidationError: Se o registro violar o contrato de entrada.
    """
    if not isinstance(registro, Mapping):
        raise TaskValidationError("Cada tarefa deve ser um dicionário de campos.")
    for campo in _CAMPOS_OBRIGATORIOS:
        if registro.get(campo) is None:
            raise TaskValidationError(f"Campo obrigatório ausente: '{campo}'.")
    id_tarefa = registro["id_tarefa"]
    if isinstance(id_tarefa, bool) or not isinstance(id_tarefa, int) or id_tarefa <= 0:
        raise TaskValidationError(f"id_tarefa deve ser inteiro > 0, recebido {id_tarefa!r}.")
    if registro["prioridade"] not in PRIORIDADES:
        raise TaskValidationError(
            f"Prioridade inválida {registro['prioridade']!r}; permitidas: {', '.join(PRIORIDADES)}."
        )
    if registro["status"] not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Status inválido {registro['status']!r}; permitidos: {', '.join(sorted(STATUS_VALIDOS))}."
        )


def _extrair_concluida(registro: Mapping[str, Any]) -> _TarefaConcluida | None:
    """Converte um registro concluído em tarefa pronta para o cálculo.

    Args:
        registro: Registro com ``status`` igual a ``concluída``.

    Returns:
        A tarefa válida, ou None se as datas forem ausentes/inconsistentes
        (registro descartado, com log WARNING).
    """
    criacao = _ler_datetime(registro, "data_criacao", obrigatorio=True)
    prazo = _ler_datetime(registro, "prazo", obrigatorio=True)
    inicio = _ler_datetime(registro, "data_inicio", obrigatorio=False)
    conclusao = _ler_datetime(registro, "data_conclusao", obrigatorio=False)

    if inicio is None or conclusao is None:
        motivo = "data_inicio ou data_conclusao ausente"
    elif conclusao < inicio:
        motivo = "data_conclusao anterior a data_inicio"
    elif conclusao < criacao:
        motivo = "data_conclusao anterior a data_criacao"
    else:
        minutos = (conclusao - inicio).total_seconds() / SEGUNDOS_POR_MINUTO
        return _TarefaConcluida(registro["prioridade"], minutos, conclusao > prazo)

    logger.warning("Tarefa %s descartada: %s.", registro["id_tarefa"], motivo)
    return None


def _calcular_metricas(tarefas: list[_TarefaConcluida]) -> dict[str, float | int]:
    """Calcula as métricas agregadas de um grupo de tarefas.

    Um grupo vazio retorna zeros (divisão por zero tratada explicitamente).

    Args:
        tarefas: Tarefas concluídas e válidas do grupo.

    Returns:
        Dicionário com ``tempo_medio_conclusao_min``, ``taxa_atraso_percentual``
        e ``quantidade_tarefas``, arredondados em 2 casas decimais.
    """
    quantidade = len(tarefas)
    if quantidade == 0:
        return {"tempo_medio_conclusao_min": 0.0, "taxa_atraso_percentual": 0.0, "quantidade_tarefas": 0}
    tempo_medio = sum(t.tempo_minutos for t in tarefas) / quantidade
    taxa_atraso = sum(t.em_atraso for t in tarefas) / quantidade * 100
    return {
        "tempo_medio_conclusao_min": round(tempo_medio, CASAS_DECIMAIS),
        "taxa_atraso_percentual": round(taxa_atraso, CASAS_DECIMAIS),
        "quantidade_tarefas": quantidade,
    }


def analyze_tasks(tarefas: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Analisa um lote de tarefas e retorna métricas de produtividade.

    Considera apenas tarefas ``concluída``. Registros concluídos com datas
    inconsistentes são ignorados e registrados em log (WARNING).

    Args:
        tarefas: Registros com os campos ``id_tarefa``, ``data_criacao``,
            ``data_inicio``, ``data_conclusao``, ``prazo``, ``prioridade``
            e ``status`` (seção 1.2.1 da especificação).

    Returns:
        Dicionário com ``tempo_medio_conclusao_min``, ``taxa_atraso_percentual``,
        ``quantidade_tarefas`` (gerais) e ``indicadores_por_prioridade`` com as
        mesmas três métricas para ``baixa``, ``média`` e ``alta``. Uma prioridade
        sem tarefas concluídas válidas retorna 0.0 / 0.0 / 0.

    Raises:
        TaskValidationError: Se algum registro violar o contrato de entrada ou
            se o lote não tiver nenhuma tarefa concluída válida.
    """
    registros = list(tarefas)
    concluidas: list[_TarefaConcluida] = []
    for registro in registros:
        _validar_registro(registro)
        if registro["status"] == STATUS_CONCLUIDA:
            tarefa = _extrair_concluida(registro)
            if tarefa is not None:
                concluidas.append(tarefa)

    if not concluidas:
        raise TaskValidationError(
            "Nenhuma tarefa concluída válida no lote: não é possível calcular as métricas "
            f"({len(registros)} registro(s) recebido(s))."
        )

    resultado: dict[str, Any] = _calcular_metricas(concluidas)
    resultado["indicadores_por_prioridade"] = {
        prioridade: _calcular_metricas([t for t in concluidas if t.prioridade == prioridade])
        for prioridade in PRIORIDADES
    }
    logger.info("Análise concluída: %d tarefa(s) consideradas de %d.", len(concluidas), len(registros))
    return resultado
