# Sketches Iniciales - ConnectMetric

Las siguientes representaciones describen las pantallas clave para soportar el flujo del usuario definido en la Fase 1. Cada sketch incluye un mockup en texto ASCII y notas funcionales.

## 1. Login SSO
```
+--------------------------------------------------------------+
| Logo corporativo                                             |
|                                                              |
| [ Botón: Continuar con SSO corporativo ]                     |
|                                                              |
| ---------------------  ó  ---------------------------------- |
|                                                              |
| Correo corporativo: [____________________________]           |
| Contraseña:         [____________________________]           |
| [ Ingresar ]   [ ¿Olvidaste tu contraseña? ]                 |
+--------------------------------------------------------------+
```
- Soporta autenticación federada con Azure AD y credenciales locales para entorno de pruebas.

## 2. Dashboard del candidato
```
+----------------------------------------------+----------------+
|   Progreso general                           |   Próximas     |
|   [ Barra % ]                                |   acciones     |
|                                              |  - Etapa X     |
| Procesos activos                             |  - Entrevista  |
| [Tarjeta] Proceso A  | Estado: Entrevista    |                |
| [Tarjeta] Proceso B  | Estado: Oferta        |                |
|                                              |                |
+----------------------------------------------------------------
| Feedback reciente | Comunidad | Recursos sugeridos             |
+----------------------------------------------------------------
```
- Resume procesos activos, próximos hitos y acceso rápido a recursos compartidos.

## 3. Detalle de proceso y registro de feedback
```
+--------------------------------------------------------------+
| Proceso: Desarrollador Backend                               |
| Etapas: 1) Screening 2) Técnica 3) Cultural 4) Oferta         |
|                                                              |
| [ Línea de tiempo con check / pendiente ]                    |
|                                                              |
| Feedback etapa actual                                        |
| [ Caja de texto multilínea ]                                 |
| Valoración utilidad: (1-5) [★ ★ ★ ☆ ☆]                       |
| [ Adjuntar documento ]                                       |
| [ Guardar feedback ]                                         |
+--------------------------------------------------------------+
| Historial de feedback (colapsable)                           |
+--------------------------------------------------------------+
```
- Permite que el candidato documente la experiencia y comparta aprendizajes.

## 4. Tablero del reclutador
```
+--------------------------------------------------------------+
| Filtros por proceso | Estado | Fecha | Responsable           |
+--------------------------------------------------------------+
| Proceso | Etapa | # candidatos con bloqueo | NPS | Alertas     |
| --------+-------+-------------------------+-----+------------- |
| Backend | Técnica | 3                     | 35  | 2 importantes|
| QA      | Cultural| 1                     | 50  | 0            |
+--------------------------------------------------------------+
| [ Ver detalle ]  [ Exportar CSV ]                            |
```
- Visualiza métricas clave, alertas de bloqueos y acceso a exportaciones.

## 5. Panel de métricas
```
+--------------------------------------------------------------+
| Métricas por proceso                                         |
|  - Tiempo medio por etapa (gráfico de barras)                |
|  - Satisfacción candidatos (gráfico de líneas)               |
|  - Comparativa entre áreas (tarjetas KPI)                    |
+--------------------------------------------------------------+
| Filtros avanzados: [Periodo] [Área] [Tipo rol]               |
+--------------------------------------------------------------+
```
- Analítica operativa para RRHH y liderazgo técnico.

## Enlaces de referencia
- Prototipo colaborativo (Figma) pendiente de subida: agregar URL pública sin datos sensibles.
- Estos sketches sirven como base para la iteración visual en alta fidelidad.
