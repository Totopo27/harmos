/**
 * tet_inversion.js
 * Objeto nativo de Max MSP para análisis geométrico de simetrías,
 * partición de pares de inversión y detección de puntos fijos en sistemas n-TET (3 a 72 TET).
 *
 * Inlets:
 *  0: Suma de índices (indexSum) / 'bang' para recalcular
 *  1: Divisiones n-TET (3 a 72)
 *
 * Outlets:
 *  0: Lista aplanada de pares de inversión [i1, partner1, i2, partner2, ...]
 *  1: Lista de puntos fijos [p1, p2, ...]
 *  2: Conteo total de pares de simetría (int)
 */

// Configuración de inlets y outlets para Max MSP
inlets = 2;
outlets = 3;

if (typeof setinletassist === 'function') {
    setinletassist(0, "Suma de indices S (int) / bang");
    setinletassist(1, "Divisiones n-TET (int 3..72)");
    setoutletassist(0, "Pares de inversion aplanados [i, partner, ...]");
    setoutletassist(1, "Puntos fijos [f1, f2, ...]");
    setoutletassist(2, "Cantidad de pares de simetria (int)");
}

// Variables de estado
var divisions = 19;
var indexSum = 0;

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
 * Calcula pares de inversión y puntos fijos para una suma de índices dada
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
 * Calcula el punto de control de curvatura Bézier para un radio dado
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
 * Ejecuta el cálculo y emite por los outlets de Max
 */
function bang() {
    var res = getInversionPairs(divisions, indexSum);
    var flattenedPairs = [];
    for (var p = 0; p < res.pairs.length; p++) {
        flattenedPairs.push(res.pairs[p][0]);
        flattenedPairs.push(res.pairs[p][1]);
    }

    if (typeof outlet !== 'undefined') {
        outlet(2, res.pairs.length);
        outlet(1, res.fixedPoints);
        outlet(0, flattenedPairs);
    }

    return {
        pairs: res.pairs,
        fixedPoints: res.fixedPoints,
        flattenedPairs: flattenedPairs,
        pairCount: res.pairs.length
    };
}

/**
 * Handlers de mensajes para Max MSP
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

// Exportación para pruebas unitarias en Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        mod: mod,
        calculateFontSize: calculateFontSize,
        getInversionPairs: getInversionPairs,
        calculateCurvature: calculateCurvature,
        bang: bang,
        setState: function(state) {
            if (state.divisions !== undefined) divisions = state.divisions;
            if (state.indexSum !== undefined) indexSum = state.indexSum;
        }
    };
}
