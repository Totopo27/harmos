"""
Harmos Microtonal Engine: Traducción del Dominio Microtonal y Forma Normal de Barry Truax para Max MSP.
Genera tablas de afinación de 384 posiciones (3 canales MIDI) compatibles con coll/buffer~
y scripts JavaScript optimizados para el objeto [js] de Max.
"""
import math
from typing import Dict, List, Tuple


class MicrotonalEngine:
    """
    Motor matemático para cálculo de afinaciones microtonales y compensación
    de fundamental mediante Forma Normal (Barry Truax).
    """

    def to_normal_form(self, c: float, m: float) -> Tuple[float, float]:
        """
        Forma Normal de Barry Truax:
        Para un ratio C:M, verifica si el Carrier es la fundamental percibida (M >= 2C o 1:1).
        Si no está en Forma Normal, aplica reducciones sucesivas: C = |C - M| hasta alcanzarla.
        """
        cur_c = max(abs(float(c)), 0.001)
        cur_m = max(abs(float(m)), 0.001)
        iterations = 0

        while (cur_c != cur_m) and (cur_m < (2.0 * cur_c)) and (iterations < 20):
            cur_c = abs(cur_c - cur_m)
            iterations += 1

        return (cur_c, cur_m)

    def calc_carrier_freq(self, f_fundamental: float, c: float, m: float) -> float:
        """
        Calcula la frecuencia del carrier necesaria para que la nota fundamental
        escuchada coincida exactamente con la afinación microtonal requerida.
        Fórmula de Truax: fCarrier = (fFundamental * C) / normalC
        """
        normal_c, _ = self.to_normal_form(c, m)
        return (float(f_fundamental) * float(c)) / normal_c

    # ------------------------------------------------------------------
    # Generadores de Escalas Microtonales (384 posiciones = 3 canales MIDI)
    # ------------------------------------------------------------------

    def build_tet(self, divisions: int, ref_freq: float = 440.0, ref_note: int = 69, total: int = 384) -> List[float]:
        step_ratio = 2.0 ** (1.0 / divisions)
        return [ref_freq * (step_ratio ** (i - ref_note)) for i in range(total)]

    def build_meantone31(self, ref_freq: float = 440.0, total: int = 384) -> List[float]:
        mean31 = [0.0] * 31
        q_meantone = (3.0 / 2.0) / ((81.0 / 80.0) ** (1.0 / 4.0))

        mean31[23] = 1.0
        for k in range(1, 16):
            prev_pc = (23 + (k - 1) * 18) % 31
            curr_pc = (23 + k * 18) % 31
            ratio = mean31[prev_pc] * q_meantone
            while ratio >= 2.0:
                ratio /= 2.0
            mean31[curr_pc] = ratio

        for k in range(1, 16):
            prev_pc = (23 + (k - 1) * 13) % 31
            curr_pc = (23 + k * 13) % 31
            ratio = mean31[prev_pc] * (2.0 / q_meantone)
            while ratio >= 2.0:
                ratio /= 2.0
            mean31[curr_pc] = ratio

        offset = mean31[0]
        for i in range(31):
            nr = mean31[i] / offset
            if nr < 1.0:
                nr *= 2.0
            mean31[i] = nr

        f0 = ref_freq / (mean31[23] * (2.0 ** 4))
        result = []
        for i in range(total):
            virtual_index = i + 23
            pc = virtual_index % 31
            octave = virtual_index // 31
            result.append(f0 * mean31[pc] * (2.0 ** octave))
        return result

    def build_magic41(self, ref_freq: float = 440.0, total: int = 384) -> List[float]:
        generator = 3.0 ** (1.0 / 5.0)
        step_ratio = generator ** (1.0 / 13.0)
        return [ref_freq * (step_ratio ** (i - 164)) for i in range(total)]

    def build_partch43(self, f0: float = 24.5, total: int = 384) -> List[float]:
        ratios = [
            1.0 / 1.0, 81.0 / 80.0, 33.0 / 32.0, 21.0 / 20.0, 16.0 / 15.0, 12.0 / 11.0, 11.0 / 10.0, 10.0 / 9.0, 9.0 / 8.0, 8.0 / 7.0,
            7.0 / 6.0, 32.0 / 27.0, 6.0 / 5.0, 11.0 / 9.0, 5.0 / 4.0, 14.0 / 11.0, 9.0 / 7.0, 21.0 / 16.0, 4.0 / 3.0, 27.0 / 20.0,
            11.0 / 8.0, 7.0 / 5.0, 10.0 / 7.0, 16.0 / 11.0, 40.0 / 27.0, 3.0 / 2.0, 32.0 / 21.0, 14.0 / 9.0, 11.0 / 7.0, 8.0 / 5.0,
            18.0 / 11.0, 5.0 / 3.0, 27.0 / 16.0, 12.0 / 7.0, 7.0 / 4.0, 16.0 / 9.0, 9.0 / 5.0, 20.0 / 11.0, 11.0 / 6.0, 15.0 / 8.0,
            40.0 / 21.0, 64.0 / 33.0, 160.0 / 81.0
        ]
        result = []
        for i in range(total):
            ratio_idx = i % 43
            octave = i // 43
            result.append(f0 * ratios[ratio_idx] * (2.0 ** octave))
        return result

    def build_centaur(self, ref_freq: float = 440.0, ref_midi: int = 69, total: int = 384) -> List[float]:
        ratios = [1.0 / 1.0, 21.0 / 20.0, 9.0 / 8.0, 7.0 / 6.0, 5.0 / 4.0, 4.0 / 3.0, 7.0 / 5.0, 3.0 / 2.0, 14.0 / 9.0, 5.0 / 3.0, 7.0 / 4.0, 15.0 / 8.0]
        ref_degree = ref_midi % 12
        ref_octave = ref_midi // 12
        f0 = ref_freq / ratios[ref_degree] / (2.0 ** ref_octave)
        result = []
        for i in range(total):
            idx = i % 12
            octave = i // 12
            result.append(f0 * ratios[idx] * (2.0 ** octave))
        return result

    def generate_all_scales(self) -> Dict[str, List[float]]:
        return {
            "tet12": self.build_tet(12, ref_note=69),
            "tet31": self.build_tet(31, ref_note=124),
            "tet41": self.build_tet(41, ref_note=164),
            "tet53": self.build_tet(53, ref_note=212),
            "meantone31": self.build_meantone31(),
            "magic41": self.build_magic41(),
            "partch": self.build_partch43(),
            "centaur": self.build_centaur(),
        }

    def export_as_coll(self, scale_key: str) -> str:
        """Exporta la escala en formato de archivo de texto compatible con el objeto coll de Max."""
        scales = self.generate_all_scales()
        scale = scales.get(scale_key, scales["tet12"])
        lines = [f"{i}, {freq:.6f};" for i, freq in enumerate(scale)]
        return "\n".join(lines) + "\n"

    def generate_truax_js(self) -> str:
        """
        Genera el script JS para Max MSP que calcula la Forma Normal de Truax
        y la frecuencia del Carrier en tiempo real dentro del parche.
        """
        return """/*
 * truax.js - Barry Truax Normal Form (N.F.) Calculator for Max MSP
 * Generated automatically by Harmos Meta-Compiler Framework
 */
inlets = 3;  // inlet 0: fundamental_freq, inlet 1: C, inlet 2: M
outlets = 2; // outlet 0: fCarrier, outlet 1: normalForm [C, M]

var fFund = 220.0;
var carrierRatio = 1.0;
var modRatio = 1.0;

function msg_float(val) {
    if (inlet == 0) {
        fFund = val;
        calc();
    } else if (inlet == 1) {
        carrierRatio = val;
        calc();
    } else if (inlet == 2) {
        modRatio = val;
        calc();
    }
}

function msg_int(val) {
    msg_float(val);
}

function list() {
    var a = arrayfromargs(arguments);
    if (a.length >= 3) {
        fFund = a[0];
        carrierRatio = a[1];
        modRatio = a[2];
        calc();
    }
}

function toNormalForm(c, m) {
    var curC = Math.max(Math.abs(c), 0.001);
    var curM = Math.max(Math.abs(m), 0.001);
    var iter = 0;

    while ((curC != curM) && (curM < (2.0 * curC)) && (iter < 20)) {
        curC = Math.abs(curC - curM);
        iter++;
    }
    return [curC, curM];
}

function calcCarrierFreq(f, c, m) {
    var nf = toNormalForm(c, m);
    return (f * c) / nf[0];
}

function calc() {
    var nf = toNormalForm(carrierRatio, modRatio);
    var fCarrier = (fFund * carrierRatio) / nf[0];

    outlet(1, nf);
    outlet(0, fCarrier);
}
"""
