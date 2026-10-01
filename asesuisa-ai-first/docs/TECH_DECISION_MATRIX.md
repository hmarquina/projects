# Matriz de decisión tecnológica

El **costo relativo** es cualitativo (B/M/A) y refleja el orden de magnitud de licencias, consumo y esfuerzo de operación; **no verifiqué
precios vigentes**. La recomendación depende del contexto: aseguradora regulada, datos sensibles, 10 internos y 30 externos, sin nuevas plazas.
No se elige por popularidad.

| Capa | Opción | Ventajas | Desventajas | Costo rel. | Riesgo | Lock-in | Recomendación contextual |
|---|---|---|---|---|---|---|---|
| **LLM** | API de proveedor líder en nube | Mejor calidad; sin operar infraestructura | Datos salen del perímetro; dispara el expediente de tercerización | M–A (variable) | Regulatorio y de concentración | Medio (mitigado por Gateway) | Solo con datos sintéticos/enmascarados hasta cerrar el expediente |
| | Modelo en la nube del cliente (Azure/AWS/GCP) con aislamiento | Datos bajo tu tenant; contratos empresariales | Costo y operación; calidad según modelo | M–A | Medio | Medio | **Candidato principal** si hay región/condiciones aceptables |
| | Modelo abierto on-premises | Máximo control y residencia | Requiere GPUs y operación; calidad menor | A (inversión) | Operativo | Bajo | Solo para casos de uso con datos muy sensibles tras demostrar valor |
| **LLM Gateway** | Propio (este MVP) | Control total; política y auditoría a medida | Hay que mantenerlo | B | Bajo | Ninguno | **Recomendado**: es el núcleo del control y de la salida |
| | Gateway de código abierto | Acelera funciones comunes | Otra dependencia en la cadena de suministro | B–M | Medio | Bajo | Evaluar si el equipo no puede sostener el propio |
| | Gateway gestionado del proveedor de nube | Integración rápida | Acopla a esa nube | M | Medio | Alto | No recomendado si se busca neutralidad |
| **RAG** | Búsqueda sobre documentación aprobada con citas | Reduce búsqueda y aclaraciones | Calidad depende del corpus; riesgo de fuga por permisos | M | Medio | Bajo | P2; empezar por documentación pública interna |
| | Sin RAG (contexto manual) | Simple | No escala | B | Bajo | Ninguno | Válido hasta tener corpus curado |
| **Base vectorial** | pgvector (en PostgreSQL) | Un solo motor; menos piezas; transacciones | Menor rendimiento a gran escala | B | Bajo | Bajo | **Recomendado** para el volumen esperado |
| | Base vectorial dedicada | Escala y funciones avanzadas | Otra pieza que operar y asegurar | M | Medio | Medio | Solo si se demuestra necesidad |
| **Frontend** | React + TypeScript | Ecosistema, tipado, contratación | Mucha libertad de arquitectura | B | Bajo | Bajo | **Recomendado** |
| | Angular | Estructura opinada | Curva de aprendizaje | B | Bajo | Bajo | Válido si la compañía ya lo estandarizó |
| **Backend** | Python + FastAPI | Tipado con Pydantic; ecosistema de IA y pruebas | Rendimiento por hilo menor que JVM/Go | B | Bajo | Bajo | **Recomendado** para la plataforma de IA |
| | Java/.NET | Habituales en el core asegurador | Más pesado para la capa de IA | M | Bajo | Bajo | Mantener para sistemas core |
| **Observabilidad** | OpenTelemetry + backend a elegir | Estándar neutral | Requiere elegir y operar el destino | B–M | Bajo | Bajo | **Recomendado** |
| | Suite propietaria | Integrada | Acoplamiento y costo por volumen | A | Medio | Alto | Solo si ya existe |
| **CI/CD** | GitHub Actions | Cercano al código; ecosistema | Ejecutores gestionados salen del perímetro | B–M | Medio | Medio | **Recomendado**, con ejecutores propios para código sensible |
| | Azure DevOps / GitLab / Jenkins | Control o integración existente | Operación propia | M | Bajo | Medio | Válido si ya es el estándar |
| **Identidad** | OIDC con el IdP corporativo | Un solo sistema de identidad; MFA y ciclo de vida ya resueltos | Integración | B | Bajo | Bajo | **Obligatorio** en producción |
| | JWT local (MVP) | Simple | No apto para producción | B | Alto | Ninguno | Solo para la demo |
| **Secretos** | Gestor de la nube o HashiCorp Vault | Rotación, auditoría, acceso por rol | Operación | M | Bajo | Medio | **Recomendado**; abstracción por variables de entorno en el código |
| | Variables de entorno | Simple | Sin rotación | B | Medio | Ninguno | Solo desarrollo |
| **Evaluación de IA** | Arnés propio con golden datasets | Control y reproducibilidad | Hay que mantener los datasets | B | Bajo | Ninguno | **Recomendado** como base |
| | Frameworks de evaluación | Métricas ya hechas | Dependencia y curva | B–M | Bajo | Bajo | Complementar, no reemplazar el gate |
| **Seguridad** | SAST + escaneo de secretos + SCA en pipeline | Detecta temprano; barato | Falsos positivos | B | Bajo | Bajo | **Recomendado**; añadir DAST y pentest anual |
| | Solo revisión manual | Sin herramientas | No escala | A (tiempo) | Alto | Ninguno | No recomendado |
