"""Corre las consultas de sql/consultas.sql sobre el CSV limpio y genera los gráficos del README."""
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
LIMPIO = RAIZ / "data" / "processed" / "spotify_2023_limpio.csv"
SQL = RAIZ / "sql" / "consultas.sql"
IMG = RAIZ / "docs" / "img"

VERDE = "#1DB954"
GRIS = "#B3B3B3"
TEXTO = "#282828"


def cargar_consultas(ruta: Path = SQL) -> dict[str, str]:
    """Separa el archivo .sql en consultas con nombre (bloques '-- name: x')."""
    consultas, nombre, lineas = {}, None, []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("-- name:"):
            if nombre:
                consultas[nombre] = "\n".join(lineas).strip()
            nombre, lineas = linea.split(":", 1)[1].strip(), []
        elif nombre:
            lineas.append(linea)
    if nombre:
        consultas[nombre] = "\n".join(lineas).strip()
    return consultas


def correr(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    return {n: con.execute(q).df() for n, q in cargar_consultas().items()}


def estilo(ax, titulo: str) -> None:
    ax.set_title(titulo, loc="left", fontsize=12, color=TEXTO, fontweight="bold")
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors=TEXTO, left=False)
    ax.yaxis.grid(True, color="#EEEEEE")
    ax.set_axisbelow(True)


def barras(df, x, y, titulo, eje_y, archivo, resaltar=None):
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    colores = [VERDE if v == resaltar else GRIS for v in df[x]]
    barras_ = ax.bar(df[x].astype(str), df[y], color=colores)
    ax.bar_label(barras_, fmt="%.0f", color=TEXTO, fontsize=9, padding=2)
    ax.set_ylabel(eje_y, color=TEXTO)
    estilo(ax, titulo)
    fig.tight_layout()
    fig.savefig(IMG / archivo)
    plt.close(fig)


def grafico_correlaciones(canciones: pd.DataFrame) -> pd.Series:
    variables = {
        "playlists_spotify": "Playlists de Spotify",
        "playlists_deezer": "Playlists de Deezer",
        "playlists_apple": "Playlists de Apple",
        "charts_spotify": "Charts de Spotify",
        "bpm": "BPM",
        "energia": "Energía",
        "valencia": "Valencia",
        "bailabilidad": "Bailabilidad",
        "locuacidad": "Locuacidad",
    }
    corr = (
        canciones[list(variables) + ["streams"]]
        .corr(method="spearman")["streams"]
        .drop("streams")
        .rename(index=variables)
        .sort_values()
    )
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    colores = [VERDE if "laylists" in i else GRIS for i in corr.index]
    ax.barh(corr.index, corr.values, color=colores)
    for i, v in enumerate(corr.values):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, f"{v:.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=9, color=TEXTO)
    ax.axvline(0, color=TEXTO, linewidth=0.8)
    ax.set_xlim(-0.3, 1)
    ax.set_xlabel("Correlación de Spearman con los streams", color=TEXTO)
    estilo(ax, "Dónde suena pesa más que cómo suena")
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color="#EEEEEE")
    fig.tight_layout()
    fig.savefig(IMG / "correlaciones.png")
    plt.close(fig)
    return corr


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    canciones = pd.read_csv(LIMPIO)
    con = duckdb.connect()
    con.register("canciones", canciones)
    r = correr(con)

    for nombre, df in r.items():
        print(f"\n== {nombre} ==\n{df.to_string(index=False)}")

    corr = grafico_correlaciones(canciones)
    print(f"\n== correlaciones (Spearman) ==\n{corr.round(3).to_string()}")

    barras(r["streams_por_cuartil_playlists"], "cuartil_playlists", "mediana_streams_millones",
           "Más playlists, muchos más streams", "Mediana de streams (millones)",
           "playlists.png", resaltar="Q4 (más)")
    barras(r["streams_por_epoca"], "epoca", "mediana_streams_millones",
           "Las canciones viejas acumulan más streams", "Mediana de streams (millones)",
           "epoca.png", resaltar="Hasta 2019")
    barras(r["streams_por_rango_bpm"], "rango_bpm", "mediana_streams_millones",
           "El tempo casi no cambia el resultado", "Mediana de streams (millones)",
           "bpm.png", resaltar="90-119")


if __name__ == "__main__":
    main()
