const test = require('node:test');
const assert = require('node:assert/strict');
const tetInversion = require('../tet_inversion.js');

test('Paridad mod: aritmetica modular matematica precisa', () => {
    assert.equal(tetInversion.mod(7, 12), 7);
    assert.equal(tetInversion.mod(12, 12), 0);
    assert.equal(tetInversion.mod(13, 12), 1);
    assert.equal(tetInversion.mod(-1, 12), 11);
    assert.equal(tetInversion.mod(-12, 12), 0);
    assert.equal(tetInversion.mod(-13, 12), 11);
    assert.equal(tetInversion.mod(-25, 12), 11);
});

test('Paridad getInversionPairs: particion exacta y puntos fijos en 12-TET', () => {
    // En 12-TET con suma par (0): 2 puntos fijos (0 y 6) y 5 pares
    const resEven = tetInversion.getInversionPairs(12, 0);
    assert.equal(resEven.fixedPoints.length, 2);
    assert.deepEqual(resEven.fixedPoints, [0, 6]);
    assert.equal(resEven.pairs.length, 5);
    const allNotesEven = new Set([...resEven.fixedPoints, ...resEven.pairs.flat()]);
    assert.equal(allNotesEven.size, 12);

    // En 12-TET con suma impar (1): 0 puntos fijos y 6 pares
    const resOdd = tetInversion.getInversionPairs(12, 1);
    assert.equal(resOdd.fixedPoints.length, 0);
    assert.equal(resOdd.pairs.length, 6);
    const allNotesOdd = new Set(resOdd.pairs.flat());
    assert.equal(allNotesOdd.size, 12);
});

test('Paridad getInversionPairs: particion exacta en temperamentos impares (19-TET)', () => {
    for (let sum = 0; sum < 19; sum++) {
        const res = tetInversion.getInversionPairs(19, sum);
        assert.equal(res.fixedPoints.length, 1, `Fallo en suma ${sum}: debe haber 1 punto fijo`);
        assert.equal(res.pairs.length, 9, `Fallo en suma ${sum}: debe haber 9 pares`);
        const allNotes = new Set([...res.fixedPoints, ...res.pairs.flat()]);
        assert.equal(allNotes.size, 19, `Fallo en suma ${sum}: no cubre las 19 notas`);
    }
});

test('Paridad calculateCurvature: curvatura Bezier finita y centro en antipodas', () => {
    const radius = 160;
    const antipodal = tetInversion.calculateCurvature(0, 6, 12, radius);
    assert.ok(Math.abs(antipodal.cx) < 1e-4);
    assert.ok(Math.abs(antipodal.cy) < 1e-4);

    const adjacent = tetInversion.calculateCurvature(0, 1, 12, radius);
    assert.ok(!isNaN(adjacent.cx));
    assert.ok(!isNaN(adjacent.cy));
    const distFromCenter = Math.sqrt(adjacent.cx ** 2 + adjacent.cy ** 2);
    assert.ok(distFromCenter > 0);
    assert.ok(distFromCenter < radius);
});

test('Paridad calculateFontSize: escala tipografica adaptativa', () => {
    assert.equal(tetInversion.calculateFontSize(12), 12);
    assert.equal(tetInversion.calculateFontSize(19), 12);
    assert.equal(tetInversion.calculateFontSize(25), 10);
    assert.equal(tetInversion.calculateFontSize(31), 8);
    assert.equal(tetInversion.calculateFontSize(41), 7);
    assert.equal(tetInversion.calculateFontSize(53), 6);
    assert.equal(tetInversion.calculateFontSize(72), 6);
});

test('Ejecucion integrada de bang() en tet_inversion (sin audio)', () => {
    tetInversion.setState({
        divisions: 19,
        indexSum: 4
    });
    const result = tetInversion.bang();
    assert.equal(result.fixedPoints.length, 1);
    assert.equal(result.pairs.length, 9);
    assert.equal(result.flattenedPairs.length, 18);
    assert.equal(result.pairCount, 9);
});
