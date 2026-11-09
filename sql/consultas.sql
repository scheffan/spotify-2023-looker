-- Consultas del análisis (DuckDB). Cada bloque arranca con "-- name:" y
-- corresponde a un gráfico o KPI del dashboard de Looker Studio.
-- La tabla "canciones" es data/processed/spotify_2023_limpio.csv.

-- name: kpis
SELECT
    COUNT(*)                                  AS canciones,
    COUNT(DISTINCT artista)                   AS artistas,
    ROUND(SUM(streams) / 1e9, 1)              AS streams_miles_de_millones,
    ROUND(MEDIAN(streams) / 1e6, 0)           AS mediana_streams_millones,
    ROUND(MEDIAN(bpm), 0)                     AS bpm_mediano
FROM canciones;

-- name: concentracion_top10
-- Qué parte de los streams se lleva el 10 % de canciones más escuchadas.
WITH ranking AS (
    SELECT streams, NTILE(10) OVER (ORDER BY streams DESC) AS decil
    FROM canciones
)
SELECT ROUND(100.0 * SUM(streams) FILTER (WHERE decil = 1) / SUM(streams), 1) AS pct_streams_top10
FROM ranking;

-- name: streams_por_cuartil_playlists
SELECT
    cuartil_playlists,
    COUNT(*)                              AS canciones,
    ROUND(MEDIAN(playlists_spotify), 0)   AS playlists_medianas,
    ROUND(MEDIAN(streams) / 1e6, 0)       AS mediana_streams_millones
FROM canciones
GROUP BY cuartil_playlists
ORDER BY cuartil_playlists;

-- name: streams_por_epoca
SELECT
    epoca,
    COUNT(*)                          AS canciones,
    ROUND(MEDIAN(streams) / 1e6, 0)   AS mediana_streams_millones
FROM canciones
GROUP BY epoca
ORDER BY MIN(anio);

-- name: streams_por_rango_bpm
SELECT
    rango_bpm,
    COUNT(*)                              AS canciones,
    ROUND(MEDIAN(streams) / 1e6, 0)       AS mediana_streams_millones,
    ROUND(SUM(streams) / 1e9, 1)          AS streams_totales_miles_de_millones,
    ROUND(AVG(bailabilidad), 1)           AS bailabilidad_promedio,
    ROUND(AVG(valencia), 1)               AS valencia_promedio
FROM canciones
GROUP BY rango_bpm
ORDER BY MIN(bpm);

-- name: streams_por_modo
SELECT
    modo,
    COUNT(*)                          AS canciones,
    ROUND(MEDIAN(streams) / 1e6, 0)   AS mediana_streams_millones
FROM canciones
GROUP BY modo;

-- name: top_artistas
-- Las colaboraciones ("Artista A, Artista B") cuentan como un artista aparte.
SELECT
    artista,
    COUNT(*)                          AS canciones,
    ROUND(SUM(streams) / 1e9, 2)      AS streams_miles_de_millones
FROM canciones
GROUP BY artista
ORDER BY SUM(streams) DESC
LIMIT 10;
