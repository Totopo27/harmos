/**
 * tet_circle.js
 * Objeto UI nativo de Max MSP (Max JSUI / mgraphics) para visualización vectorial interactiva,
 * análisis de simetrías de inversión y exportación SVG en temperamentos n-TET (3 a 72 divisiones).
 *
 * Se ejecuta directamente en el lienzo del patcher dentro de una caja [jsui tet_circle.js].
 * CERO dependencias de navegadores web o servidores externos.
 *
 * Inlets:
 *  0: Suma de indices S (int) / mensajes ('divisions <N>', 'sum <S>', 'export_svg <path>', 'bang')
 *  1: Divisiones n-TET (int 3..72)
 *
 * Outlets:
 *  0: Lista aplanada de pares de inversion [i1, partner1, i2, partner2, ...]
 *  1: Lista de puntos fijos [p1, p2, ...]
 *  2: Conteo total de pares de simetria (int)
 *  3: Mensaje 'svg_exported <path>'
 */

inlets = 2;
outlets = 4;

if (typeof setinletassist === 'function') {
    setinletassist(0, "Suma de indices S (int) / mensajes / bang");
    setinletassist(1, "Divisiones n-TET (int 3..72)");
    setoutletassist(0, "Pares de inversion aplanados [i, partner, ...]");
    setoutletassist(1, "Puntos fijos [f1, f2, ...]");
    setoutletassist(2, "Cantidad de pares de simetria (int)");
    setoutletassist(3, "Notificacion de exportacion SVG");
}

// Inicialización del motor gráfico vectorial de Max MSP
if (typeof mgraphics !== 'undefined') {
    mgraphics.init();
    mgraphics.relative_coords = 0;
    mgraphics.autofill = 0;
}

// Variables de estado
var divisions = 19;
var indexSum = 0;
var showInversion = true;
var isDark = true;

/**
 * Operación módulo matemática que maneja números negativos: ((n % m) + m) % m
 */
function mod(n, m) {
    return ((n % m) + m) % m;
}

/**
 * Escala tipográfica adaptativa según divisiones
 */
function calculateFontSize(divs) {
    if (divs <= 20) return 12;
    if (divs <= 30) return 10;
    if (divs <= 40) return 8;
    if (divs <= 50) return 7;
    return 6;
}

/**
 * Calcula pares de inversión y puntos fijos
 */
function getInversionPairs(divs, sum) {
    var pairs = [];
    var fixedPoints = [];
    var visited = {};

    for (var i = 0; i < divs; i++) {
        if (visited[i]) continue;

        var partner = mod(sum - i, divs);

        if (partner === i) {
            fixedPoints.push(i);
            visited[i] = true;
        } else if (!visited[partner]) {
            pairs.push([i, partner]);
            visited[i] = true;
            visited[partner] = true;
        }
    }

    return { pairs: pairs, fixedPoints: fixedPoints };
}

/**
 * Calcula el punto de control de curvatura Bézier
 */
function calculateCurvature(i, partner, divs, circleRadius) {
    var angleStep = (2 * Math.PI) / divs;
    var angle1 = -Math.PI / 2 + (i * angleStep);
    var angle2 = -Math.PI / 2 + (partner * angleStep);

    var angularDist = Math.abs(partner - i);
    if (angularDist > divs / 2) {
        angularDist = divs - angularDist;
    }

    var normalizedDist = angularDist / (divs / 2);
    var curvatureFactor = (1 - normalizedDist) * 0.6;

    var diff = ((angle2 - angle1 + Math.PI) % (2 * Math.PI)) - Math.PI;
    if (diff < -Math.PI) diff += 2 * Math.PI;
    var midAngle = angle1 + diff / 2;

    var controlRadius = circleRadius * curvatureFactor;

    return {
        cx: controlRadius * Math.cos(midAngle),
        cy: controlRadius * Math.sin(midAngle)
    };
}

/**
 * Emite los datos de simetría por los outlets
 */
function bang() {
    var res = getInversionPairs(divisions, indexSum);
    var flattened = [];
    for (var p = 0; p < res.pairs.length; p++) {
        flattened.push(res.pairs[p][0]);
        flattened.push(res.pairs[p][1]);
    }

    if (typeof outlet !== 'undefined') {
        outlet(2, res.pairs.length);
        outlet(1, res.fixedPoints);
        outlet(0, flattened);
    }

    if (typeof mgraphics !== 'undefined') {
        mgraphics.redraw();
    }

    return {
        pairs: res.pairs,
        fixedPoints: res.fixedPoints,
        flattened: flattened,
        pairCount: res.pairs.length
    };
}

/**
 * Renderizado vectorial nativo con mgraphics sobre el lienzo del patcher
 */
function paint() {
    if (typeof mgraphics === 'undefined') return;

    var viewsize = mgraphics.size;
    var width = viewsize[0];
    var height = viewsize[1];
    var centerX = width / 2;
    var centerY = height / 2;
    var minDim = Math.min(width, height);
    var circleRadius = minDim * 0.36;
    var innerRadius = circleRadius * 0.85;
    var tickRadius = circleRadius * 0.92;
    var numbersRadius = circleRadius * 1.15;
    var angleStep = (2 * Math.PI) / divisions;

    // 1. Fondo sólido estilizado
    if (isDark) {
        mgraphics.set_source_rgba(0.12, 0.12, 0.14, 1.0);
    } else {
        mgraphics.set_source_rgba(0.98, 0.98, 0.98, 1.0);
    }
    mgraphics.rectangle(0, 0, width, height);
    mgraphics.fill();

    // Marco sutil
    mgraphics.set_source_rgba(0.85, 0.45, 0.15, 0.4);
    mgraphics.set_line_width(1.5);
    mgraphics.rectangle(1, 1, width - 2, height - 2);
    mgraphics.stroke();

    // 2. Círculo principal y círculo punteado interno
    if (isDark) {
        mgraphics.set_source_rgba(0.95, 0.95, 0.98, 0.9);
    } else {
        mgraphics.set_source_rgba(0.1, 0.1, 0.15, 0.9);
    }
    mgraphics.set_line_width(2.0);
    mgraphics.arc(centerX, centerY, circleRadius, 0, 2 * Math.PI);
    mgraphics.stroke();

    // Círculo interno
    mgraphics.set_source_rgba(0.95, 0.95, 0.98, 0.25);
    mgraphics.set_line_width(1.0);
    mgraphics.arc(centerX, centerY, innerRadius, 0, 2 * Math.PI);
    mgraphics.stroke();

    // 3. Ticks radiales y números de cada nota
    var fontSize = Math.max(8, calculateFontSize(divisions) * (minDim / 400.0));
    mgraphics.select_font_face("Segoe UI", "normal", "bold");
    mgraphics.set_font_size(fontSize);

    for (var i = 0; i < divisions; i++) {
        var angle = -Math.PI / 2 + (i * angleStep);
        var cosA = Math.cos(angle);
        var sinA = Math.sin(angle);

        // Tick radial
        var x1 = centerX + tickRadius * cosA;
        var y1 = centerY + tickRadius * sinA;
        var x2 = centerX + circleRadius * cosA;
        var y2 = centerY + circleRadius * sinA;

        mgraphics.set_source_rgba(0.95, 0.95, 0.98, 0.5);
        mgraphics.set_line_width(1.2);
        mgraphics.move_to(x1, y1);
        mgraphics.line_to(x2, y2);
        mgraphics.stroke();

        // Número de nota
        var tx = centerX + numbersRadius * cosA;
        var ty = centerY + numbersRadius * sinA;
        var numStr = i.toString();
        var extents = mgraphics.text_measure(numStr);

        if (isDark) {
            mgraphics.set_source_rgba(0.96, 0.96, 0.98, 1.0);
        } else {
            mgraphics.set_source_rgba(0.1, 0.1, 0.15, 1.0);
        }
        mgraphics.move_to(tx - extents[0] / 2, ty + extents[1] / 3);
        mgraphics.text_path(numStr);
        mgraphics.fill();
    }

    // 4. Mapeo de Inversión: Curvas Bézier y Puntos Fijos
    if (showInversion) {
        var invData = getInversionPairs(divisions, indexSum);

        // Curvas Bézier para parejas simétricas
        mgraphics.set_source_rgba(0.23, 0.51, 0.96, 0.85); // Azul #3b82f6
        mgraphics.set_line_width(2.2);

        for (var p = 0; p < invData.pairs.length; p++) {
            var i1 = invData.pairs[p][0];
            var i2 = invData.pairs[p][1];

            var a1 = -Math.PI / 2 + (i1 * angleStep);
            var a2 = -Math.PI / 2 + (i2 * angleStep);

            var startX = centerX + circleRadius * Math.cos(a1);
            var startY = centerY + circleRadius * Math.sin(a1);
            var endX = centerX + circleRadius * Math.cos(a2);
            var endY = centerY + circleRadius * Math.sin(a2);

            var curv = calculateCurvature(i1, i2, divisions, circleRadius);
            var ctrlX = centerX + curv.cx;
            var ctrlY = centerY + curv.cy;

            // En mgraphics, curve_to usa coordenadas de Bézier cúbica.
            // Para aproximar una cuadrática con control C:
            // CP1 = Start + (2/3)*(C - Start), CP2 = End + (2/3)*(C - End)
            var cp1x = startX + (2.0 / 3.0) * (ctrlX - startX);
            var cp1y = startY + (2.0 / 3.0) * (ctrlY - startY);
            var cp2x = endX + (2.0 / 3.0) * (ctrlX - endX);
            var cp2y = endY + (2.0 / 3.0) * (ctrlY - endY);

            mgraphics.move_to(startX, startY);
            mgraphics.curve_to(cp1x, cp1y, cp2x, cp2y, endX, endY);
            mgraphics.stroke();
        }

        // Puntos Fijos (Ejes de simetría) marcados en rojo (#ef4444)
        for (var f = 0; f < invData.fixedPoints.length; f++) {
            var fNote = invData.fixedPoints[f];
            var fAngle = -Math.PI / 2 + (fNote * angleStep);
            var fx = centerX + circleRadius * Math.cos(fAngle);
            var fy = centerY + circleRadius * Math.sin(fAngle);

            // Círculo rojo exterior
            mgraphics.set_source_rgba(0.93, 0.27, 0.27, 1.0);
            mgraphics.arc(fx, fy, 6.0, 0, 2 * Math.PI);
            mgraphics.fill();

            // Borde blanco de contraste
            mgraphics.set_source_rgba(1.0, 1.0, 1.0, 0.9);
            mgraphics.set_line_width(1.5);
            mgraphics.arc(fx, fy, 6.0, 0, 2 * Math.PI);
            mgraphics.stroke();
        }
    }

    // 5. Título y estado en el pie del objeto
    mgraphics.select_font_face("Segoe UI", "normal", "bold");
    mgraphics.set_font_size(11);
    mgraphics.set_source_rgba(0.85, 0.45, 0.15, 1.0); // Acento naranja
    var infoText = divisions + "-TET | Suma S: " + indexSum + " | Pares: " + Math.floor((divisions - (divisions % 2 === 0 ? (indexSum % 2 === 0 ? 2 : 0) : 1)) / 2);
    mgraphics.move_to(12, 22);
    mgraphics.text_path(infoText);
    mgraphics.fill();
}

/**
 * Interacción de ratón en el lienzo del patcher: click para cambiar suma de índices
 */
function onclick(x, y) {
    if (typeof mgraphics === 'undefined') return;
    var viewsize = mgraphics.size;
    var centerX = viewsize[0] / 2;
    var centerY = viewsize[1] / 2;
    var dx = x - centerX;
    var dy = y - centerY;

    // Calcular ángulo del click
    var angle = Math.atan2(dy, dx) + Math.PI / 2;
    if (angle < 0) angle += 2 * Math.PI;

    var noteClicked = Math.round((angle / (2 * Math.PI)) * divisions) % divisions;
    indexSum = noteClicked;
    bang();
}

function ondrag(x, y, button) {
    if (button) {
        onclick(x, y);
    }
}

/**
 * Exportador vectorial SVG a disco nativo sin dependencias
 */
function export_svg(filePath) {
    if (!filePath) {
        filePath = "D:/DocumentosDiscoD/OptimizandoParaMaxSDK/benchmarks/generadorTETAnalisisCirculos/" + divisions + "-TET-inversion-" + indexSum + ".svg";
    }

    var inv = getInversionPairs(divisions, indexSum);
    var width = 540;
    var height = 540;
    var centerX = width / 2;
    var centerY = height / 2;
    var circleRadius = 160;
    var angleStep = (2 * Math.PI) / divisions;

    var svg = [];
    svg.push('<?xml version="1.0" encoding="UTF-8"?>');
    svg.push('<svg xmlns="http://www.w3.org/2000/svg" width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '">');
    svg.push('<rect width="100%" height="100%" fill="#1e1e1e" rx="12"/>');
    svg.push('<text x="' + centerX + '" y="35" font-family="Segoe UI" font-size="16" font-weight="bold" text-anchor="middle" fill="#fcfaff">' + divisions + '-TET Inversión (Suma ' + indexSum + ')</text>');
    svg.push('<g transform="translate(' + centerX + ',' + centerY + ')">');
    svg.push('<circle cx="0" cy="0" r="' + circleRadius + '" fill="none" stroke="#fcfaff" stroke-width="2"/>');

    // Arcos Bézier
    for (var p = 0; p < inv.pairs.length; p++) {
        var i1 = inv.pairs[p][0];
        var i2 = inv.pairs[p][1];
        var a1 = -Math.PI / 2 + i1 * angleStep;
        var a2 = -Math.PI / 2 + i2 * angleStep;
        var x1 = (circleRadius * Math.cos(a1)).toFixed(2);
        var y1 = (circleRadius * Math.sin(a1)).toFixed(2);
        var x2 = (circleRadius * Math.cos(a2)).toFixed(2);
        var y2 = (circleRadius * Math.sin(a2)).toFixed(2);
        var curv = calculateCurvature(i1, i2, divisions, circleRadius);
        svg.push('<path d="M ' + x1 + ',' + y1 + ' Q ' + curv.cx.toFixed(2) + ',' + curv.cy.toFixed(2) + ' ' + x2 + ',' + y2 + '" fill="none" stroke="#3b82f6" stroke-width="2.2" opacity="0.85"/>');
    }

    // Puntos fijos
    for (var f = 0; f < inv.fixedPoints.length; f++) {
        var fn = inv.fixedPoints[f];
        var fa = -Math.PI / 2 + fn * angleStep;
        var fx = (circleRadius * Math.cos(fa)).toFixed(2);
        var fy = (circleRadius * Math.sin(fa)).toFixed(2);
        svg.push('<circle cx="' + fx + '" cy="' + fy + '" r="5.5" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>');
    }

    svg.push('</g>');
    svg.push('</svg>');

    if (typeof File !== 'undefined') {
        var file = new File(filePath, "write", "TEXT");
        if (file.isopen) {
            file.writestring(svg.join("\n"));
            file.close();
            if (typeof post !== 'undefined') {
                post("SVG exportado exitosamente en: " + filePath + "\n");
            }
        }
    }

    if (typeof outlet !== 'undefined') {
        outlet(3, "svg_exported", filePath);
    }
    return filePath;
}

/**
 * Handlers de mensajes de Max MSP
 */
function msg_int(val) {
    if (typeof inlet === 'undefined') return;
    if (inlet === 0) {
        indexSum = Math.max(0, Math.min(val, divisions - 1));
        bang();
    } else if (inlet === 1) {
        divisions = Math.max(3, Math.min(val, 72));
        indexSum = Math.min(indexSum, divisions - 1);
        bang();
    }
}

function set_divisions(val) {
    divisions = Math.max(3, Math.min(val, 72));
    indexSum = Math.min(indexSum, divisions - 1);
    bang();
}

function set_sum(val) {
    indexSum = Math.max(0, Math.min(val, divisions - 1));
    bang();
}

function toggle_inversion() {
    showInversion = !showInversion;
    bang();
}

// Exportación para pruebas Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        mod: mod,
        calculateFontSize: calculateFontSize,
        getInversionPairs: getInversionPairs,
        calculateCurvature: calculateCurvature,
        export_svg: export_svg,
        bang: bang,
        setState: function(s) {
            if (s.divisions !== undefined) divisions = s.divisions;
            if (s.indexSum !== undefined) indexSum = s.indexSum;
        }
    };
}
