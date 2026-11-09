"""Limpieza del dataset de Spotify 2023 exportado desde Looker Studio.

Genera data/processed/spotify_2023_limpio.csv, que es la fuente que usa el dashboard.
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "raw" / "spotify_2023.csv"
LIMPIO = RAIZ / "data" / "processed" / "spotify_2023_limpio.csv"

COLUMNAS = {
    "Cancion": "cancion",
    "Artista": "artista",
    "Cant_Ft.": "cant_artistas",
    "Year": "anio",
    "Month": "mes",
    "Day": "dia",
    "En_spotify_playlists": "playlists_spotify",
    "in_spotify_charts": "charts_spotify",
    "streams": "streams",
    "in_apple_playlists": "playlists_apple",
    "in_deezer_playlists": "playlists_deezer",
    "in_shazam_charts": "charts_shazam",
    "bpm": "bpm",
    "key": "tonalidad",
    "Escala": "modo",
    "Bailable_%": "bailabilidad",
    "valence_%": "valencia",
    "energy_%": "energia",
    "Acustica_%": "acustica",
    "instrument_Altivez_%": "instrumentalidad",
    "liveness_%": "en_vivo",
    "Locuacidad_%": "locuacidad",
}


def a_numero(serie: pd.Series) -> pd.Series:
    """Convierte textos como '1,021' a número; los vacíos quedan como NaN."""
    return pd.to_numeric(serie.astype("string").str.replace(",", "", regex=False), errors="coerce")


def rango_bpm(bpm: int) -> str:
    if bpm < 90:
        return "60-89"
    if bpm < 120:
        return "90-119"
    return "120+"


def nivel(valor: float) -> str:
    """Agrupa una escala 0-100 en Baja / Media / Alta."""
    if valor < 33:
        return "Baja"
    if valor < 66:
        return "Media"
    return "Alta"


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df = df[list(COLUMNAS)].rename(columns=COLUMNAS)

    df["charts_shazam"] = a_numero(df["charts_shazam"])
    df["playlists_deezer"] = a_numero(df["playlists_deezer"])

    # La fecha original tenía día y mes invertidos cuando el día era <= 12.
    # Se arma de nuevo a partir de año, mes y día.
    df["fecha_lanzamiento"] = pd.to_datetime(
        dict(year=df["anio"], month=df["mes"], day=df["dia"]), errors="coerce"
    )

    # Hay canciones repetidas (misma canción y artista). Se queda la fila con más streams.
    df = (
        df.sort_values("streams", ascending=False)
        .drop_duplicates(["cancion", "artista"], keep="first")
        .reset_index(drop=True)
    )

    df["streams_millones"] = (df["streams"] / 1_000_000).round(1)
    df["rango_bpm"] = df["bpm"].apply(rango_bpm)
    df["nivel_valencia"] = df["valencia"].apply(nivel)
    df["nivel_bailabilidad"] = df["bailabilidad"].apply(nivel)
    df["epoca"] = pd.cut(
        df["anio"],
        bins=[0, 2019, 2021, 2022, 2023],
        labels=["Hasta 2019", "2020-2021", "2022", "2023"],
    ).astype("string")
    df["cuartil_playlists"] = pd.qcut(
        df["playlists_spotify"], 4, labels=["Q1 (menos)", "Q2", "Q3", "Q4 (más)"]
    ).astype("string")
    return df


def main() -> None:
    crudo = pd.read_csv(CRUDO)
    limpio = limpiar(crudo)
    LIMPIO.parent.mkdir(parents=True, exist_ok=True)
    limpio.to_csv(LIMPIO, index=False, date_format="%Y-%m-%d")
    print(f"{len(crudo)} filas crudas -> {len(limpio)} filas limpias en {LIMPIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
