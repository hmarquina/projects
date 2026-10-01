# Seguridad

Cada fila dice **qué control existe, dónde está el código y qué test lo prueba**. Lo que no está implementado se marca como brecha.
Marco conceptual: OWASP Top 10 for LLM Applications. Este documento no afirma cumplimiento regulatorio (ver `REGULATORY.md`).

## 1. OWASP Top 10 for LLM Applications → controles

| Riesgo | Control implementado | Evidencia (test) | Brecha |
|---|---|---|---|
| **LLM01 Prompt injection** | El contenido del usuario es dato; detección heurística (ES/EN) que **señala** sin alterar el resultado; salida validada contra esquema; auditoría marca `injection_flagged` | `test_injection_flagged_but_does_not_alter_result`, `test_injection_in_requirement_is_flagged_in_audit`, caso `security-injection` del golden dataset | Heurística: no detecta ataques nuevos. Defensa en capas, no garantía |
| **LLM02 Sensitive information disclosure** | PII redactada **antes** de llegar al proveedor; rechazo de PII al registrar o editar; la auditoría guarda hashes, no contenido | `test_pii_never_reaches_provider`, `test_pii_rejected_at_initiative_creation`, `test_patch_rejects_pii_and_is_audited` | Patrones DUI/NIT/teléfono son supuesto de formato |
| **LLM03 Supply chain** | Lista blanca de dependencias del servicio generado; `pip-audit`; versiones mínimas | `test_unknown_dependency_is_blocked`, `test_pip_audit_*`, test online | Sin SBOM ni firma de artefactos |
| **LLM04 Data/model poisoning** | Prompts versionados y con huella; golden datasets con gate de regresión | `test_evaluation_catches_regression` | Sin control del origen de datos de RAG (RAG no implementado) |
| **LLM05 Improper output handling** | Toda salida se valida con Pydantic; código generado pasa política estática **antes** de ejecutarse; ruta y extensión de archivos validadas | `test_invalid_output_rejected`, `test_malicious_generated_code_is_never_executed`, `test_malicious_or_invalid_source_is_rejected` | — |
| **LLM06 Excessive agency** | No existe identidad de IA con permisos de aprobación; artefactos en `draft`; aprobación humana segregada; L3 como techo | `test_approval_flow_and_segregation`, `test_contributor_cannot_approve_own_work`, `test_blocked_run_cannot_be_decided_or_released` | — |
| **LLM07 System prompt leakage** | El prompt no contiene secretos; la salida se valida contra esquema | — | Sin pruebas de extracción de prompt |
| **LLM08 Vector/embedding weaknesses** | No aplica: no hay base vectorial | — | RAG en diseño |
| **LLM09 Misinformation / hallucination** | Toda cita debe existir literalmente en el requerimiento; las cifras no pueden inventarse; lo desconocido es "por confirmar" | `test_artifact_evaluation_detects_invented_numbers`, golden datasets (groundedness, fidelidad numérica) | Cobertura limitada a 9 métricas y pocos casos |
| **LLM10 Unbounded consumption** | Timeout y límites de CPU/memoria/archivo en el sandbox; tamaño máximo de entrada | `test_sandbox_timeout_is_a_failure` | Sin límite de tasa ni de costo por usuario |

## 2. Controles de plataforma

| Control | Implementación | Test |
|---|---|---|
| Autenticación | JWT HS256 con expiración, emisor y claims obligatorios; `alg=none` y firma ajena rechazadas | `test_token_signed_with_other_secret_rejected`, `test_alg_none_token_rejected` |
| Autorización (RBAC) | Permiso por endpoint; segregación de funciones | `test_viewer_cannot_create_initiative`, `test_pipeline_rbac` |
| Contraseñas | scrypt con sal; comparación en tiempo constante; relleno de tiempo ante usuario inexistente | `test_login_*` |
| Secretos | Solo por entorno; ninguno en el repositorio; escaneo de literales en el código generado | `test_secret_scanner_detects_literals`, `test_generated_service_reads_secret_from_environment` |
| Auditoría | Append-only, hash encadenado, verificación de integridad | `test_chain_detects_tampering` |
| Integridad del release | Hash por archivo, verificación antes de empaquetar, hash del paquete | `test_release_detects_tampered_files`, `test_release_package_is_verifiable` |
| Aislamiento del código generado | Política estática (lista blanca de imports, sin `eval/open/exec`, sin atributos de escape); sandbox de proceso con entorno mínimo | `test_sandbox_does_not_expose_platform_environment`, `test_sandbox_rejects_path_traversal` |
| SAST / dependencias | `bandit` (cero MEDIUM/HIGH) y `pip-audit` sobre plataforma y servicio generado | `test_bandit_blocks_insecure_code` |

## 3. Límites que hay que decir en voz alta

1. **El sandbox es de proceso, no de contenedor.** Un `python -I` con entorno mínimo y límites de recursos mitiga, no aísla.
   Para código generado por un LLM real en producción: runner efímero en contenedor o gVisor, **sin red** y con sistema de archivos de solo lectura.
1b. **En Windows el sandbox es aún más débil:** no hay límites de CPU, memoria ni tamaño de archivo (el módulo `resource` es solo de Unix); solo quedan el entorno mínimo, el timeout y la política estática. Para un LLM real, contenedor sin red.
2. La política estática es lista blanca de imports y llamadas: reduce la superficie, no es una prueba de ausencia de comportamiento malicioso.
3. Las pruebas generadas verifican el contrato y los controles básicos; **no** sustituyen pruebas de carga, de intrusión ni de seguridad dinámica (DAST).
4. JWT local con HS256: en producción debe sustituirse por validación OIDC (JWKS) con el proveedor de identidad de la compañía.
5. Sin límite de tasa, sin gestor de secretos real, sin cifrado en reposo configurado en la base (SQLite en local).
6. Datos **100% sintéticos**. Nada de lo aquí probado demuestra el comportamiento con datos reales de clientes.

## 4. Brechas priorizadas

| # | Brecha | Por qué importa | Prioridad |
|---|---|---|---|
| 1 | Aislamiento por contenedor sin red | Ejecutar código generado por un LLM real | Alta, antes de usar un LLM real |
| 2 | OIDC y gestor de secretos | Identidad y secretos de producción | Alta |
| 3 | Límite de tasa y de costo | Consumo sin control | Media |
| 4 | DAST y pentest anual | NRP-23 Art. 20 i) pide pruebas de vulnerabilidad e intrusión | Media (proceso) |
| 5 | Módulo de incidentes | NRP-23 Art. 13 | Media |
| 6 | Revisión periódica de accesos | NRP-23 Art. 11 c) | Media |
