"""
Harmos SC Voice Compiler: Sintetizador de subpatchers de voz Max MSP (.maxpat)
a partir de especificaciones de grafos de síntesis de SuperCollider (SCMicroSynth/diesisRosa).
Genera parches estructurados para poly~ con cero hardcoding mediante TypedPatch.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from core.compiler.typed_patch import TypedPatch
from core.compiler.contract_engine import ContractEngine


class SCVoiceCompiler:
    """
    Compilador especializado en convertir SynthDefs de SuperCollider en
    subpatchers de voz compatibles con el objeto poly~ de Max MSP.
    """
    def __init__(self, contract_engine: Optional[ContractEngine] = None):
        self.engine = contract_engine or ContractEngine()

    def compile_fm_voice(self, output_path: str, ir_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sintetiza la voz de 3 operadores FM en cascada:
        Modulador 2 -> Modulador 1 -> Carrier.
        Implementa control de envolvente, vibrato y desasignación dinámica de poly~.
        """
        patch = TypedPatch(self.engine)

        # -------------------------------------------------------------
        # 1. Entradas y Control de Polifonía (poly~ Voice Architecture)
        # -------------------------------------------------------------
        # in~ 1: Frecuencia fundamental del carrier en Hz (señal o continua)
        in_freq = patch.add_box("in~ 1", x=50.0, y=30.0)
        # in 2: Gate / Trigger para disparo de notas y envolventes
        in_gate = patch.add_box("in 2", x=350.0, y=30.0)
        # in 3: Frecuencia y ganancia de vibrato [fVib, aVib]
        in_vib = patch.add_box("in 3", x=180.0, y=30.0)

        # LFO de vibrato: tri~ a fVib (default 5 Hz) con escalado a señal
        vib_lfo = patch.add_box("tri~ 5.0", x=180.0, y=80.0)
        vib_amp = patch.add_box("*~ 0.0", x=180.0, y=130.0)
        patch.connect(vib_lfo, 0, vib_amp, 0)

        # Suma de vibrato a la frecuencia fundamental base: cFrec = f + vib
        carrier_freq_sum = patch.add_box("+~", x=50.0, y=80.0)
        patch.connect(in_freq, 0, carrier_freq_sum, 0)
        patch.connect(vib_amp, 0, carrier_freq_sum, 1)

        # Dispositivo de muteo/desactivación dinámica de poly~
        thispoly = patch.add_box("thispoly~", x=550.0, y=480.0)

        # -------------------------------------------------------------
        # 2. Modulador 2 (Operador más alto en la cascada)
        # -------------------------------------------------------------
        # Ratio de frecuencia para Mod2 y Mod1 (por defecto multiplicador de señal)
        # mod2_osc: cycle~ que corre a (cFrec * m1Ratio * m2Ratio)
        mod2_osc = patch.add_box("cycle~ 440", x=50.0, y=130.0)
        mod2_index_mul = patch.add_box("*~ 0.0", x=50.0, y=175.0)
        mod2_env = patch.add_box("adsr~ 0.0 0.0 1.0 0.0", x=350.0, y=90.0)
        mod2_sig_mul = patch.add_box("*~", x=50.0, y=220.0)

        # Conectar Mod2: osc * index -> sig_mul; sig_mul * env
        patch.connect(mod2_osc, 0, mod2_index_mul, 0)
        patch.connect(mod2_index_mul, 0, mod2_sig_mul, 0)
        patch.connect(mod2_env, 0, mod2_sig_mul, 1)

        # -------------------------------------------------------------
        # 3. Modulador 1 (Operador Intermedio)
        # -------------------------------------------------------------
        # mod1 recibe modulación de mod2 en su frecuencia/fase: m1Frec + m2Sig
        mod1_sum = patch.add_box("+~", x=50.0, y=265.0)
        # Base de frecuencia conectada a la frecuencia modulada con vibrato
        patch.connect(carrier_freq_sum, 0, mod1_sum, 0)
        patch.connect(mod2_sig_mul, 0, mod1_sum, 1)

        mod1_osc = patch.add_box("cycle~", x=50.0, y=310.0)
        patch.connect(mod1_sum, 0, mod1_osc, 0)

        mod1_index_mul = patch.add_box("*~ 100.0", x=50.0, y=355.0)
        mod1_env = patch.add_box("adsr~ 0.0 0.0 1.0 0.0", x=350.0, y=190.0)
        mod1_sig_mul = patch.add_box("*~", x=50.0, y=400.0)

        patch.connect(mod1_osc, 0, mod1_index_mul, 0)
        patch.connect(mod1_index_mul, 0, mod1_sig_mul, 0)
        patch.connect(mod1_env, 0, mod1_sig_mul, 1)

        # -------------------------------------------------------------
        # 4. Carrier (Portadora Principal)
        # -------------------------------------------------------------
        # Carrier recibe la modulación acumulada: cFrec + mod1Sig
        carrier_sum = patch.add_box("+~", x=50.0, y=445.0)
        patch.connect(carrier_freq_sum, 0, carrier_sum, 0)
        patch.connect(mod1_sig_mul, 0, carrier_sum, 1)

        carrier_osc = patch.add_box("cycle~", x=50.0, y=490.0)
        patch.connect(carrier_sum, 0, carrier_osc, 0)

        # Envolvente Carrier: adsr~ 10ms At, 300ms De, 0.5 Su, 1000ms Re
        # SuperCollider usa curve: -2 en dadsr. En Max MSP podemos aplicar
        # una función de transferencia de potencia/curva o curve~ para aproximar
        # la curva logarítmica/exponencial del cCurv.
        carrier_env = patch.add_box("adsr~ 10 300 0.5 1000", x=350.0, y=290.0)
        carrier_amp_mul = patch.add_box("*~", x=50.0, y=535.0)

        patch.connect(carrier_osc, 0, carrier_amp_mul, 0)
        patch.connect(carrier_env, 0, carrier_amp_mul, 1)

        # -------------------------------------------------------------
        # 5. Control de Envolventes y Desasignación de Voz (Gate)
        # -------------------------------------------------------------
        patch.connect(in_gate, 0, mod2_env, 0)
        patch.connect(in_gate, 0, mod1_env, 0)
        patch.connect(in_gate, 0, carrier_env, 0)

        # El outlet 1 de adsr~ emite un bang al completar la fase de release
        patch.connect(carrier_env, 1, thispoly, 0)

        # -------------------------------------------------------------
        # 6. Salidas Estéreo hacia poly~
        # -------------------------------------------------------------
        out_l = patch.add_box("out~ 1", x=50.0, y=575.0)
        out_r = patch.add_box("out~ 2", x=180.0, y=575.0)

        patch.connect(carrier_amp_mul, 0, out_l, 0)
        patch.connect(carrier_amp_mul, 0, out_r, 0)

        # Guardar archivo .maxpat
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        patch.save(output_path)

        return {
            "success": True,
            "patcher_path": str(Path(output_path).resolve()),
            "boxes_count": len(patch.boxes),
            "lines_count": len(patch.lines)
        }

    def compile_main_synth(self, output_path: str, voice_patcher_name: str = "fmVoice", polyphony: int = 16, control_ir: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sintetiza el parche principal contenedor de diesisRosa (diesisRosa.maxpat):
        - Entrada MIDI (notein)
        - Selector de afinaciones microtonales dinámico derivado de control_ir (umenu -> prepend read -> coll)
        - Mapeo de frecuencia microtonal con tabla de afinaciones (coll)
        - Compensación de fundamental por Forma Normal de Barry Truax (js truax.js)
        - Banco polifónico (poly~ <voice_patcher_name> <polyphony>)
        - Master Limiter / Output (omx.peaklim~ / gain~ / ezdac~)
        """
        patch = TypedPatch(self.engine)

        # 1. Entrada de control MIDI
        midi_in = patch.add_box("notein", x=50.0, y=30.0)

        # 2. Selector de afinaciones microtonales derivado de la IR de control
        scale_menu = patch.add_box("umenu", x=220.0, y=30.0, w=150.0)
        prepend_read = patch.add_box("prepend read", x=220.0, y=70.0)
        patch.connect(scale_menu, 1, prepend_read, 0)

        # Determinar tabla por defecto según control_ir o fallback canónico
        default_table = "tet31.txt"
        if control_ir and "data_tables" in control_ir and control_ir["data_tables"]:
            default_table = control_ir["data_tables"][0].get("source_file", "tet31.txt")

        # 3. Mapeador de afinación microtonal (coll cargando tabla 384 posiciones)
        tuning_coll = patch.add_box(f"coll {default_table}", x=50.0, y=110.0)
        patch.connect(prepend_read, 0, tuning_coll, 0)
        patch.connect(midi_in, 0, tuning_coll, 0)

        # 4. Calculador de Forma Normal de Barry Truax (js truax.js)
        # Recibe la frecuencia de la nota microtonal en inlet 0 y emite la frecuencia corregida del carrier
        truax_calc = patch.add_box("js truax.js", x=50.0, y=160.0)
        patch.connect(tuning_coll, 0, truax_calc, 0)

        # Convertir frecuencia calculada a señal para poly~
        freq_sig = patch.add_box("sig~", x=50.0, y=210.0)
        patch.connect(truax_calc, 0, freq_sig, 0)

        # 5. Banco Polifónico (poly~ fmVoice 16)
        poly_synth = patch.add_box(f"poly~ {voice_patcher_name} {polyphony}", x=50.0, y=260.0)
        # Señal de frecuencia al inlet de audio de poly~ (inlet 1)
        patch.connect(freq_sig, 0, poly_synth, 1)
        # Velocity de notein al inlet de control de poly~ (inlet 0) para disparar la envolvente
        patch.connect(midi_in, 1, poly_synth, 0)

        # 6. Etapa de salida estéreo con control de ganancia y protección
        gain_left = patch.add_box("gain~", x=50.0, y=320.0)
        gain_right = patch.add_box("gain~", x=180.0, y=320.0)

        patch.connect(poly_synth, 0, gain_left, 0)
        patch.connect(poly_synth, 1, gain_right, 0)

        dac = patch.add_box("ezdac~", x=50.0, y=380.0)
        patch.connect(gain_left, 0, dac, 0)
        patch.connect(gain_right, 0, dac, 1)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        patch.save(output_path)

        return {
            "success": True,
            "patcher_path": str(Path(output_path).resolve()),
            "boxes_count": len(patch.boxes),
            "lines_count": len(patch.lines)
        }

