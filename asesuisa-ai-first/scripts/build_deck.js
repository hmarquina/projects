// Genera docs/presentacion-director-soluciones.pptx (8 láminas) a partir del contenido de docs/PRESENTATION.md.
// Uso: node scripts/build_deck.js   (requiere pptxgenjs). Las cifras salen del modelo documentado en docs/PRODUCTIVITY_MODEL.md.
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "docs", "presentacion-director-soluciones.pptx");

// Paleta con dominancia del azul marino; ámbar solo para salvedades; verde/rojo solo para estado.
const C = {
  navy: "14253D", blue: "1F4E8C", sky: "DCE8F7", ink: "1B2430", muted: "5B6776", line: "D9DEE5",
  bg: "F4F6F8", white: "FFFFFF", amber: "8A5A00", amberBg: "FFF3D6", ok: "1D7A46", okBg: "E4F4EA", bad: "B3261E", badBg: "FBE9E7",
};
const HEAD = "Cambria", BODY = "Calibri";
const W = 13.33, H = 7.5, MX = 0.6;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Transformación AI-First del ciclo de entrega — Director de Soluciones";
pres.author = "Candidato a Director de Soluciones";

const text = (s, t, o) => s.addText(t, { fontFace: BODY, color: C.ink, isTextBox: true, margin: 0, valign: "top", ...o });
const title = (s, t, dark = false) =>
  text(s, t, { x: MX, y: 0.45, w: W - 2 * MX, h: 1.0, fontFace: HEAD, fontSize: 32, bold: true, color: dark ? C.white : C.navy, valign: "middle" });
const footer = (s, dark = false) =>
  text(s, "Datos del caso y cifras de palancas, costos y retorno: supuestos (ver ASSUMPTIONS.md). Datos de la demo: sintéticos.", {
    x: MX, y: H - 0.42, w: W - 2 * MX - 0.8, h: 0.3, fontSize: 10, color: dark ? "9AA8B8" : C.muted, valign: "middle",
  });
const card = (s, x, y, w, h, fill = C.bg, shadow = false) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill }, line: { color: C.line, width: 0.75 }, rectRadius: 0.08,
    ...(shadow ? { shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 } } : {}),
  });
const bullets = (items, o = {}) =>
  items.map((t, i) => ({
    text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: 8, ...o },
  }));

// ---------------------------------------------------------------- 1. Tesis
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  text(s, "TRANSFORMACIÓN AI-FIRST DEL CICLO DE ENTREGA DE SOFTWARE", { x: MX, y: 0.55, w: 11, h: 0.4, fontSize: 14, color: "9AA8B8", charSpacing: 2 });
  text(s, "Duplicar la capacidad no es duplicar el esfuerzo", {
    x: MX, y: 1.25, w: 11.4, h: 1.9, fontFace: HEAD, fontSize: 48, bold: true, color: C.white, valign: "top",
  });
  text(s, "La capacidad que falta no está en escribir código más rápido: está en lo que se pierde alrededor del código. Rediseñamos el sistema de entrega y la IA lo multiplica, con los controles integrados al flujo.", {
    x: MX, y: 3.2, w: 9.6, h: 1.0, fontSize: 18, color: "CFD8E6",
  });
  const stats = [["25%", "de la capacidad se va en aclaraciones y retrabajo"], ["10%", "de las pruebas están automatizadas"], ["30%", "de los cambios vuelve por documentación"]];
  stats.forEach(([n, l], i) => {
    const x = MX + i * 4.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.55, w: 3.8, h: 1.55, fill: { color: "1D3558" }, line: { color: "2B4A75", width: 0.75 }, rectRadius: 0.08 });
    text(s, n, { x: x + 0.3, y: 4.68, w: 1.6, h: 1.2, fontFace: HEAD, fontSize: 44, bold: true, color: C.white, valign: "middle" });
    text(s, l, { x: x + 1.85, y: 4.68, w: 1.8, h: 1.2, fontSize: 14, color: "CFD8E6", valign: "middle" });
  });
  text(s, "Meta de la dirección: 2×  ·  Compromiso en escalera: piso 1.3×, objetivo 1.5×, meta 2× con camino explícito  ·  Autonomía de IA L3, aprobación siempre humana", {
    x: MX, y: 6.4, w: W - 2 * MX, h: 0.4, fontSize: 14, bold: true, color: "F2C14E",
  });
  footer(s, true);
  s.addNotes("QUÉ / POR QUÉ. Abrir con la tesis, no con la tecnología. Dar las tres cifras del caso y, en el mismo minuto, decir que 2× es la meta de la dirección y que voy a mostrar qué tendría que ser verdad para llegar y qué compromiso me parece defendible. Credibilidad desde el primer minuto: la cifra y su límite a la vez. Adelantar la estructura: siete preguntas (qué, por qué, cómo, cuándo, cuánto, cómo medir, cómo controlar el riesgo) y, al final, decisiones concretas. Tiempo: 2:00.");
}

// ---------------------------------------------------------------- 2. Estado actual
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "El sistema actual pierde capacidad en cinco sitios y la demanda sube 50%");
  s.addChart(pres.charts.BAR, [
    { name: "Retrabajo y aclaraciones (dato del caso)", labels: ["Capacidad actual"], values: [25] },
    { name: "Trabajo repetitivo (supuesto)", labels: ["Capacidad actual"], values: [20] },
    { name: "Trabajo núcleo (supuesto)", labels: ["Capacidad actual"], values: [55] },
  ], {
    x: MX, y: 1.7, w: 6.0, h: 4.6, barDir: "bar", barGrouping: "percentStacked", chartColors: [C.bad, C.amber, C.blue],
    showValue: true, dataLabelColor: C.white, dataLabelFontSize: 16, dataLabelFontBold: true, dataLabelPosition: "ctr", dataLabelFormatCode: '0"%"',
    showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: C.ink,
    showTitle: true, title: "¿Dónde se va la capacidad? (base = 100)", titleFontSize: 14, titleColor: C.navy,
    catAxisLabelColor: C.ink, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, barGapWidthPct: 40,
  });
  card(s, 7.0, 1.7, 5.75, 4.6, C.bg);
  text(s, bullets([
    "25% en aclaraciones y retrabajo: casi siempre nace en el requerimiento.",
    "10% de pruebas automatizadas: QA es el cuello de botella y 12% de los defectos aparece después de QA.",
    "30% de cambios devueltos por documentación; 2 releases al mes; 8% de incidentes por cambio.",
    "75% de la capacidad es externa; 8 iniciativas simultáneas sobre 8 células.",
  ], { fontSize: 16 }), { x: 7.3, y: 1.95, w: 5.2, h: 3.4 });
  text(s, "Lead time 20 semanas  ·  Defectos post-QA 12%  ·  Change failure rate 8%", { x: 7.3, y: 5.5, w: 5.2, h: 0.6, fontSize: 13, bold: true, color: C.blue });
  text(s, "La distribución 20 / 55 es un supuesto propio: se valida en 30 días con muestreo de tiempos.", { x: MX, y: 6.45, w: 6.0, h: 0.4, fontSize: 12, italic: true, color: C.amber });
  footer(s);
  s.addNotes("POR QUÉ. Los datos del caso son estos; el reparto 20/55 del resto es un supuesto mío y lo digo yo antes de que me lo pregunten: si el retrabajo real es menor, el techo del modelo baja. Ejemplo concreto: un requerimiento dice 'rápido y fácil'; a mitad del desarrollo el equipo pregunta cuánto es rápido; negocio responde dos semanas después; mientras tanto se construyó algo que se rehace. Ese ciclo pregunta-espera-rehacer cuesta una de cada cuatro horas. Propongo hacer la pregunta el primer día. Tiempo: 2:30.");
}

// ---------------------------------------------------------------- 3. Modelo operativo
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "De 8 células tradicionales a 8 células aumentadas por una plataforma común");
  // plataforma (banda externa) + célula (interior)
  card(s, MX, 1.7, 6.3, 4.65, C.sky);
  text(s, "PLATAFORMA AI-FIRST COMÚN", { x: MX + 0.25, y: 1.82, w: 5.8, h: 0.35, fontSize: 12, bold: true, color: C.blue, charSpacing: 1 });
  const mods = ["Gateway de IA", "Pipeline y gates", "Evaluación", "Evidencia"];
  mods.forEach((m, i) => {
    const x = MX + 0.25 + i * 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.25, w: 1.4, h: 0.7, fill: { color: C.white }, line: { color: C.blue, width: 1 }, rectRadius: 0.06 });
    text(s, m, { x, y: 2.25, w: 1.4, h: 0.7, fontSize: 12, bold: true, color: C.navy, align: "center", valign: "middle" });
  });
  card(s, MX + 0.25, 3.2, 5.8, 2.9, C.white);
  text(s, "UNA CÉLULA (5 personas, sin plazas nuevas)", { x: MX + 0.5, y: 3.32, w: 5.3, h: 0.3, fontSize: 12, bold: true, color: C.muted });
  const roles = [["Scrum Master", "gestiona el flujo y el WIP"], ["Líder técnico", "revisa; no documenta a mano"], ["2 Desarrolladores", "ingeniería asistida"], ["QA", "ingeniería de calidad"]];
  roles.forEach(([r, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + 0.5 + col * 2.75, y = 3.75 + row * 1.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.6, h: 1.0, fill: { color: C.bg }, line: { color: C.line, width: 0.75 }, rectRadius: 0.06 });
    text(s, r, { x: x + 0.15, y: y + 0.12, w: 2.3, h: 0.3, fontSize: 14, bold: true, color: C.navy });
    text(s, d, { x: x + 0.15, y: y + 0.5, w: 2.3, h: 0.4, fontSize: 12, color: C.muted });
  });
  text(s, bullets([
    "Platform & Enablement: 3–4 personas internas reasignadas, repuestas con proveedores; un AI Champion (≈20%) por célula.",
    "Proveedores: de horas a resultados, sobre estándares de la compañía; documentación y transferencia como entregable.",
    "Interno: arquitectura, seguridad, gobierno de IA, dominio crítico y aprobación de cambios.",
    "Capacidad, no reemplazo: nadie sale por esta iniciativa.",
  ], { fontSize: 16 }), { x: 7.2, y: 1.8, w: 5.5, h: 3.9 });
  text(s, "WIP 8 → 6  ·  Pruebas automatizadas 10% → 60%+", { x: 7.2, y: 5.75, w: 5.5, h: 0.5, fontSize: 14, bold: true, color: C.blue });
  footer(s);
  s.addNotes("CÓMO. Tres cambios de rol: el líder técnico deja de documentar a mano y es la revisión humana final; QA deja la regresión manual y diseña calidad; el Scrum Master gestiona el flujo. Dos figuras sin plazas nuevas: Platform & Enablement (internos reasignados, repuestos con capacidad de proveedores) y un campeón de IA por célula. Proveedores: hoy se paga por horas, nadie gana por reducir retrabajo; pasamos a resultados con scorecard de calidad, entrega, seguridad y documentación. Riesgo: resistencia; control: 'capacidad, no reemplazo'. Tiempo: 3:00.");
}

// ---------------------------------------------------------------- 4. SDLC
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "Ciclo AI-First: IA en todo el flujo y un control en cada paso");
  const gates = [["Definition of Ready", "score ≥ 75 y análisis vigente"], ["AI Readiness", "política estática antes de ejecutar"], ["Quality", "pruebas contra el contrato"], ["Security", "SAST, secretos, dependencias"], ["Release", "aprobación humana segregada"], ["Producción", "verificación y observabilidad"]];
  const gw = 1.85, gap = 0.2;
  gates.forEach(([g, d], i) => {
    const x = MX + i * (gw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.75, w: gw, h: 1.25, fill: { color: i === 4 ? C.navy : C.sky }, line: { color: C.blue, width: 0.75 }, rectRadius: 0.08 });
    text(s, g, { x: x + 0.1, y: 1.82, w: gw - 0.2, h: 0.55, fontSize: 13, bold: true, color: i === 4 ? C.white : C.navy, align: "center", valign: "middle" });
    text(s, d, { x: x + 0.1, y: 2.42, w: gw - 0.2, h: 0.55, fontSize: 11, color: i === 4 ? "CFD8E6" : C.muted, align: "center" });
    if (i < gates.length - 1) text(s, "›", { x: x + gw - 0.02, y: 2.05, w: gap + 0.04, h: 0.6, fontSize: 24, bold: true, color: C.blue, align: "center", valign: "middle" });
  });
  const cols = [
    ["Entrada", ["Ningún requerimiento consume capacidad sin superar la Definition of Ready.", "Ambigüedades con su cita y su pregunta de aclaración."]],
    ["Construcción", ["Historias, criterios, riesgos, contrato, código y pruebas generados como borrador.", "Todo cita la frase fuente; lo desconocido se marca «por confirmar»."]],
    ["Salida", ["Evidencia de cambio automática y readiness.", "Aprobación humana: quien ejecuta no aprueba y reconoce los riesgos."]],
  ];
  cols.forEach(([h, items], i) => {
    const x = MX + i * 4.1;
    card(s, x, 3.3, 3.95, 2.55, C.bg);
    text(s, h, { x: x + 0.25, y: 3.42, w: 3.5, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: C.navy });
    text(s, bullets(items, { fontSize: 14 }), { x: x + 0.25, y: 3.9, w: 3.5, h: 1.85 });
  });
  text(s, "Devoluciones documentales 30% → 8%   ·   Defectos post-QA 12% → 6%   ·   Un control que no se pudo ejecutar figura «no verificado», nunca «pasó»", {
    x: MX, y: 6.1, w: W - 2 * MX, h: 0.6, fontSize: 14, bold: true, color: C.blue,
  });
  footer(s);
  s.addNotes("CÓMO / CÓMO CONTROLAR EL RIESGO. El flujo tiene catorce etapas; estas seis puertas son las que importan. Entrada: ataca el retrabajo en su origen. Construcción: la IA propone, siempre en borrador y citando la frase del requerimiento; si falta el beneficio, escribe 'por confirmar', no lo inventa. Controles: política estática antes de ejecutar código generado; pruebas que verifican el contrato; SAST, secretos y dependencias. Salida: evidencia automática y aprobación humana segregada. DEMO (60-90 s): requerimiento pobre bloqueado; refinado; un código con 'import subprocess' bloqueado y nunca ejecutado. Aclarar: datos sintéticos y el generador es determinista, no un LLM. Riesgos: pruebas que pasan por inercia (se comprueba rompiendo el servicio) y aprobación sin leer (se muestra lo no verificado). Tiempo: 3:00.");
}

// ---------------------------------------------------------------- 5. Arquitectura y gobierno
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "Arquitectura y gobierno: independiente del modelo, con el control en el Gateway");
  const layers = [["Aplicación", "API (FastAPI) · RBAC · auditoría", C.sky, C.navy], ["Orquestación de IA", "registro de prompts · gates · evaluación", C.sky, C.navy], ["Model Gateway", "redacta PII · valida la salida · fallback · audita", C.navy, C.white], ["Proveedor de modelo", "mock determinista hoy · nube, on-premises o modelo propio", C.bg, C.navy]];
  layers.forEach(([t, d, fill, fg], i) => {
    const y = 1.75 + i * 1.12;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y, w: 5.6, h: 0.9, fill: { color: fill }, line: { color: C.blue, width: 0.75 }, rectRadius: 0.08 });
    text(s, t, { x: MX + 0.25, y: y + 0.08, w: 5.1, h: 0.36, fontSize: 16, bold: true, color: fg });
    text(s, d, { x: MX + 0.25, y: y + 0.46, w: 5.1, h: 0.36, fontSize: 12, color: fg === C.white ? "CFD8E6" : C.muted });
    if (i < layers.length - 1) text(s, "▼", { x: MX + 2.6, y: y + 0.88, w: 0.4, h: 0.26, fontSize: 11, color: C.blue, align: "center", valign: "middle" });
  });
  text(s, "Auditoría append-only con hash encadenado  ·  Evaluación con golden datasets", { x: MX, y: 6.3, w: 5.6, h: 0.4, fontSize: 12, bold: true, color: C.blue });
  text(s, bullets([
    "Autonomía L0–L5; techo L3 el primer año. La IA nunca aprueba su propio trabajo ni cambia controles regulatorios.",
    "Cada llamada deja modelo, versión del prompt y hashes. Ningún cambio de prompt o modelo se promueve sin pasar la evaluación.",
    "NRP-23 aplica expresamente a sociedades de seguros (Art. 2 d). Un LLM externo es tercerización de TI (Arts. 14 y 26, Anexo 1).",
    "Brecha reconocida: el sandbox de la demo es de proceso, no de contenedor.",
  ], { fontSize: 15 }), { x: 6.7, y: 1.75, w: 6.0, h: 4.0 });
  text(s, "148 pruebas del backend (también contra PostgreSQL real)  ·  27 de UI  ·  16 verificaciones E2E", { x: 6.7, y: 5.85, w: 6.0, h: 0.6, fontSize: 13, bold: true, color: C.blue });
  footer(s);
  s.addNotes("CÓMO CONTROLAR EL RIESGO. Principio: independencia del modelo y de la nube. Todo acceso a modelos pasa por el Gateway: redacta información personal antes de que llegue al proveedor, valida la salida contra un esquema, hace respaldo si falla un proveedor y audita. Cambiar de proveedor es configuración: control de costo y plan de salida. Autonomía de 0 a 5, techo 3 el primer año; en el MVP no existe una identidad de IA con permisos de aprobación. REGULACIÓN, con precisión: la NRP-23 aplica expresamente a sociedades de seguros (lo comprobé en el Art. 2 d); usar un modelo alojado por un tercero es tercerizar actividades de TI, con condiciones de propiedad de datos, aislamiento, acceso del regulador y plan de salida; por eso propongo datos sintéticos o enmascarados hasta cerrar ese expediente con Cumplimiento. Hay normas que NO he podido confirmar (ley de datos personales) y las dejo por confirmar. No afirmo cumplimiento. Brecha: el sandbox de la demo es de proceso; para un LLM real, contenedor sin red. Tiempo: 3:00.");
}

// ---------------------------------------------------------------- 6. Roadmap
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "Roadmap de 12 meses: primero medir, luego escalar");
  const phases = [
    ["0–30 días", "Diagnóstico y baseline medido", "Política de IA · normas confirmadas · 2 células piloto", "Aprobar política y WIP"],
    ["30–90 días", "Pilotos y plataforma", "DoR y pipeline en 2 células · primer scorecard", "Escalar, ajustar o parar"],
    ["3–6 meses", "Escalar y automatizar", "7 células · ≥ 35% automatizado · contratos por resultados", "Modelo con proveedores"],
    ["6–9 meses", "Cobertura total y legacy", "8 células · ≥ 50% automatizado · change failure ≤ 6%", "Inversión en legacy"],
    ["9–12 meses", "Consolidar y medir", "Targets a régimen · informe auditable", "Plan del año 2"],
  ];
  const pw = 2.3, pg = 0.12;
  phases.forEach(([when, goal, deliver, decision], i) => {
    const x = MX + i * (pw + pg);
    card(s, x, 1.75, pw, 3.35, i === 1 ? C.sky : C.bg, i === 1);
    text(s, when, { x: x + 0.18, y: 1.88, w: pw - 0.36, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: C.navy });
    text(s, goal, { x: x + 0.18, y: 2.3, w: pw - 0.36, h: 0.7, fontSize: 14, bold: true, color: C.blue });
    text(s, deliver, { x: x + 0.18, y: 3.05, w: pw - 0.36, h: 1.05, fontSize: 12, color: C.ink });
    text(s, "DECISIÓN", { x: x + 0.18, y: 4.2, w: pw - 0.36, h: 0.25, fontSize: 10, bold: true, color: C.muted, charSpacing: 1 });
    text(s, decision, { x: x + 0.18, y: 4.45, w: pw - 0.36, h: 0.55, fontSize: 13, bold: true, color: C.navy });
  });
  card(s, MX, 5.3, W - 2 * MX, 1.2, C.amberBg);
  text(s, "Decisión a los 90 días (criterios pactados el día 30, antes de ver resultados)", { x: MX + 0.25, y: 5.38, w: 11.5, h: 0.32, fontSize: 13, bold: true, color: C.amber });
  text(s, "Retrabajo −5 puntos y salvaguardas estables → escalar   ·   Mejora la velocidad pero empeora una salvaguarda → ajustar   ·   Adopción < 30% → no escalar: revisar el diseño del cambio", {
    x: MX + 0.25, y: 5.75, w: 11.6, h: 0.65, fontSize: 14, color: C.ink,
  });
  footer(s);
  s.addNotes("CUÁNDO. Cinco tramos, cada uno con una decisión y un criterio de parada. Primer mes: escuchar, medir (en dos células registro dónde se va el tiempo durante dos semanas, para confirmar o corregir 25/20/55), acordar con Cumplimiento qué se automatiza y qué normas aplican, y fijar los criterios de decisión de los 90 días ANTES de ver resultados. Mis primeras decisiones personales: cómo se define y mide la capacidad entregada, qué células son piloto, qué se automatiza y qué no, qué modelo y con qué datos. A los 90 días: continuar, ajustar o parar. Si mejora la velocidad pero empeora una salvaguarda, ajustamos; no escalamos. Quick wins: calidad del requerimiento, pruebas automatizadas y evidencia. Tiempo: 2:30.");
}

// ---------------------------------------------------------------- 7. Caso de negocio
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  title(s, "Caso de negocio: el valor viene del retrabajo, del trabajo repetitivo y de la demanda");
  const cats = ["Base", "Retrabajo", "Trabajo repetitivo", "IA en núcleo", "Reuso", "Gestión de demanda"];
  s.addChart([
    { type: pres.charts.BAR, data: [{ name: "Capacidad acumulada (caso Base)", labels: cats, values: [1.0, 1.15, 1.28, 1.43, 1.48, 1.61] }],
      options: { barDir: "col", chartColors: [C.blue], barGapWidthPct: 45, showValue: true, dataLabelPosition: "inBase", dataLabelFormatCode: '0.00"×"', dataLabelColor: C.white, dataLabelFontSize: 12, dataLabelFontBold: true } },
    { type: pres.charts.LINE, data: [{ name: "Demanda +50% (1.5×)", labels: cats, values: [1.5, 1.5, 1.5, 1.5, 1.5, 1.5] }, { name: "Meta 2×", labels: cats, values: [2, 2, 2, 2, 2, 2] }],
      options: { chartColors: [C.amber, C.bad], lineSize: 2, lineDash: ["dash", "dash"], lineDataSymbol: "none" } },
  ], {
    x: MX, y: 1.65, w: 7.3, h: 4.75, showTitle: true, title: "Puente de capacidad: caso Base (supuestos)", titleFontSize: 14, titleColor: C.navy,
    showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 2.2, valAxisMajorUnit: 0.5,
    valAxisLabelColor: C.muted, catAxisLabelColor: C.ink, catAxisLabelFontSize: 11, valAxisLabelFormatCode: '0.0"×"',
    valGridLine: { color: C.line, size: 0.5 }, catGridLine: { style: "none" },
  });
  // tabla de escenarios
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center", valign: "middle", fontSize: 12 } });
  const cell = (t, o = {}) => ({ text: t, options: { align: "center", valign: "middle", fontSize: 13, color: C.ink, ...o } });
  s.addTable([
    [hdr("Escenario"), hdr("Capacidad"), hdr("De valor")],
    [cell("Conservador", { align: "left" }), cell("1.22×"), cell("1.28×")],
    [cell("Base", { align: "left" }), cell("1.48×"), cell("1.61×")],
    [cell("Stretch", { align: "left", bold: true }), cell("1.80×", { bold: true }), cell("2.00×", { bold: true, color: C.bad })],
  ], { x: 8.2, y: 1.75, w: 4.55, colW: [1.75, 1.4, 1.4], rowH: 0.36, fontFace: BODY, border: { type: "solid", color: C.line, pt: 0.75 }, margin: [2, 6, 2, 6] });
  text(s, bullets([
    "2× de valor es el techo de los rangos, no un valor esperado: exige el Stretch completo, o el Base más diferir ≈ 26% del alcance.",
    "Simulación con adopción parcial: mediana 1.42× (P10 1.31 – P90 1.54); P(≥1.5×) = 19%.",
    "Inversión año 1 ≈ $261 k (supuesto). Base: neto ≈ +$222 k, recuperación ≈ 3 meses. Conservador: ≈ −$43 k.",
  ], { fontSize: 13 }), { x: 8.2, y: 3.4, w: 4.55, h: 2.6 });
  text(s, "Costo evitado, no ahorro de caja. Salvaguardas: calidad, seguridad, cumplimiento y estabilidad.", { x: 8.2, y: 6.0, w: 4.55, h: 0.5, fontSize: 11, italic: true, color: C.muted });
  footer(s);
  s.addNotes("CUÁNTO / CÓMO MEDIR. Cinco palancas: retrabajo, trabajo repetitivo, IA sobre el núcleo, reuso y gestión de la demanda. Lo que dice el modelo, sin suavizar: (1) la palanca principal es el retrabajo, no el código; (2) 2× es el techo de mis rangos, no el valor esperado; (3) el caso Base (1.48×) no cubre por sí solo el +50% de demanda, lo cubre en valor (1.61×); (4) con adopción parcial la mediana simulada es 1.42×. Por eso el compromiso es una escalera: piso 1.3× (≈92% de probabilidad en la simulación), objetivo 1.5×, meta 2× con su camino explícito. Si el negocio acepta diferir ese 26%, la IA deja de ser la parte frágil del plan. En dinero: son costos evitados (no se contrata a nadie), los montos son ilustrativos hasta que Finanzas aporte los reales, y el conservador pierde dinero el primer año. Una mejora de velocidad que empeora una salvaguarda se reporta como fallo. Tiempo: 2:30.");
}

// ---------------------------------------------------------------- 8. Riesgos y decisiones
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  title(s, "Riesgos, decisiones y resultados esperados", true);
  const rows = [
    ["Adopción baja", "AI Champions, pilotos voluntarios, métrica de adopción"],
    ["Fuga de datos", "PII redactada antes del modelo; sin datos de clientes a terceros hasta cerrar la tercerización"],
    ["Código inseguro", "Política estática, SAST, pruebas contra contrato, aprobación humana"],
    ["Baseline distinto del supuesto", "Medir en 30 días antes de comprometer cifras"],
    ["Una salvaguarda se degrada", "Regla anti-Goodhart: no se escala; se corrige"],
  ];
  const hd = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: "2B4A75" }, fontSize: 12 } });
  s.addTable([[hd("Riesgo"), hd("Control")], ...rows.map(([a, b]) => [
    { text: a, options: { bold: true, color: C.white, fill: { color: "1D3558" }, fontSize: 13 } },
    { text: b, options: { color: "E3EAF4", fill: { color: "1D3558" }, fontSize: 12 } },
  ])], { x: MX, y: 1.65, w: 6.3, colW: [2.05, 4.25], rowH: 0.56, fontFace: BODY, border: { type: "solid", color: "2B4A75", pt: 0.75 }, margin: [3, 8, 3, 8] });
  text(s, "CINCO DECISIONES QUE PIDO", { x: 7.3, y: 1.65, w: 5.4, h: 0.35, fontSize: 12, bold: true, color: "F2C14E", charSpacing: 1 });
  text(s, [
    "Aprobar la política de uso de IA y el comité ligero.",
    "Congelar el WIP en 6 y priorizar el portafolio con el negocio.",
    "Dos células piloto y un presupuesto mínimo de plataforma.",
    "Compromiso escalonado con revisión a los 90 días.",
    "Con Cumplimiento: normas aplicables y dónde se aloja el modelo.",
  ].map((t, i, a) => ({ text: t, options: { bullet: { type: "number" }, breakLine: i < a.length - 1, paraSpaceAfter: 6 } })), {
    x: 7.3, y: 2.05, w: 5.45, h: 2.95, fontSize: 14, color: C.white,
  });
  card(s, MX, 5.4, W - 2 * MX, 1.4, "1D3558");
  text(s, "Sabremos en 12 meses que funcionó si…", { x: MX + 0.3, y: 5.5, w: 11.5, h: 0.35, fontSize: 13, bold: true, color: "F2C14E" });
  text(s, "La capacidad de valor medida supera el piso comprometido  ·  Calidad, seguridad, cumplimiento y estabilidad no empeoraron  ·  Entregamos la demanda adicional de +50% sin una sola plaza nueva  ·  Los proveedores trabajan por resultados", {
    x: MX + 0.3, y: 5.88, w: 11.8, h: 0.85, fontSize: 14, color: C.white,
  });
  footer(s, true);
  s.addNotes("TODO, y la petición. Cerrar con las decisiones, no con un resumen. Qué NO haré: prometer 100% de automatización, enviar datos de clientes sin cerrar el expediente de tercerización, eliminar un control sin cobertura demostrable, reemplazar personas con IA. Dejar el tiempo de preguntas con las tres más probables preparadas: (1) ¿duplicamos? — meta 2× de valor, techo de mis rangos, camino explícito, piso 1.3×, medimos a los 90 días; (2) ¿fuga de datos? — el modelo nunca ve PII, sin datos de clientes a terceros hasta cerrar la tercerización; (3) ¿quién responde por un error de la IA? — quien aprueba, segregado, auditado y con riesgos reconocidos. Tiempo: 1:30.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("escrito:", f));
