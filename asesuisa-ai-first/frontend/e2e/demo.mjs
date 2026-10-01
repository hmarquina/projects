// E2E del flujo completo en un navegador real, contra el backend real (UI compilada servida por FastAPI).
// Uso: DEMO_PASSWORD=... CHROMIUM_PATH=/ruta/a/chrome node e2e/demo.mjs   (BASE_URL por defecto: http://127.0.0.1:8000)
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { chromium } from "playwright-core";

const BASE = process.env.BASE_URL ?? "http://127.0.0.1:8000";
const PASSWORD = process.env.DEMO_PASSWORD;
const OUT = process.env.E2E_OUT ?? "e2e/screenshots";
if (!PASSWORD) throw new Error("Defina DEMO_PASSWORD");
mkdirSync(OUT, { recursive: true });

const GOOD =
  "El asegurado debe registrar un reclamo desde el portal web en menos de 3 minutos para recibir un número de seguimiento. " +
  "El sistema deberá responder en menos de 2 segundos para el 95% de solicitudes, exigir autenticación y dejar trazabilidad en un log de auditoría. " +
  "La disponibilidad mensual mínima será de 99.5% y el ajustador podrá consultar el estado del reclamo en cualquier momento.";

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH, headless: true, args: ["--no-sandbox"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
page.on("console", (m) => m.type() === "error" && !m.text().includes("401") && !m.text().includes("403") && !m.text().includes("409") && errors.push(`console: ${m.text()}`));

const shot = (name) => page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
const nav = (name) => page.getByRole("navigation").getByRole("button", { name, exact: true }).click();
const see = (text, opts = {}) => page.getByText(text, opts).first().waitFor({ timeout: 20000 });
let step = 0;
const log = (m) => console.log(`✓ ${String(++step).padStart(2, "0")} ${m}`);

async function login(role) {
  await page.goto(BASE);
  await page.getByLabel("Usuario").selectOption(`demo_${role}`);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("heading", { name: "Dashboard" }).waitFor();
}
const logout = () => page.getByRole("button", { name: "Salir" }).click();

// 0. credenciales inválidas
await page.goto(BASE);
await page.getByLabel("Contraseña").fill("incorrecta");
await page.getByRole("button", { name: "Entrar" }).click();
await see("Credenciales inválidas");
log("credenciales inválidas rechazadas con mensaje");

// 1. analyst: registra un requerimiento pobre, se bloquea
await login("analyst");
await shot("01-dashboard-analyst");
await see("Datos 100% sintéticos");
log("dashboard con aviso de datos sintéticos y mock");
await nav("Initiatives");
await page.getByRole("button", { name: "Registrar y analizar" }).click();
await page.getByRole("heading", { name: "Requirements" }).waitFor();
await page.getByRole("button", { name: "Analizar calidad" }).click();
await see("No cumple la Definition of Ready");
await shot("02-requerimiento-bloqueado");
log("requerimiento pobre: score bajo y bloqueo de Definition of Ready");

await nav("AI Analysis");
await page.getByRole("button", { name: "Generar historias de usuario" }).click();
const gateAlert = page.getByRole("alert").first();
await gateAlert.waitFor({ timeout: 20000 });
assert.match(await gateAlert.innerText(), /Definition of Ready/);
log("la generación se bloquea con un requerimiento no listo (gate)");

// 2. refina el requerimiento y genera los artefactos
await nav("Requirements");
await page.getByLabel("Texto del requerimiento").fill(GOOD);
await page.getByRole("button", { name: "Guardar cambios" }).click();
await page.waitForFunction(() => document.querySelector("textarea") && !document.body.innerText.includes("Hay cambios sin guardar"));
await page.getByRole("button", { name: "Analizar calidad" }).click();
await see("Cumple la Definition of Ready");
await shot("03-requerimiento-listo");
log("requerimiento refinado: cumple la Definition of Ready");

await nav("AI Analysis");
for (const k of ["historias de usuario", "criterios de aceptación", "riesgos", "arquitectura", "contrato de api"]) {
  await page.getByRole("button", { name: `Generar ${k}` }).click();
  await page.waitForTimeout(250);
}
await see("Como asegurado, quiero registrar un reclamo", { exact: false });
await see("beneficio sin confirmar");
await shot("04-artefactos");
log("5 artefactos generados; el beneficio no confirmado se marca, no se inventa");
await nav("Architecture");
await see("Contrato OpenAPI");
await shot("05-arquitectura");
log("arquitectura y contrato OpenAPI visibles");
await logout();

// 3. tech_lead: ejecuta el pipeline; no puede aprobar
await login("tech_lead");
await nav("Development");
await page.getByRole("button", { name: "Ejecutar pipeline" }).click();
await see("Ejecución #", { exact: false });
await page.getByText("espera aprobación").first().waitFor({ timeout: 60000 });
await see("14/14 pruebas pasaron");
await shot("06-pipeline");
log("pipeline ejecutado: 14/14 pruebas, estado 'espera aprobación'");
await page.getByRole("button", { name: "generated_service/app.py" }).click();
await see("Servicio generado (borrador asistido por IA)");
log("el código generado es visible y auditable");
await nav("Testing");
await see("AC-SR-2: requiere verificación manual", { exact: false });
await shot("07-testing");
log("Testing lista lo que quedó sin verificar");
await nav("Security");
await see("«No verificado» nunca cuenta como «pasó»", { exact: false });
await shot("08-security");
log("Security distingue 'no verificado' de 'pasó'");
await nav("Approvals");
await see("no decide", { exact: false });
assert.equal(await page.getByRole("button", { name: "Aprobar" }).count(), 0);
log("el tech_lead no ve controles de aprobación (segregación)");
await logout();

// 4. approver: decisión con riesgos reconocidos
await login("approver");
await nav("Approvals");
const approve = page.getByRole("button", { name: "Aprobar" });
assert.ok(await approve.isDisabled());
await page.getByLabel(/Comentario de la decisión/).fill("Revisado el reporte de readiness");
assert.ok(await approve.isDisabled(), "no debe habilitarse sin reconocer los riesgos");
await page.getByLabel(/Reconozco los riesgos residuales/).check();
assert.ok(await approve.isEnabled());
await shot("09-aprobacion");
await approve.click();
await see("Decisiones registradas");
await page.getByRole("cell", { name: "Revisado el reporte de readiness" }).waitFor();
log("aprobación exige comentario y reconocer riesgos; decisión registrada");
await logout();

// 5. tech_lead: publica el release y verifica el hash del paquete descargado
await login("tech_lead");
await nav("Releases");
await page.getByRole("button", { name: "Publicar release" }).click();
await page.getByRole("cell", { name: "v1" }).waitFor();
const shownHash = (await page.locator("td.hash").first().innerText()).trim();
const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Descargar" }).click()]);
const file = await download.path();
const actual = createHash("sha256").update(readFileSync(file)).digest("hex");
assert.equal(actual, shownHash, "el hash del zip descargado debe coincidir con el publicado");
await shot("10-release");
log(`release v1 publicado; sha256 del zip descargado coincide (${actual.slice(0, 12)}…)`);
await logout();

// 6. security: verifica la cadena de auditoría
await login("security");
await nav("Audit");
await page.getByRole("button", { name: "Verificar integridad" }).click();
await see("Cadena íntegra");
await see("pipeline.decision");
await shot("11-audit");
log("auditoría: cadena íntegra y eventos de decisión visibles");
await nav("Metrics");
await see("techo de los rangos supuestos", { exact: false });
await shot("12-metrics");
log("Metrics: 2× presentado como techo de los rangos");
await logout();

await browser.close();
assert.deepEqual(errors, [], `errores de consola/página inesperados:\n${errors.join("\n")}`);
console.log(`\nE2E OK: ${step} verificaciones, sin errores de consola. Capturas en ${OUT}/`);
