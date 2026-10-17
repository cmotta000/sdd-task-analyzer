"""Test Harness (pytest) do TaskAnalyzer.

Traduz os cenários de aceite da seção 2.1 de ``specs/task_analyzer_spec.md``:
CT-01..CT-08 (Cenário 1), CT-09..CT-10 (Cenário 2) e casos de borda.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from task_analyzer import TaskValidationError, analyze_tasks  # noqa: E402

BASE = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)


def h(horas: float) -> datetime:
    """Retorna BASE deslocado em horas (auxiliar para montar datas)."""
    return BASE + timedelta(hours=horas)


def tarefa(
    id_tarefa: int,
    prioridade: str,
    status: str,
    inicio: datetime | None,
    conclusao: datetime | None,
    prazo: datetime,
) -> dict[str, Any]:
    """Monta um registro de tarefa conforme a seção 1.2.1 da especificação."""
    return {
        "id_tarefa": id_tarefa,
        "data_criacao": h(-24),
        "data_inicio": inicio,
        "data_conclusao": conclusao,
        "prazo": prazo,
        "prioridade": prioridade,
        "status": status,
    }


@pytest.fixture
def lote_valido() -> list[dict[str, Any]]:
    """Lote do Cenário 1: concluídas (alta x2, média, baixa), 1 pendente, 1 cancelada.

    Tempos (min): alta 60 e 150; média 45; baixa 70.
    Atrasos: alta #2 e baixa #4.
    """
    return [
        tarefa(1, "alta", "concluída", h(0), h(1), h(2)),
        tarefa(2, "alta", "concluída", h(0), h(2.5), h(2)),
        tarefa(3, "média", "concluída", h(0), h(0.75), h(1)),
        tarefa(4, "baixa", "concluída", h(-1), h(0) + timedelta(minutes=10), h(0)),
        tarefa(5, "média", "pendente", h(0), None, h(5)),
        tarefa(6, "baixa", "cancelada", None, None, h(5)),
    ]


# --- Cenário 1: sucesso -----------------------------------------------------


def test_calcula_tempo_medio_conclusao_geral(lote_valido):
    assert analyze_tasks(lote_valido)["tempo_medio_conclusao_min"] == 81.25


def test_calcula_tempo_medio_conclusao_por_prioridade(lote_valido):
    ind = analyze_tasks(lote_valido)["indicadores_por_prioridade"]
    assert ind["alta"]["tempo_medio_conclusao_min"] == 105.0
    assert ind["média"]["tempo_medio_conclusao_min"] == 45.0
    assert ind["baixa"]["tempo_medio_conclusao_min"] == 70.0


def test_calcula_taxa_atraso_geral(lote_valido):
    assert analyze_tasks(lote_valido)["taxa_atraso_percentual"] == 50.0


def test_calcula_taxa_atraso_por_prioridade(lote_valido):
    ind = analyze_tasks(lote_valido)["indicadores_por_prioridade"]
    assert ind["alta"]["taxa_atraso_percentual"] == 50.0
    assert ind["média"]["taxa_atraso_percentual"] == 0.0
    assert ind["baixa"]["taxa_atraso_percentual"] == 100.0


def test_quantidade_tarefas_por_prioridade(lote_valido):
    resultado = analyze_tasks(lote_valido)
    ind = resultado["indicadores_por_prioridade"]
    assert resultado["quantidade_tarefas"] == 4
    assert (ind["alta"]["quantidade_tarefas"], ind["média"]["quantidade_tarefas"], ind["baixa"]["quantidade_tarefas"]) == (2, 1, 1)


def test_ignora_tarefas_pendentes_no_calculo_de_tempo(lote_valido):
    sem_pendentes = [t for t in lote_valido if t["status"] == "concluída"]
    assert analyze_tasks(lote_valido) == analyze_tasks(sem_pendentes)


def test_ignora_tarefa_com_datas_inconsistentes_no_lote(lote_valido, caplog):
    invalida = tarefa(99, "alta", "concluída", h(3), h(2), h(4))  # conclusão < início
    with caplog.at_level(logging.WARNING):
        resultado = analyze_tasks(lote_valido + [invalida])
    assert resultado == analyze_tasks(lote_valido)
    assert "Tarefa 99 descartada" in caplog.text


def test_arredondamento_duas_casas_decimais():
    um_min, dois_min = timedelta(minutes=1), timedelta(minutes=2)
    lote = [
        tarefa(1, "alta", "concluída", h(0), h(0) + um_min, h(1)),
        tarefa(2, "alta", "concluída", h(0), h(0) + um_min, h(1)),
        tarefa(3, "alta", "concluída", h(0), h(0) + dois_min, h(0)),  # atrasada
    ]
    resultado = analyze_tasks(lote)
    assert resultado["tempo_medio_conclusao_min"] == 1.33
    assert resultado["taxa_atraso_percentual"] == 33.33


# --- Cenário 2: exceção -----------------------------------------------------


def test_lanca_excecao_sem_tarefas_concluidas():
    apenas_pendentes = [tarefa(1, "alta", "pendente", h(0), None, h(2))]
    with pytest.raises(TaskValidationError):
        analyze_tasks(apenas_pendentes)


def test_mensagem_de_excecao_e_clara_e_especifica():
    with pytest.raises(TaskValidationError) as exc:
        analyze_tasks([tarefa(1, "alta", "concluída", h(2), h(1), h(3))])
    mensagem = str(exc.value)
    assert "Nenhuma tarefa concluída válida" in mensagem
    assert "1 registro(s)" in mensagem


# --- Casos de borda ---------------------------------------------------------


def test_borda_lote_vazio_lanca_excecao():
    with pytest.raises(TaskValidationError):
        analyze_tasks([])


def test_borda_conclusao_antes_da_criacao_e_descartada():
    registro = tarefa(1, "alta", "concluída", h(-30), h(-25), h(0))  # criação em h(-24)
    with pytest.raises(TaskValidationError, match="Nenhuma tarefa concluída válida"):
        analyze_tasks([registro])


def test_borda_concluida_sem_datas_e_descartada(lote_valido):
    sem_datas = tarefa(50, "baixa", "concluída", None, None, h(1))
    assert analyze_tasks(lote_valido + [sem_datas]) == analyze_tasks(lote_valido)


def test_borda_prioridade_sem_concluidas_retorna_zero_sem_excecao():
    lote = [tarefa(1, "alta", "concluída", h(0), h(1), h(2)), tarefa(2, "baixa", "pendente", h(0), None, h(2))]
    ind = analyze_tasks(lote)["indicadores_por_prioridade"]
    assert ind["baixa"] == {"tempo_medio_conclusao_min": 0.0, "taxa_atraso_percentual": 0.0, "quantidade_tarefas": 0}
    assert ind["média"]["quantidade_tarefas"] == 0


def test_borda_conclusao_no_prazo_exato_nao_e_atraso():
    lote = [tarefa(1, "média", "concluída", h(0), h(1), h(1))]
    assert analyze_tasks(lote)["taxa_atraso_percentual"] == 0.0


def test_borda_datetime_ingenuo_e_tratado_como_utc():
    ingenuo = tarefa(1, "alta", "concluída", datetime(2026, 1, 5, 10, 0), datetime(2026, 1, 5, 11, 0), datetime(2026, 1, 5, 12, 0))
    assert analyze_tasks([ingenuo])["tempo_medio_conclusao_min"] == 60.0


def test_borda_fusos_diferentes_sao_normalizados_para_utc():
    gmt3 = timezone(timedelta(hours=-3))
    registro = tarefa(1, "alta", "concluída", datetime(2026, 1, 5, 7, 0, tzinfo=gmt3), datetime(2026, 1, 5, 11, 0, tzinfo=timezone.utc), h(5))
    assert analyze_tasks([registro])["tempo_medio_conclusao_min"] == 60.0


def test_contrato_de_saida_possui_apenas_campos_especificados(lote_valido):
    resultado = analyze_tasks(lote_valido)
    assert set(resultado) == {"tempo_medio_conclusao_min", "taxa_atraso_percentual", "quantidade_tarefas", "indicadores_por_prioridade"}
    assert list(resultado["indicadores_por_prioridade"]) == ["baixa", "média", "alta"]
    assert isinstance(resultado["tempo_medio_conclusao_min"], float)
    assert isinstance(resultado["quantidade_tarefas"], int)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("prioridade", "urgente"),
        ("status", "atrasada"),
        ("id_tarefa", 0),
        ("id_tarefa", True),
        ("id_tarefa", "1"),
        ("prazo", None),
        ("prazo", "2026-01-05"),
        ("data_inicio", "ontem"),
    ],
)
def test_borda_registro_fora_do_contrato_lanca_excecao(lote_valido, campo, valor):
    lote_valido[0][campo] = valor
    with pytest.raises(TaskValidationError):
        analyze_tasks(lote_valido)


def test_borda_registro_nao_dicionario_lanca_excecao():
    with pytest.raises(TaskValidationError, match="dicionário"):
        analyze_tasks(["não sou um registro"])  # type: ignore[list-item]
