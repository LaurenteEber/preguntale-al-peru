# M1-03 — Doradas por corte: lo publicado frente a lo calculado

Cada fila: la cifra del informe del INEI («Perú: Indicadores de Resultados de los Programas Presupuestales, 2024. ENDES», recurso `endes-2024-informe-ppr`) frente a la que calcula la receta por el camino nuevo (plan → verificador → ejecutor), nacional, con el corte pedido. Los casos son los «casos sin ponderar» del cuadro y tienen que ser idénticos. Se generó con `evidencia/m1-03_reproducir.py` (12/11/2026).

| Receta | Corte | Categoría | Publicado (INEI) | Calculado | Diferencia (pp) | Casos publicados | Casos nuestros | Pasa |
|---|---|---|---|---|---|---|---|---|
| endes_anemia_6_35m | region_natural | Costa | 36.1 | 36.1 | +0.0 | 4 058 | 4 058 | sí |
| endes_anemia_6_35m | region_natural | Sierra | 53.4 | 53.4 | +0.0 | 3 176 | 3 176 | sí |
| endes_anemia_6_35m | region_natural | Selva | 48.3 | 48.3 | +0.0 | 2 725 | 2 725 | sí |
| endes_anemia_6_35m | quintil_riqueza | los más pobres | 54.8 | 54.8 | +0.0 | 3 138 | 3 138 | sí |
| endes_anemia_6_35m | quintil_riqueza | pobre | 47.0 | 47.0 | +0.0 | 2 660 | 2 660 | sí |
| endes_anemia_6_35m | quintil_riqueza | medio | 38.4 | 38.4 | +0.0 | 1 932 | 1 932 | sí |
| endes_anemia_6_35m | quintil_riqueza | rico | 32.8 | 32.8 | +0.0 | 1 406 | 1 406 | sí |
| endes_anemia_6_35m | quintil_riqueza | más rico | 31.1 | 31.1 | +0.0 | 823 | 823 | sí |
| endes_anemia_6_35m | grupo_edad | 6 a 8 meses | 68.1 | 68.1 | +0.0 | 968 | 968 | sí |
| endes_anemia_6_35m | grupo_edad | 9 a 11 meses | 66.3 | 66.3 | +0.0 | 1 059 | 1 059 | sí |
| endes_anemia_6_35m | grupo_edad | 12 a 17 meses | 53.1 | 53.1 | +0.0 | 1 977 | 1 977 | sí |
| endes_anemia_6_35m | grupo_edad | 18 a 23 meses | 40.2 | 40.2 | +0.0 | 1 961 | 1 961 | sí |
| endes_anemia_6_35m | grupo_edad | 24 a 35 meses | 29.0 | 29.0 | +0.0 | 3 994 | 3 994 | sí |
| endes_anemia_6_35m_oms2024 | region_natural | Costa | 27.0 | 27.0 | +0.0 | 4 058 | 4 058 | sí |
| endes_anemia_6_35m_oms2024 | region_natural | Sierra | 43.1 | 43.1 | +0.0 | 3 176 | 3 176 | sí |
| endes_anemia_6_35m_oms2024 | region_natural | Selva | 44.1 | 44.1 | +0.0 | 2 725 | 2 725 | sí |
| endes_anemia_6_35m_oms2024 | quintil_riqueza | los más pobres | 47.5 | 47.5 | +0.0 | 3 138 | 3 138 | sí |
| endes_anemia_6_35m_oms2024 | quintil_riqueza | pobre | 37.2 | 37.2 | +0.0 | 2 660 | 2 660 | sí |
| endes_anemia_6_35m_oms2024 | quintil_riqueza | medio | 29.7 | 29.7 | +0.0 | 1 932 | 1 932 | sí |
| endes_anemia_6_35m_oms2024 | quintil_riqueza | rico | 24.5 | 24.5 | +0.0 | 1 406 | 1 406 | sí |
| endes_anemia_6_35m_oms2024 | quintil_riqueza | más rico | 22.8 | 22.8 | +0.0 | 823 | 823 | sí |
| endes_anemia_6_35m_oms2024 | grupo_edad | 6 a 8 meses | 51.8 | 51.8 | +0.0 | 968 | 968 | sí |
| endes_anemia_6_35m_oms2024 | grupo_edad | 9 a 11 meses | 51.8 | 51.8 | +0.0 | 1 059 | 1 059 | sí |
| endes_anemia_6_35m_oms2024 | grupo_edad | 12 a 17 meses | 36.0 | 36.0 | +0.0 | 1 977 | 1 977 | sí |
| endes_anemia_6_35m_oms2024 | grupo_edad | 18 a 23 meses | 25.4 | 25.4 | +0.0 | 1 961 | 1 961 | sí |
| endes_anemia_6_35m_oms2024 | grupo_edad | 24 a 35 meses | 31.6 | 31.6 | +0.0 | 3 994 | 3 994 | sí |
| endes_dci_menores_5 | region_natural | Costa | 7.3 | 7.3 | +0.0 | 8 047 | 8 047 | sí |
| endes_dci_menores_5 | region_natural | Sierra | 17.6 | 17.6 | +0.0 | 6 162 | 6 162 | sí |
| endes_dci_menores_5 | region_natural | Selva | 16.3 | 16.3 | +0.0 | 5 302 | 5 302 | sí |
| endes_dci_menores_5 | quintil_riqueza | los más pobres | 22.4 | 22.4 | +0.0 | 5 991 | 5 991 | sí |
| endes_dci_menores_5 | quintil_riqueza | pobre | 10.8 | 10.8 | +0.0 | 5 218 | 5 218 | sí |
| endes_dci_menores_5 | quintil_riqueza | medio | 8.5 | 8.5 | +0.0 | 3 835 | 3 835 | sí |
| endes_dci_menores_5 | quintil_riqueza | rico | 5.9 | 5.9 | +0.0 | 2 786 | 2 786 | sí |
| endes_dci_menores_5 | quintil_riqueza | más rico | 3.5 | 3.5 | +0.0 | 1 681 | 1 681 | sí |
| endes_dci_menores_5 | grupo_edad | Menores de 36 meses | 13.8 | 13.8 | +0.0 | 11 449 | 11 449 | sí |
| endes_dci_menores_5 | grupo_edad | De 36 a 59 meses | 9.8 | 9.8 | +0.0 | 8 062 | 8 062 | sí |

36 doradas por corte, 36 se reproducen, 0 no; mayor |diferencia| = 0.0 pp (tolerancia 0,1 pp).
