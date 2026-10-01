# Marco regulatorio: qué está verificado y qué no

> **Esto no es asesoría legal ni una afirmación de cumplimiento.** Distingue tres cosas:
> **requisito confirmado** (el texto de la norma lo dice y lo he leído), **control recomendado**
> (mi respuesta de diseño, que Cumplimiento debe validar) y **por confirmar** (no verificado).
> Toda decisión debe validarse con Cumplimiento, Riesgos y Auditoría Interna de la aseguradora.

## 1. Norma verificada contra el texto oficial

**NRP-23 — Normas Técnicas para la Gestión de la Seguridad de la Información**
(CNBCR-07/2020; aprobada 14/04/2020; vigente desde 01/07/2020). Emisor: Banco Central de Reserva
de El Salvador; supervisa la Superintendencia del Sistema Financiero (SSF).
Fuente leída (texto compilado, 26 páginas): [bcr.gob.sv — NRP-23.pdf](https://www.bcr.gob.sv/regulaciones/upload/NRP-23.pdf).
El texto compilado incluye modificaciones aprobadas en 2025 (arts. 2, 3, 11, 13, 19, 20, 22, 25 y 26;
vigentes desde el 04/04/2025, y art. 2 desde el 15/10/2025).

**Ámbito (Art. 2, literal d):** alcanza a *"las sociedades de seguros, sus sucursales en el extranjero
y las sucursales de sociedades de seguros extranjeras establecidas en el país y las Asociaciones
Cooperativas de Seguros constituidas en el país, en lo que no contradiga su respectiva Ley"*.
La salvedad ("en lo que no contradiga su respectiva Ley") exige que Cumplimiento confirme el alcance exacto.

### Mapeo requisito → control de la plataforma

| Art. | Requisito (texto de la norma, resumido) | Control de la plataforma | Evidencia | Estado |
|---|---|---|---|---|
| 11 b) | *Segregación de funciones: una misma persona no debe tener roles o privilegios que pongan en peligro la seguridad.* | Roles con permisos mínimos; quien ejecuta el pipeline no aprueba; el aprobador no puede haber creado iniciativa, análisis, artefactos ni ejecución | Tests `test_contributor_cannot_approve_own_work`, `test_approval_flow_and_segregation`, `test_rbac_*` | Implementado en el MVP |
| 11 a), c) | *Procedimientos formales de alta/baja de cuentas privilegiadas; revisión al menos semestral de derechos, con bitácora.* | Roles definidos; **no hay** módulo de revisión periódica de accesos | — | **Brecha** |
| 20 b) | *Controles y pruebas sobre los cambios en el ambiente operativo.* | Gates: política estática, pruebas contra contrato, SAST, secretos, dependencias, readiness, aprobación humana | `pipeline.run`, `pipeline.decision` en auditoría; evidencia de cambio | Implementado en el MVP |
| 20 c) | *Separación de los ambientes de desarrollo, pruebas y producción.* | El MVP corre en un solo entorno | — | **Brecha** (a resolver en Compose/CI y en la infraestructura real) |
| 20 h) | *Resguardo de registros de auditoría y monitoreo del uso de los sistemas.* | Audit trail append-only con hash encadenado y endpoint de verificación | `test_chain_detects_tampering` | Implementado; falta anclaje externo/WORM |
| 20 i) | *Pruebas de vulnerabilidad e intrusión al menos anuales sobre infraestructura.* | Fuera del alcance de la plataforma (pentest externo) | — | **Brecha** (proceso, no software) |
| 21 c) | *Controles sobre la implementación de aplicaciones antes del ingreso a producción.* | Release Gate: readiness ≥ 85, cero bloqueos duros, aprobación humana | Release package con manifest y hashes | Implementado en el MVP |
| 21 d) | *Controlar el acceso al código fuente.* | Se delega al repositorio (permisos de GitHub, protección de ramas) | — | Fuera de la plataforma; **por configurar** |
| 21 e) | *Control formal de cambios y versiones, apoyado por sistemas.* | Artefactos versionados; release `vN` con manifest; trazabilidad requerimiento→prueba | `traceability`, `MANIFEST.json` | Implementado en el MVP |
| 21 f) | *Mecanismos de desarrollo seguro que analicen y corrijan vulnerabilidades durante el ciclo de vida y en producción.* | SAST (bandit), escaneo de secretos, auditoría de dependencias en el pipeline. Sin DAST ni escaneo en producción | Pasos `sast_bandit`, `escaneo_secretos`, `dependencias` | **Parcial** |
| 13 | *Notificar incidentes a la Alta Gerencia y a la SSF y remitir la documentación completa en un plazo máximo de siete días hábiles.* | El audit trail permite reconstruir qué pasó; **no hay** módulo de incidentes | — | **Brecha** (proceso + herramienta) |
| Anexo 1, Secc. C.1 | *Procedimientos para compartir información con la SSF 72 horas después de un incidente.* | Ídem | — | **Brecha** |
| 14, 26, Anexo 1 | *Tercerización de TI: evaluación de riesgos previa, debida diligencia del proveedor, contrato con requisitos de seguridad, acceso de la SSF a datos, propiedad exclusiva de la entidad sobre los datos, aislamiento de otros clientes, borrado seguro, plan de salida.* | Ver sección 2 | Gateway, redacción de PII | Control de diseño; **requiere proceso contractual** |
| 25 | *Informar a la SSF con 30 días hábiles de anticipación el traslado/ubicación del centro de datos; si es fuera del país, demostrar las condiciones del Anexo 1.* | Decisión de dónde se aloja el modelo (ver sección 2) | — | **Decisión pendiente** |
| 29, 30 | *Informe anual a la SSF sobre el SGSI; Auditoría Interna evalúa el cumplimiento.* | El evidence package y la bitácora alimentan el informe | `evidence.json` | Apoyo, no sustituto |

## 2. Lo que esto implica para usar un LLM

Usar un modelo alojado por un tercero **es una tercerización de actividades de TI** bajo los Arts. 14 y 26
y el Anexo 1. No es una compra de licencia sin más. Condiciones del Anexo 1 que más pesan en un proveedor de IA:

- **A.1–A.2:** evaluación de riesgos previa (operacionales, tecnológicos, legales, reputacionales, financieros), incluida la concentración en un proveedor.
- **A.3 c):** debida diligencia documentada y revisada anualmente.
- **A.4:** identificar todos los proveedores de la cadena de suministro (el proveedor del modelo y sus subencargados).
- **A.5:** la SSF, la auditoría interna y la externa deben poder acceder a los datos del servicio sin restricciones.
- **B.1 y B.18:** la entidad conserva la propiedad exclusiva de sus datos; el proveedor **no adquiere derechos para usarlos para sus propios fines**. En la práctica: sin entrenamiento con datos de la aseguradora.
- **B.17:** el procesamiento debe estar aislado de los datos de otros clientes.
- **B.19:** devolución y borrado seguro al terminar.
- **C.2:** plan de salida documentado y probado.

**Cómo responde el diseño (control recomendado, no cumplimiento demostrado):**

| Condición | Respuesta de diseño |
|---|---|
| Datos personales fuera del perímetro | El Gateway redacta PII **antes** de llamar al proveedor; el MVP usa solo datos sintéticos |
| Plan de salida (C.2) y concentración (A.1) | Arquitectura *model-agnostic*: cambiar de proveedor es configuración, con fallback ordenado |
| Ubicación del procesamiento (Art. 25) | Dos caminos: modelo alojado on-premises/nube privada en el país, o proveedor externo con el expediente del Anexo 1. **Esta es una decisión de la dirección con Cumplimiento y la SSF** |
| Auditoría (A.5) | Cada llamada deja modelo, versión del prompt y hashes de entrada y salida |

**Opción más conservadora para el año 1:** empezar con **datos sintéticos/enmascarados y un modelo bajo control de la
entidad**, y no enviar datos de clientes a proveedores externos hasta cerrar el expediente de tercerización.

## 3. Lo que NO está verificado

| Tema | Qué encontré | Qué falta |
|---|---|---|
| Ley de Supervisión y Regulación del Sistema Financiero | NRP-23 la cita (arts. 2, 7, 32, 35, 99) como base | Leer el texto completo |
| **Ley de Protección de Datos Personales** | Prensa reporta su aprobación en 2024 y un plazo de adecuación de seis meses; **las fuentes son inconsistentes** (otra nota habla de 2021) y no pude leer el texto publicado | Texto vigente, fecha, obligaciones y sanciones. Hasta entonces: **por confirmar** |
| Ley de Ciberseguridad y Seguridad de la Información (2024) | Solo menciones de prensa | Texto y aplicabilidad |
| Otras normas del regulador aplicables a **aseguradoras** (riesgo operacional, continuidad, gobierno corporativo, gestión integral de riesgos) | No las identifiqué con certeza | Cumplimiento debe indicar cuáles aplican |

**Corrección a mi propia memoria.** Yo recordaba NRP-11 como norma de riesgo operacional. Al verificar,
NRP-11 corresponde a la gestión integral de riesgos de **entidades de mercados bursátiles**, y NPB4-50
(riesgo operacional) aparece como norma de **bancos**. **No** las asumo aplicables a una aseguradora.

## 4. Cómo usar este documento en la entrevista

1. Citar NRP-23 y el Art. 2 d) como base **porque está verificado**, no porque "debería aplicar".
2. Decir qué cubre el MVP (11 b, 20 b, 20 h, 21 c, 21 e), qué cubre parcialmente (21 f) y cuáles son las **brechas** (revisión de accesos, separación de ambientes, incidentes, pentest anual).
3. Reconocer que el uso de un LLM externo dispara el Anexo 1 y es una decisión conjunta con Cumplimiento.
