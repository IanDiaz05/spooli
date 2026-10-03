# Spooli 🧵

Gestor ligero en línea de comandos para entusiastas de la impresión 3D FDM. Diseñado para responder a una sola pregunta antes de imprimir: **¿me va a alcanzar el filamento?**

Spooli parsea directamente los metadatos de tus archivos `.gcode`, compara el peso requerido contra tu inventario de bobinas y mantiene un registro automático de consumo y costes, sin requerir hojas de cálculo ni herramientas pensadas para negocios.

---

## Características

- **Cero dependencias externas:** Funciona únicamente con la biblioteca estándar de Python (`sqlite3`, `argparse`, `re`). No necesitas crear entornos virtuales (`venv`) ni ejecutar `pip install`.
- **Análisis directo de `.gcode`:** Extrae automáticamente gramos estimados, tiempo de impresión y material compatible desde los comentarios del slicer.
- **Selección inteligente de bobina:** Si no especificas una bobina, Spooli selecciona automáticamente una compatible que tenga material suficiente priorizando terminar restos.
- **Control de piezas fallidas:** Registra impresiones incompletas ajustando el consumo por porcentaje o por peso real para no descuadrar el inventario físico.
- **Cálculo de costes integrado:** Registra el coste de filamento y estima el coste eléctrico por trabajo de impresión según tu tarifa local.
- **Doble modo de uso:** Ejecución directa por comandos (para flujos rápidos sin interrupciones) o menú interactivo para gestionar bobinas y configuraciones.

---

## Requisitos

- Python 3.10 o superior (usando la instalación estándar del sistema).
