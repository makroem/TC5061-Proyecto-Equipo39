# Capturas de MLflow para la Etapa 2

Las 19 capturas del 28 de octubre de 2026 documentan las búsquedas oficiales de P1, P2 y P3, los artefactos y las tres versiones registradas con alias `champion`. Se prepararon para incorporarlas al reporte de experimentos. El [manifiesto de imágenes](../figures/etapa2/capturas_20261028/origen.json) identifica las corridas, las dimensiones, los recortes y el SHA-256 de cada archivo.

## Índice y pies de imagen

| Archivo | Contenido |
|---|---|
| [01_registry_tres_modelos.jpg](../figures/etapa2/capturas_20261028/01_registry_tres_modelos.jpg) | Registro de los tres modelos, versión 1 y alias champion. |
| [02_p1_champion_linaje.jpg](../figures/etapa2/capturas_20261028/02_p1_champion_linaje.jpg) | P1: versión 1, alias, corrida de reproducción, commit y versión de datos. |
| [03_p2_champion_linaje.jpg](../figures/etapa2/capturas_20261028/03_p2_champion_linaje.jpg) | P2: versión 1, alias, corrida de reproducción, commit y versión de datos. |
| [04_p3_champion_linaje.jpg](../figures/etapa2/capturas_20261028/04_p3_champion_linaje.jpg) | P3: versión 1, alias, corrida de reproducción, commit y versión de datos. |
| [05_p3_arbol_artefactos.jpg](../figures/etapa2/capturas_20261028/05_p3_arbol_artefactos.jpg) | P3 reproducida: árbol de config, data, model y plots; firma y ejemplo guardados en model. |
| [06_p3_firma_modelo.jpg](../figures/etapa2/capturas_20261028/06_p3_firma_modelo.jpg) | P3 reproducida: detalle inicial del esquema de 48 entradas y URI de carga del modelo. |
| [07_p3_corridas_anidadas.jpg](../figures/etapa2/capturas_20261028/07_p3_corridas_anidadas.jpg) | P3: búsqueda padre desplegada, baseline KMeans 3 y tres candidatas. |
| [08_p3_comparacion_prueba.jpg](../figures/etapa2/capturas_20261028/08_p3_comparacion_prueba.jpg) | P3: comparación de prueba; GMM 3, KMeans 5, KMeans 4 y baseline KMeans 3. |
| [09_p3_comparacion_validacion.jpg](../figures/etapa2/capturas_20261028/09_p3_comparacion_validacion.jpg) | P3: comparación de validación y estabilidad de entrenamiento, en el mismo orden. |
| [10_p1_corridas_anidadas.jpg](../figures/etapa2/capturas_20261028/10_p1_corridas_anidadas.jpg) | P1: búsqueda padre desplegada, baseline y tres candidatas. |
| [11_p1_comparacion_prueba.jpg](../figures/etapa2/capturas_20261028/11_p1_comparacion_prueba.jpg) | P1: prueba y costos; Random Forest 300, HGB 200, HGB 100 y baseline. |
| [12_p1_comparacion_validacion.jpg](../figures/etapa2/capturas_20261028/12_p1_comparacion_validacion.jpg) | P1: validación y costos, conservando el mismo orden de corridas. |
| [13_p2_corridas_anidadas.jpg](../figures/etapa2/capturas_20261028/13_p2_corridas_anidadas.jpg) | P2: búsqueda padre desplegada, baseline y tres candidatas. |
| [14_p2_comparacion_prueba.jpg](../figures/etapa2/capturas_20261028/14_p2_comparacion_prueba.jpg) | P2: precisión y recall de prueba; C=10, C=1, C=0.1 y baseline. |
| [15_p2_comparacion_validacion.jpg](../figures/etapa2/capturas_20261028/15_p2_comparacion_validacion.jpg) | P2: F1, precisión, recall y AP de validación, en el mismo orden. |
| [16_p2_hiperparametros.jpg](../figures/etapa2/capturas_20261028/16_p2_hiperparametros.jpg) | P2: hiperparámetros de logística y baseline en las cuatro corridas. |
| [17_p2_comparacion_f1_prueba.jpg](../figures/etapa2/capturas_20261028/17_p2_comparacion_f1_prueba.jpg) | P2: F1, AP y alertas por mil de prueba, en el mismo orden. |
| [18_p2_matriz_bicicletas_validacion.jpg](../figures/etapa2/capturas_20261028/18_p2_matriz_bicicletas_validacion.jpg) | P2 candidata C=0.1: panel de bicicletas de la matriz de confusión de validación; umbral 0.65. |
| [19_p2_artefacto_matriz_contexto.jpg](../figures/etapa2/capturas_20261028/19_p2_artefacto_matriz_contexto.jpg) | P2 candidata C=0.1: identidad de la corrida y selección del artefacto de matrices de confusión. |

## Cómo interpretar la evidencia

Las capturas 07, 10 y 13 muestran una búsqueda padre expandida con cuatro corridas hijas: un baseline y tres candidatas. La reproducción posterior aparece como otra corrida padre; no debe contarse como una candidata adicional. Las comparaciones conservan los mismos cuatro identificadores en cada pregunta.

Las capturas 01 a 04 pertenecen a las reproducciones verificadas del 27 de octubre. Los nombres de variante coinciden con las búsquedas, pero sus identificadores son diferentes. `champion` representa producción académica; el campo de etapas antiguas puede mostrar `None` porque se utiliza el esquema de alias. No representa un servicio desplegado.

Las capturas 05 y 06 son dos recortes complementarios del panel de artefactos de la reproducción de P3: el árbol y el inicio de la firma. La firma completa tiene 48 entradas; la imagen 06 muestra su encabezado y las primeras filas. Las imágenes 18 y 19 documentan el panel de bicicletas y la selección de `plots/p2_matrices_confusion_validacion.png` en la candidata original de P2. El panel de anclajes no está incluido en el recorte 18. Se excluyó del encuadre la ruta local del equipo; no se sustituyeron nombres, resultados ni etiquetas de la interfaz.

La interfaz redondea las métricas. En P2 las tres variantes pueden verse como `0.042` en validación; ese redondeo no significa empate. La selección usa los valores completos de los CSV oficiales. La notación `1e+05` en la matriz procede de la gráfica original y tampoco debe interpretarse como un conteo exacto de 100,000.

Las tablas completas, con hiperparámetros y métricas, están en [P1](p1_comparacion_oficial.csv), [P2](p2_comparacion_oficial.csv) y [P3](p3_comparacion_oficial.csv). La explicación de la selección está en las [búsquedas oficiales](busquedas_oficiales_marco.md) y el [cierre técnico](cierre_tecnico_marco.md). Las figuras originales de P3 y su interpretación se conservan en [P3](p3.md).

## Incorporación al reporte

1. Usar las capturas de búsquedas y comparaciones en la sección de resultados de cada pregunta; conservar los pies de imagen y el orden de las columnas. Mostrar las tablas numéricas con al menos seis decimales cuando sea necesario distinguir variantes.
2. Incorporar las vistas de artefactos y los tres modelos registrados en la sección de evidencias del paso 10. Presentar los recortes junto con su contexto e identificador de corrida.
3. Diego Hurtado consolida el Word y el PDF con los resultados e interpretaciones ya revisados. Otro integrante revisa este conjunto de capturas mediante Pull Request; Marco podrá integrarlo después de la aprobación.
4. El integrante designado por el equipo confirma el envío en Canvas y conserva el comprobante. Estas capturas no acreditan ese envío.

No se ejecutaron nuevos entrenamientos ni se modificaron modelos para obtener estas vistas.
