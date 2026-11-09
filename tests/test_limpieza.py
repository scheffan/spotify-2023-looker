import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analisis import cargar_consultas  # noqa: E402
from limpieza import CRUDO, a_numero, limpiar, nivel, rango_bpm  # noqa: E402


@pytest.fixture(scope="module")
def limpio():
    return limpiar(pd.read_csv(CRUDO))


def test_a_numero_saca_separador_de_miles():
    assert a_numero(pd.Series(["1,021", "8", None])).tolist()[:2] == [1021, 8]


@pytest.mark.parametrize("bpm, esperado", [(65, "60-89"), (89, "60-89"), (90, "90-119"), (119, "90-119"), (120, "120+")])
def test_rango_bpm(bpm, esperado):
    assert rango_bpm(bpm) == esperado


@pytest.mark.parametrize("valor, esperado", [(0, "Baja"), (32, "Baja"), (33, "Media"), (65, "Media"), (66, "Alta")])
def test_nivel(valor, esperado):
    assert nivel(valor) == esperado


def test_sin_duplicados(limpio):
    assert not limpio.duplicated(["cancion", "artista"]).any()


def test_fecha_coincide_con_anio_mes_dia(limpio):
    fechas = pd.to_datetime(limpio["fecha_lanzamiento"])
    assert (fechas.dt.month == limpio["mes"]).all()
    assert (fechas.dt.day == limpio["dia"]).all()


def test_porcentajes_en_rango(limpio):
    for col in ["bailabilidad", "valencia", "energia", "acustica", "locuacidad"]:
        assert limpio[col].between(0, 100).all(), col


def test_streams_positivos(limpio):
    assert (limpio["streams"] > 0).all()


def test_consultas_sql_tienen_nombre():
    consultas = cargar_consultas()
    assert {"kpis", "streams_por_cuartil_playlists", "top_artistas"} <= set(consultas)
    assert all(q.strip() for q in consultas.values())
