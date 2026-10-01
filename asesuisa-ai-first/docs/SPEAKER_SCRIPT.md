# Guion de 20 minutos

Medido: ≈ 2 400 palabras habladas = 17.2 min a 140 ppm, 18.6 min a 130 ppm (ritmo ejecutivo pausado), más 1–1.5 min de demo breve en la lámina 4: **18–20 min en total**. Ensayar con cronómetro y ajustar con los cortes de emergencia. Las marcas `[mm:ss]` son acumuladas. Se habla en primera persona y sin diapositivas leídas.
Cada iniciativa responde cuatro preguntas: **qué problema resuelve · qué resultado medible produce · qué riesgo introduce · cómo se controla**.
Al final hay tres cortes de emergencia si el tiempo se acorta.

---

## [00:00] Lámina 1: Tesis (2:00)

Buenos días. Me han pedido duplicar la capacidad de entrega de software en doce meses, sin sumar personas y sin deteriorar calidad,
seguridad, cumplimiento ni estabilidad. Voy a empezar por lo que creo y por lo que no.

No creo que el problema sea que escribamos código despacio. Creo que perdemos la capacidad **alrededor** del código. Una de cada cuatro horas
se va en aclaraciones y retrabajo. Nueve de cada diez pruebas se hacen a mano. Tres de cada diez cambios vuelven por documentación. Y los controles
llegan al final, cuando corregir es más caro.

Por eso mi propuesta no es "pongamos inteligencia artificial en los programadores". Es rediseñar el sistema de entrega para que cada equipo produzca
más valor con la misma gente, y que la calidad, la seguridad, el cumplimiento y la trazabilidad dejen de ser una etapa para ser parte del flujo.
La inteligencia artificial es lo que multiplica ese rediseño. No lo sustituye.

Y quiero ser claro con el número desde ya. La meta es dos veces. Voy a mostrarles qué tendría que ser verdad para llegar, y qué compromiso me parece
defendible. Prefiero darles esa conversación hoy que una sorpresa dentro de seis meses.

En los próximos veinte minutos voy a responder siete preguntas: qué proponemos, por qué, cómo, cuándo, cuánto cuesta, cómo lo medimos y cómo controlamos el riesgo. Cada lámina contesta una o dos de ellas, y al final les pido decisiones concretas.

## [02:00] Lámina 2: Estado actual → problema → oportunidad (2:30)

Veamos dónde está la capacidad. Tenemos ocho células de cinco personas. Solo una de cada cuatro personas es interna; las demás son proveedores.
Hay ocho iniciativas a la vez. El tiempo promedio de una iniciativa es de veinte semanas.

Lo que más pesa es el retrabajo: veinticinco por ciento. Y casi siempre nace en el requerimiento: llega con distintos niveles de detalle, se
aclara a mitad del desarrollo y se vuelve a hacer. Segundo, las pruebas: con solo diez por ciento automatizado, QA es un cuello de botella, y aun así el
doce por ciento de los defectos aparece después de QA. Tercero, la documentación y la evidencia: treinta por ciento de los cambios se devuelven, y cada
devolución son días. Dos releases al mes, grandes, con un ocho por ciento de incidentes atribuibles a cambios.

Un ejemplo para hacerlo concreto. Llega un requerimiento que dice que el proceso de reclamos debe ser rápido y fácil. Nadie puede construir "rápido". A mitad del desarrollo el equipo pregunta cuánto es rápido; negocio responde dos semanas después; mientras tanto se construyó una versión que luego se rehace. Ese ciclo de pregunta, espera y rehacer es el que cuesta una de cada cuatro horas. Lo que propongo es hacer esa pregunta el primer día, cuando cuesta minutos y no semanas.

Quiero señalar algo. Los datos del caso son estos. La forma en que se reparte el esfuerzo restante entre trabajo núcleo y trabajo repetitivo es
un supuesto mío: cincuenta y cinco y veinte. Lo voy a validar en los primeros treinta días, porque si el retrabajo real es menor, el techo de todo
esto baja. Prefiero decirlo yo.

Y la demanda sube cincuenta por ciento. Con las plazas congeladas, el sistema actual no escala. Esa es la oportunidad: la capacidad que necesitamos ya está
dentro de la organización, atrapada en retrabajo, esperas y trabajo manual.

## [04:30] Lámina 3: Modelo operativo (3:00)

¿Cómo recuperarla? Pasamos de ocho células tradicionales a ocho células aumentadas por una plataforma común. Sin nuevas plazas; redistribuyendo responsabilidades.

Tres cambios de rol. El líder técnico deja de redactar documentación a mano y pasa a ser la revisión humana final de la calidad técnica. QA deja de ejecutar
regresión manual y pasa a diseñar estrategia de calidad y automatización. El Scrum Master deja de ser solo ceremonias y gestiona el flujo: límite de trabajo en curso,
impedimentos, métricas.

Creamos dos figuras sin crear plazas. Un equipo virtual de Plataforma y Habilitación, de tres o cuatro personas internas reasignadas, que cuida la plataforma de IA,
los pipelines y los estándares. Y un campeón de IA por célula, con una quinta parte de su tiempo, para adopción y para llevar el feedback. Las reasignaciones
internas se reponen con capacidad de proveedores, no con plazas.

Hagámoslo tangible. Hoy, un líder técnico dedica parte de su semana a documentar a mano lo que ya hizo y a atender devoluciones de cambios por falta de evidencia. Mañana la evidencia sale del pipeline, y su tiempo se va a lo que solo él puede hacer: decidir si el diseño es correcto y si el código es seguro. Hoy, QA ejecuta regresión manual en cada release; mañana diseña la estrategia de pruebas, revisa las que se generan automáticamente y dedica su criterio a lo que de verdad lo requiere. Hoy, un analista descubre las ambigüedades cuando el equipo ya está construyendo; mañana las ve en minutos, con la pregunta de aclaración lista. Y para que la transición no sea un acto de fe, cada célula usa el mismo tablero de métricas, y cada proveedor tiene un scorecard de calidad, entrega, seguridad y documentación.

Los proveedores son la mitad de la historia, porque son tres cuartas partes de la capacidad. Hoy se les paga por horas, así que nadie gana por reducir retrabajo.
Pasamos a resultados: entregables aceptados, con calidad medida, sobre estándares y plataforma que son nuestros, y con documentación y transferencia de
conocimiento como entregable contractual. Lo que se queda adentro: arquitectura, seguridad, gobierno de IA, el conocimiento crítico del negocio y la aprobación de cambios.

¿Qué riesgo introduce esto? Resistencia. La medida es una comunicación clara: esto es capacidad, no reemplazo. Nadie sale por esta iniciativa.

## [07:30] Lámina 4: El ciclo de vida AI-First (3:00)

Aquí está el corazón. El flujo tiene catorce etapas, de negocio a aprendizaje continuo, y cada una tiene un control integrado. Les cuento las que más
capacidad recuperan.

**Primero, la entrada.** Ningún requerimiento consume capacidad hasta superar una Definition of Ready con puntaje. La plataforma analiza el texto, detecta ambigüedades y
formula la pregunta de aclaración para cada una. Si no pasa, se bloquea. Esto ataca directamente el retrabajo, que es la mayor fuga.

**Segundo, la construcción.** A partir de un requerimiento listo, la IA propone historias, criterios de aceptación, riesgos, arquitectura, contrato de API, código y pruebas.
Todo en estado borrador, y todo citando la frase del requerimiento de la que sale. Si el requerimiento no dice el beneficio, el sistema escribe "por confirmar";
no lo inventa.

**Tercero, los controles.** Antes de ejecutar cualquier código generado pasa una política estática: qué puede importar, qué no. Las pruebas verifican que el servicio cumpla
su contrato. Después, análisis estático de seguridad, escaneo de secretos y de dependencias.

**Cuarto, la salida.** La evidencia de cambio se genera sola. Y la aprobación es humana y segregada: quien ejecutó el trabajo no puede aprobarlo, y el aprobador debe reconocer
los riesgos residuales.

*[Demo breve, 60–90 segundos: requerimiento pobre → bloqueado; mejorado → artefactos; un código con `import subprocess` → bloqueado y nunca ejecutado.]*

¿El riesgo? Que pruebas generadas pasen por inercia, o que la aprobación se haga sin leer. Para lo primero, comprobamos que las pruebas **fallen** si se rompe el servicio.
Para lo segundo, mostramos qué quedó sin verificar, de forma explícita. Una verificación que no se pudo hacer aparece como "no verificada", nunca como "aprobada".

Y una aclaración honesta: lo que ven es una demostración con datos sintéticos, y el generador es determinista, no un modelo de lenguaje real. Demuestra el flujo y los controles.

## [10:30] Lámina 5: Arquitectura y gobierno (3:00)

La arquitectura tiene un principio: independencia del modelo y de la nube. Entre la aplicación y el modelo hay un Gateway. Todo acceso pasa por él. Ahí se redacta la
información personal **antes** de que llegue al proveedor, se valida la salida contra un esquema, se hace respaldo con otro proveedor si falla uno, y se audita cada
llamada con el modelo y la versión del prompt. Cambiar de proveedor es configuración. Eso es control de costo y es el plan de salida que cualquier regulador pide.

Gobierno. Definimos niveles de autonomía de cero a cinco. El primer año, el techo es tres: la IA ejecuta con aprobación humana. Hay cosas que una IA nunca hace: aprobar su propio
código o su propia evidencia, desplegar cambios críticos sin controles, modificar controles regulatorios, borrar trazabilidad. No es una política escrita; en el MVP no
existe una identidad de IA con permisos de aprobación.

Auditoría: cada evento queda en una cadena de hashes que se puede verificar, con usuario, rol, modelo, versión del prompt, referencias de entrada y salida, aprobación y decisión.
Y evaluación: ningún cambio de prompt o de modelo se promueve sin pasar los conjuntos de referencia.

En regulación, tengo que ser preciso. La NRP-23, de gestión de la seguridad de la información, **aplica expresamente a sociedades de seguros**; lo comprobé en el artículo 2.
Y trae algo que importa mucho aquí: usar un modelo alojado por un tercero es **tercerizar actividades de TI**, con condiciones sobre propiedad de los datos, aislamiento, auditoría
del regulador y plan de salida. Por eso propongo empezar con datos sintéticos o enmascarados y no enviar datos de clientes a un proveedor externo hasta cerrar ese expediente con Cumplimiento.
Además, hay normas que **no** he podido confirmar, como la ley de protección de datos, y las dejo marcadas como por confirmar. No voy a afirmar cumplimiento que no puedo demostrar.

El riesgo de todo esto: que el sandbox de pruebas de mi demo es de proceso, no de contenedor. Para un modelo real en producción exige contenedor sin red. Es la brecha de seguridad número uno y la tengo anotada.

## [13:30] Lámina 6: Roadmap (2:30)

Cuándo. Cinco tramos, cada uno con una decisión y un criterio de parada.

En los primeros treinta días: diagnóstico. Medimos de verdad, no de supuestos. Política de IA, comité ligero, congelamos el trabajo en curso y elegimos dos células piloto.
Entre treinta y noventa: los pilotos con Definition of Ready y el pipeline. Entre tres y seis meses: escalamos a siete células y pasamos a contratos por resultados.
De seis a nueve: las ocho células y modernización de legacy, acotada. De nueve a doce: consolidar y medir.

Mis primeros noventa días tienen decisiones que no delego: cómo se define y mide la capacidad entregada, qué células son piloto, qué se automatiza y qué no con
Cumplimiento, qué modelo y con qué datos.

Déjenme concretar el primer mes, porque es donde se decide si esto funciona. Primero, escuchar: hablo con ustedes, con los líderes de célula y con los proveedores. Segundo, medir: en dos células registro dónde se va el tiempo durante dos semanas, para confirmar o corregir mi supuesto de veinticinco, veinte y cincuenta y cinco. Tercero, acordar con Cumplimiento qué se puede automatizar y con qué evidencia, y qué normas aplican; yo ya verifiqué que la NRP-23 incluye a las aseguradoras, pero ellos tienen la última palabra. Y cuarto, definir con ustedes los criterios de decisión de los noventa días **antes** de ver resultados, para no acomodarlos después. Son simples: si el retrabajo baja al menos cinco puntos y ninguna salvaguarda empeora, escalamos. Si mejora la velocidad pero empeora una salvaguarda, corregimos antes de crecer. Y si la adopción es menor al treinta por ciento, no escalamos: revisamos cómo estamos cambiando el trabajo, no cuántas licencias compramos.

Y el punto clave: a los noventa días hay una decisión de continuar, ajustar o parar, con reglas acordadas el día treinta. Si mejora la velocidad pero empeora una salvaguarda, **ajustamos**;
no escalamos.

## [16:00] Lámina 7: Caso de negocio (2:30)

Ahora el número, con honestidad.

Mi modelo suma cinco palancas: el retrabajo, la automatización del trabajo repetitivo, la IA sobre el trabajo núcleo, el reuso de activos y la gestión de la demanda. Resultado:
caso conservador, uno coma veintidós; base, uno coma cuarenta y ocho; y el máximo, uno coma ochenta de capacidad, que son dos veces en capacidad de **valor** si además diferimos diez por ciento de alcance.

Lo que dice el modelo, sin suavizar. Uno: la palanca principal es el retrabajo, no el código. Si la IA falla del todo en el caso base, perdemos menos que si falla el retrabajo.
Dos: dos veces es el techo de mis rangos, no el valor esperado. Exige todo en su máximo, o el caso base **más** descartar o diferir alrededor del veintiséis por ciento del alcance
de bajo valor. Con adopción parcial, mi simulación da una mediana de uno coma cuarenta y dos. Por eso el compromiso es una escalera: piso de uno coma tres, objetivo de uno coma cinco, que cubre el aumento de demanda, y la meta de dos con su camino explícito.

Si el negocio acepta diferir ese veintiséis por ciento, la inteligencia artificial deja de ser la parte frágil del plan. Y es un buen indicador de madurez: que lo más difícil de esta transformación no sea la tecnología, sino la priorización.

En dinero: inversión del primer año de unos doscientos sesenta mil dólares, que son supuestos. En el caso base, el primer año deja unos doscientos veintidós mil netos y se recupera en unos tres meses. El conservador **pierde**
cuarenta y tres mil el primer año. No es ahorro de caja, es costo evitado de contratar esa capacidad, o valor de entregar la demanda adicional. Los montos son ilustrativos hasta que Finanzas aporte los reales.

Y las salvaguardas: calidad, seguridad, cumplimiento y estabilidad. Una mejora de velocidad que empeora una de ellas la reporto como **fallo**.

## [18:30] Lámina 8: Riesgos y decisiones (1:30)

Los riesgos principales: la adopción baja; la fuga de datos; el código inseguro; que el punto de partida real sea distinto al supuesto; que se degrade una salvaguarda. Cada uno tiene un control y un dueño.

Y qué no voy a hacer: no voy a prometer cien por ciento de automatización, no voy a enviar datos de clientes sin cerrar el expediente de tercerización, no voy a eliminar un control sin cobertura demostrable.

Les pido cinco decisiones: aprobar la política de uso de IA; congelar el trabajo en curso en seis, que es lo que más nos acerca a dos; dos células piloto con un presupuesto mínimo; el compromiso escalonado con una revisión a noventa días;
y, con Cumplimiento, confirmar las normas aplicables y dónde se aloja el modelo.

En doce meses sabremos que funcionó si la capacidad de valor medida supera el piso, si ninguna salvaguarda empeoró y si entregamos el cincuenta por ciento adicional de demanda sin una sola plaza nueva.

Una última idea: si en doce meses lo único que hubiéramos logrado fuera medir bien dónde se pierde la capacidad y corregir la entrada de los requerimientos, ya habríamos mejorado el sistema. Todo lo demás se construye sobre esa base.

Gracias. Quedo para sus preguntas.

---

## Cortes de emergencia
- **Si quedan 15 min:** saltar la demo y comprimir la lámina 6 a su tabla.
- **Si quedan 10 min:** láminas 1, 3, 5 (solo regulación y brecha del sandbox) y 7.
- **Si quedan 5 min:** tesis, número en escalera, riesgos y las cinco decisiones.

## Frases a evitar
"La IA lo resuelve todo" · "cien por ciento automatizado" · "cero riesgo" · "reemplazamos desarrolladores" · "cumplimos con la regulación" (sin evidencia) · "garantizamos 2×".
