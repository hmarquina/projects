# Guion de la demo (8 minutos)

Caso ficticio: **"Digitalización del proceso de reclamos"**. Todo el contenido es sintético. La demo muestra el flujo y los controles;
**no** muestra la calidad de un modelo de lenguaje, porque el proveedor de IA es un mock determinista. Dilo en voz alta al empezar.

## 0. Preparación (una sola vez)

Desde `asesuisa-ai-first/`:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements-dev.txt
npm --prefix frontend ci && npm --prefix frontend run build   # la UI compilada la sirve el backend

export DATABASE_URL=sqlite:///./data/demo.db            # relativo a backend/
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DEMO_PASSWORD="elija-una-contraseña-de-12+"     # la usará para entrar con todos los usuarios demo
export PIPELINE_DEPENDENCY_AUDIT=false                  # offline: la auditoría de dependencias queda "no verificada"
mkdir -p backend/data && cd backend && python -m app.seed && uvicorn app.main:app --port 8000
```

Abrir <http://127.0.0.1:8000>. Con red y `PIPELINE_DEPENDENCY_AUDIT=true`, la auditoría de dependencias corre de verdad (≈ 10 s más por ejecución).

**Alternativa con Docker** (`docker compose up --build`, con `.env` a partir de `.env.example`): el `Dockerfile` y el Compose están escritos
y su sintaxis validada, pero **no se han construido ni ejecutado** (no había demonio de Docker). Si la demo es en vivo, usa la opción anterior.

**Verificación previa (opcional, 1 min):** con el backend arriba, `CHROMIUM_PATH=<chrome> node frontend/e2e/demo.mjs` recorre todo el guion en un navegador real y falla si algo no se comporta como se describe aquí.

Usuarios: `demo_analyst`, `demo_tech_lead`, `demo_approver`, `demo_security`, `demo_viewer`, `demo_admin` (la misma contraseña).

## 1. Entrada y límites (0:00–0:45) — *analyst*
- Entrar como `demo_analyst`. En el **Dashboard** señala el aviso: *datos 100% sintéticos, proveedor mock determinista*.
- Muestra la tabla Baseline · Target · Current · Trend · Confianza: **Current dice "sin dato"**. *"No invento lo que no se mide."*
- Señala el modelo de capacidad: *"2× de valor es el techo de mis rangos, no el valor esperado."*

## 2. Un requerimiento pobre se bloquea (0:45–2:15) — *analyst*
- **Initiatives → Registrar y analizar** (el texto de ejemplo es deliberadamente vago: "rápido", "fácil", "adecuado", "etc.").
- **Requirements → Analizar calidad:** score ≈ 30 de 100, *bloqueado*. Muestra las ambigüedades **con su cita y la pregunta de aclaración**.
- **AI Analysis → Generar historias de usuario:** el servidor responde con un error de *Definition of Ready*.
- **Qué decir:** *"Ningún requerimiento consume capacidad hasta que está listo. Esto ataca el 25% de retrabajo en su origen."*

## 3. Se refina y se generan los artefactos (2:15–3:45) — *analyst*
- En **Requirements**, sustituir el texto por uno medible (el guion de `frontend/e2e/demo.mjs` trae uno), **Guardar** y **Analizar**: score 100, *cumple Ready*.
- **AI Analysis:** generar los cinco artefactos. Muestra que **cada historia cita su frase fuente**, y que una historia sin beneficio dice *"beneficio sin confirmar"*: el sistema no lo inventa.
- **Architecture:** componentes, relaciones, decisiones y el contrato OpenAPI (todas las operaciones declaran 401 y 403).
- **Qué decir:** *"Todo es borrador. Nada de esto se aprueba solo."*

## 4. Pipeline: genera, prueba y escanea (3:45–5:30) — *tech_lead*
- Cerrar sesión; entrar como `demo_tech_lead`. **Development → Ejecutar pipeline** (≈ 3 s offline).
- Recorre los pasos: política estática, 14/14 pruebas, SAST, secretos, dependencias (**"no verificado"**, no "pasó"), trazabilidad 7/8, readiness 90.
- Abre `generated_service/app.py`: *"El código es visible y auditable."*
- **Testing:** el criterio `AC-SR-2` (99.5% de disponibilidad) aparece **sin verificar**: requiere operación real.
- **Security:** composición del readiness y los límites (sandbox de proceso, no de contenedor).
- **Si hay tiempo (30 s):** mostrar el test que inyecta `import subprocess` en el código generado y el pipeline lo **bloquea sin ejecutarlo** (`test_malicious_generated_code_is_never_executed`).

## 5. Aprobación humana segregada (5:30–6:45)
- Con el tech_lead: **Approvals** — *no ve controles de aprobación*. *"Quien ejecuta no aprueba."*
- Cerrar sesión; entrar como `demo_approver`. **Approvals:** el botón *Aprobar* está deshabilitado. Escribe el comentario: sigue deshabilitado.
  Marca *"Reconozco los riesgos residuales"*: se habilita. Aprobar.
- **Qué decir:** *"Quien aprueba acepta explícitamente lo que quedó sin verificar. Y no puede haber participado en el trabajo."*

## 6. Release y auditoría (6:45–8:00)
- `demo_tech_lead` → **Releases → Publicar release → Descargar**. Verificar: `sha256sum release-v1.zip` coincide con el hash de la pantalla.
- `demo_security` → **Audit → Verificar integridad:** *"cadena íntegra"*. Señala modelo, versión del prompt, decisión y aprobación en cada evento.
- **Cierre:** *"Más velocidad no significa menos control: el control es parte del flujo y deja evidencia."*

## Si algo falla en vivo
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Login falla | `DEMO_PASSWORD` distinta a la usada en `app.seed` | Borrar `backend/data/demo.db` y repetir el seed |
| Pipeline responde 409 "Falta el artefacto" | No se generaron los 5 artefactos o se editó el requerimiento después | Volver a analizar y generar |
| Pipeline "bloqueado" | Un control funcionó | **Es parte de la demo**: lee el paso fallido en la tabla |
| Pantalla vacía en `:8000` | Falta compilar la UI | `npm --prefix frontend run build` |

## Preguntas que la demo provoca
Ver `QA.md`: #2 (¿duplicamos?), #8 (fuga de datos), #9 (código inseguro), #11 (dónde se ejecuta el código), #12 (quién responde).
