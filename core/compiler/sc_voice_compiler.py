"""
Harmos SC Voice Compiler: Sintetizador de subpatchers de voz Max MSP (.maxpat)
a partir de especificaciones de grafos de síntesis de SuperCollider (SCMicroSynth/diesisRosa).
Genera parches estructurados para poly~ con cero hardcoding mediante TypedPatch.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from core.compiler.typed_patch import TypedPatch
from core.compiler.contract_engine import ContractEngine


class SCVoiceCompiler:
    """
    Compilador especializado en convertir SynthDefs de SuperCollider en
    subpatchers de voz compatibles con el objeto poly~ de Max MSP.
    """
    def __init__(self, contract_engine: Optional[ContractEngine] = None):
        self.engine = contract_engine or ContractEngine()

    def _build_voice_inputs(self, patch: TypedPatch) -> Dict[str, Any]:
        """Construye las entradas de audio/control y el módulo de vibrato."""
        # in~ 1: Frecuencia fundamental del carrier en Hz (señal)
        in_freq = patch.add_box("in~ 1", x=50.0, y=30.0)
        # in 2: Gate / Trigger para disparo de notas y envolventes
        in_gate = patch.add_box("in 2", x=350.0, y=30.0)
        # in 3: Amplitud de vibrato (control message -> sig~)
        in_vib = patch.add_box("in 3", x=180.0, y=30.0)
        sig_vib = patch.add_box("sig~ 0.0", x=180.0, y=70.0)
        patch.connect(in_vib, 0, sig_vib, 0)

        # LFO de vibrato: tri~ a fVib (default 5 Hz) con escalado a señal
        vib_lfo = patch.add_box("tri~ 5.0", x=260.0, y=70.0)
        vib_amp = patch.add_box("*~", x=180.0, y=120.0)
        patch.connect(vib_lfo, 0, vib_amp, 0)
        patch.connect(sig_vib, 0, vib_amp, 1)

        # Suma de vibrato a la frecuencia fundamental base: cFrec = f + vib
        carrier_freq_sum = patch.add_box("+~", x=50.0, y=80.0)
        patch.connect(in_freq, 0, carrier_freq_sum, 0)
        patch.connect(vib_amp, 0, carrier_freq_sum, 1)

        # Dispositivo de muteo/desactivación dinámica de poly~
        thispoly = patch.add_box("thispoly~", x=550.0, y=480.0)

        return {
            "in_freq": in_freq,
            "in_gate": in_gate,
            "in_vib": in_vib,
            "carrier_freq_sum": carrier_freq_sum,
            "thispoly": thispoly
        }

    def _build_fm_cascade(self, patch: TypedPatch, carrier_freq_sum: Any) -> Dict[str, Any]:
        """Construye la cascada FM de 3 operadores (Mod2 -> Mod1 -> Carrier)."""
        # 1. Modulador 2 (Operador más alto en la cascada)
        mod2_osc = patch.add_box("cycle~ 440", x=50.0, y=130.0)
        mod2_index_mul = patch.add_box("*~ 0.0", x=50.0, y=175.0)
        mod2_env = patch.add_box("adsr~ 0.0 0.0 1.0 0.0", x=350.0, y=90.0)
        mod2_sig_mul = patch.add_box("*~", x=50.0, y=220.0)

        patch.connect(mod2_osc, 0, mod2_index_mul, 0)
        patch.connect(mod2_index_mul, 0, mod2_sig_mul, 0)
        patch.connect(mod2_env, 0, mod2_sig_mul, 1)

        # 2. Modulador 1 (Operador Intermedio)
        mod1_sum = patch.add_box("+~", x=50.0, y=265.0)
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

        # 3. Carrier (Portadora Principal)
        carrier_sum = patch.add_box("+~", x=50.0, y=445.0)
        patch.connect(carrier_freq_sum, 0, carrier_sum, 0)
        patch.connect(mod1_sig_mul, 0, carrier_sum, 1)

        carrier_osc = patch.add_box("cycle~", x=50.0, y=490.0)
        patch.connect(carrier_sum, 0, carrier_osc, 0)

        carrier_env = patch.add_box("adsr~ 10 300 0.5 1000", x=350.0, y=290.0)
        carrier_amp_mul = patch.add_box("*~", x=50.0, y=535.0)

        patch.connect(carrier_osc, 0, carrier_amp_mul, 0)
        patch.connect(carrier_env, 0, carrier_amp_mul, 1)

        return {
            "mod2_env": mod2_env,
            "mod1_env": mod1_env,
            "carrier_env": carrier_env,
            "carrier_amp_mul": carrier_amp_mul
        }

    def compile_fm_voice(self, output_path: str, ir_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sintetiza la voz de 3 operadores FM en cascada:
        Modulador 2 -> Modulador 1 -> Carrier.
        Implementa control de envolvente, vibrato y desasignación dinámica de poly~.
        """
        patch = TypedPatch(self.engine)

        inputs = self._build_voice_inputs(patch)
        fm = self._build_fm_cascade(patch, inputs["carrier_freq_sum"])

        # Control de Envolventes y Desasignación de Voz (Gate)
        in_gate = inputs["in_gate"]
        patch.connect(in_gate, 0, fm["mod2_env"], 0)
        patch.connect(in_gate, 0, fm["mod1_env"], 0)
        patch.connect(in_gate, 0, fm["carrier_env"], 0)

        # El outlet 1 de adsr~ emite un bang al completar la fase de release
        patch.connect(fm["carrier_env"], 1, inputs["thispoly"], 0)

        # Salidas Estéreo hacia poly~
        out_l = patch.add_box("out~ 1", x=50.0, y=575.0)
        out_r = patch.add_box("out~ 2", x=180.0, y=575.0)

        carrier_amp_mul = fm["carrier_amp_mul"]
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

    def _resolve_scale_menu_items(self, control_ir: Optional[Dict[str, Any]]) -> List[str]:
        """Resuelve la lista de opciones para el menú de afinaciones microtonales."""
        menu_items = []
        if control_ir and "control_interfaces" in control_ir:
            for iface in control_ir["control_interfaces"]:
                if iface.get("ui_type") == "umenu" and iface.get("options"):
                    menu_items = iface["options"]
                    break

        if not menu_items and control_ir and "data_tables" in control_ir:
            menu_items = [
                t.get("source_file") or f"{t['name']}.txt"
                for t in control_ir["data_tables"]
                if t.get("source_file") or t.get("name")
            ]

        if not menu_items:
            menu_items = [
                "tet12.txt", "tet31.txt", "tet41.txt", "tet53.txt",
                "meantone31.txt", "magic41.txt", "partch.txt", "centaur.txt"
            ]
        return menu_items

    def _build_tuning_pipeline(
        self,
        patch: TypedPatch,
        midi_in: Any,
        control_ir: Optional[Dict[str, Any]]
    ) -> Any:
        """Construye el pipeline de selección de escala, lectura de coll y cálculo Truax."""
        menu_items = self._resolve_scale_menu_items(control_ir)
        umenu_extra = {
            "items": TypedPatch.format_umenu_items(menu_items)
        }
        scale_menu = patch.add_box("umenu", x=220.0, y=30.0, w=150.0, extra_attributes=umenu_extra)
        prepend_read = patch.add_box("prepend read", x=220.0, y=70.0)
        patch.connect(scale_menu, 1, prepend_read, 0)

        # Determinar tabla por defecto según control_ir o fallback canónico
        default_table = "tet31.txt"
        if control_ir and "data_tables" in control_ir and control_ir["data_tables"]:
            default_table = control_ir["data_tables"][0].get("source_file", "tet31.txt")

        # Mapeador de afinación microtonal (coll cargando tabla 384 posiciones)
        tuning_coll = patch.add_box(f"coll {default_table}", x=50.0, y=110.0)
        patch.connect(prepend_read, 0, tuning_coll, 0)
        patch.connect(midi_in, 0, tuning_coll, 0)

        # Calculador de Forma Normal de Barry Truax (js truax.js)
        truax_calc = patch.add_box("js truax.js", x=50.0, y=160.0)
        patch.connect(tuning_coll, 0, truax_calc, 0)

        # Convertir frecuencia calculada a señal para poly~
        freq_sig = patch.add_box("sig~", x=50.0, y=210.0)
        patch.connect(truax_calc, 0, freq_sig, 0)
        return freq_sig

    def compile_main_synth(
        self,
        output_path: str,
        voice_patcher_name: str = "fmVoice",
        polyphony: int = 16,
        control_ir: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sintetiza el parche principal contenedor de diesisRosa (diesisRosa.maxpat):
        - Entrada MIDI (notein)
        - Selector de afinaciones microtonales dinámico derivado de control_ir (umenu -> prepend read -> coll)
        - Mapeo de frecuencia microtonal con tabla de afinaciones (coll)
        - Compensación de fundamental por Forma Normal de Barry Truax (js truax.js)
        - Banco polifónico (poly~ <voice_patcher_name> <polyphony>)
        - Master Limiter / Output (gain~ / ezdac~)
        """
        patch = TypedPatch(self.engine)

        midi_in = patch.add_box("notein", x=50.0, y=30.0)
        freq_sig = self._build_tuning_pipeline(patch, midi_in, control_ir)

        # Banco Polifónico (poly~ fmVoice 16)
        poly_synth = patch.add_box(f"poly~ {voice_patcher_name} {polyphony}", x=50.0, y=260.0)
        # Señal de frecuencia al inlet de audio de poly~ (inlet 1)
        patch.connect(freq_sig, 0, poly_synth, 1)
        # Velocity de notein al inlet de control de poly~ (inlet 0) para disparar la envolvente
        patch.connect(midi_in, 1, poly_synth, 0)

        # Etapa de salida estéreo con control de ganancia y dac
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
