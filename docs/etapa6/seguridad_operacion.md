# Revisión de seguridad de la operación

El análisis de los módulos de operación y de los programas de fixture, carga y consolidación registra **9 avisos bajos, 0 medios y 0 altos**. No se han suprimido los avisos bajos. La evidencia completa se conserva en `references/etapa6/checks/bandit.json`.

| Aviso | Casos | Interpretación y control |
|---|---:|---|
| B404 | 2 | Importación de subprocess en programas locales para ejecutar Git y Docker. No se exponen como endpoints ni reciben instrucciones de una petición HTTP. |
| B603 | 4 | Procesos con argumentos separados, sin shell. Los comandos provienen del programa y de opciones explícitas del operador; no se interpolan cuerpos de solicitudes, títulos de PR o datos del modelo. Se requiere un entorno de ejecución confiable. |
| B607 | 2 | Git se resuelve mediante PATH. En CI se usa el ejecutor preparado por GitHub; localmente debe verificarse la instalación de Git y el PATH antes de ejecutar. Docker puede especificarse mediante --docker con su ruta instalada. |
| B311 | 1 | El generador pseudoaleatorio produce entradas sintéticas de carga. No genera contraseñas, tokens ni identificadores de seguridad. |

Los avisos de apertura de URL se corrigieron mediante un cliente limitado a HTTP y HTTPS: rechaza otros esquemas, credenciales embebidas, consultas y fragmentos en la dirección base; no sigue redirecciones y limita el tamaño de respuesta. Diez pruebas verifican rechazo previo a conectar, POST, propagación de 422 y cierre de conexión.

El modelo sintético de CI se serializa con cloudpickle desde un estimador creado por el mismo trabajo y se valida mediante su inventario. No se cargan archivos serializados aportados por terceros. P1 se recibe por el procedimiento autorizado y se verifica contra su manifiesto; su paquete permanece fuera de Git y de los artefactos públicos.

Compose restringe puertos a loopback, usa usuarios sin privilegios, montajes de modelo de solo lectura, límites de recursos, raíz de solo lectura y almacenamiento persistente separado para tracking. La ejecución de trabajos de MLflow se desactiva porque esta etapa solo necesita tracking; la comprobación de persistencia se ejecutó después de recrear el contenedor.

Estos resultados describen el análisis efectuado; no equivalen a una auditoría exhaustiva de todas las dependencias de las imágenes.
