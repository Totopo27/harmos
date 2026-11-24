"""
Harmos SC Voice Compiler: Sintetizador de subpatchers de voz Max MSP (.maxpat)
a partir de especificaciones IR de grafos de síntesis y control (agnóstico de dominio).
Genera parches estructurados para poly~ con cero hardcoding mediante TypedPatch.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
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
        patch.connect_semantic(in_vib, "control_output", sig_vib, "number_or_signal")

        # LFO de vibrato: tri~ a fVib (default 5 Hz) con escalado a señal
        vib_lfo = patch.add_box("tri~ 5.0", x=260.0, y=70.0)
        vib_amp = patch.add_box("*~", x=180.0, y=120.0)
        patch.connect_semantic(vib_lfo, "audio_out", vib_amp, "audio_in_a")
        patch.connect_semantic(sig_vib, "signal_out", vib_amp, "audio_in_b_or_gain")

        # Suma de vibrato a la frecuencia fundamental base: cFrec = f + vib
        carrier_freq_sum = patch.add_box("+~", x=50.0, y=80.0)
        patch.connect_semantic(in_freq, "signal_output", carrier_freq_sum, "audio_in_a")
        patch.connect_semantic(vib_amp, "multiplied_audio", carrier_freq_sum, "audio_in_b_or_offset")

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

        patch.connect_semantic(mod2_osc, "audio_out", mod2_index_mul, "audio_in_a")
        patch.connect_semantic(mod2_index_mul, "multiplied_audio", mod2_sig_mul, "audio_in_a")
        patch.connect_semantic(mod2_env, "envelope_signal", mod2_sig_mul, "audio_in_b_or_gain")

        # 2. Modulador 1 (Operador Intermedio)
        mod1_sum = patch.add_box("+~", x=50.0, y=265.0)
        patch.connect_semantic(carrier_freq_sum, "summed_audio", mod1_sum, "audio_in_a")
        patch.connect_semantic(mod2_sig_mul, "multiplied_audio", mod1_sum, "audio_in_b_or_offset")

        mod1_osc = patch.add_box("cycle~", x=50.0, y=310.0)
        patch.connect_semantic(mod1_sum, "summed_audio", mod1_osc, "frequency_hz")

        mod1_index_mul = patch.add_box("*~ 100.0", x=50.0, y=355.0)
        mod1_env = patch.add_box("adsr~ 0.0 0.0 1.0 0.0", x=350.0, y=190.0)
        mod1_sig_mul = patch.add_box("*~", x=50.0, y=400.0)

        patch.connect_semantic(mod1_osc, "audio_out", mod1_index_mul, "audio_in_a")
        patch.connect_semantic(mod1_index_mul, "multiplied_audio", mod1_sig_mul, "audio_in_a")
        patch.connect_semantic(mod1_env, "envelope_signal", mod1_sig_mul, "audio_in_b_or_gain")

        # 3. Carrier (Portadora Principal)
        carrier_sum = patch.add_box("+~", x=50.0, y=445.0)
        patch.connect_semantic(carrier_freq_sum, "summed_audio", carrier_sum, "audio_in_a")
        patch.connect_semantic(mod1_sig_mul, "multiplied_audio", carrier_sum, "audio_in_b_or_offset")

        carrier_osc = patch.add_box("cycle~", x=50.0, y=490.0)
        patch.connect_semantic(carrier_sum, "summed_audio", carrier_osc, "frequency_hz")

        carrier_env = patch.add_box("adsr~ 10 300 0.5 1000", x=350.0, y=290.0)
        carrier_amp_mul = patch.add_box("*~", x=50.0, y=535.0)

        patch.connect_semantic(carrier_osc, "audio_out", carrier_amp_mul, "audio_in_a")
        patch.connect_semantic(carrier_env, "envelope_signal", carrier_amp_mul, "audio_in_b_or_gain")

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
        patch.connect_semantic(in_gate, "control_output", fm["mod2_env"], "gate_trigger")
        patch.connect_semantic(in_gate, "control_output", fm["mod1_env"], "gate_trigger")
        patch.connect_semantic(in_gate, "control_output", fm["carrier_env"], "gate_trigger")

        # El outlet de fin de release dispara un mensaje "0" para liberar la voz en poly~
        release_free_msg = patch.add_message("0", x=450.0, y=430.0)
        patch.connect_semantic(fm["carrier_env"], "envelope_completed_bang", release_free_msg, "trigger_or_set_message")
        patch.connect_semantic(release_free_msg, "message_out", inputs["thispoly"], "mute_or_voice_messages")

        # Salidas Estéreo hacia poly~
        out_l = patch.add_box("out~ 1", x=50.0, y=575.0)
        out_r = patch.add_box("out~ 2", x=180.0, y=575.0)

        carrier_amp_mul = fm["carrier_amp_mul"]
        patch.connect_semantic(carrier_amp_mul, "multiplied_audio", out_l, "signal_input")
        patch.connect_semantic(carrier_amp_mul, "multiplied_audio", out_r, "signal_input")

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

        return menu_items or ["scale_default.txt"]

    def _build_tuning_pipeline(
        self,
        patch: TypedPatch,
        midi_in: Any,
        control_ir: Optional[Dict[str, Any]]
    ) -> Any:
        """Construye el pipeline de selección de tabla, coll y mapeo JS."""
        menu_items = self._resolve_scale_menu_items(control_ir)
        umenu_extra = {
            "items": TypedPatch.format_umenu_items(menu_items)
        }
        scale_menu = patch.add_box("umenu", x=220.0, y=30.0, w=150.0, extra_attributes=umenu_extra)
        prepend_read = patch.add_box("prepend read", x=220.0, y=70.0)
        patch.connect_semantic(scale_menu, "item_text", prepend_read, "input_message")

        # Determinar tabla por defecto según control_ir o fallback neutral
        default_table = menu_items[0]
        if control_ir and "data_tables" in control_ir and control_ir["data_tables"]:
            default_table = control_ir["data_tables"][0].get("source_file", default_table)

        # Mapeador de frecuencias basado en tabla (coll)
        tuning_coll = patch.add_box(f"coll {default_table}", x=50.0, y=110.0)
        patch.connect_semantic(prepend_read, "prepended_message", tuning_coll, "address_or_message")
        patch.connect_semantic(midi_in, "pitch", tuning_coll, "address_or_message")

        # Procesador JS configurable desde control_ir
        script_file = (control_ir or {}).get("script_file", "pitch_mapper.js")
        pitch_calc = patch.add_box(f"js {script_file}", x=50.0, y=160.0)
        patch.connect_semantic(tuning_coll, "entry_data", pitch_calc, "js_inlet_0")

        # Convertir frecuencia calculada a señal para poly~
        freq_sig = patch.add_box("sig~", x=50.0, y=210.0)
        patch.connect_semantic(pitch_calc, "js_outlet_0", freq_sig, "number_or_signal")
        return freq_sig

    def compile_main_synth(
        self,
        output_path: str,
        voice_patcher_name: str = "fmVoice",
        polyphony: int = 16,
        control_ir: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sintetiza el parche principal contenedor polifónico a partir de control_ir:
        - Entrada MIDI (notein) -> selector dinámico (umenu -> prepend read -> coll -> js -> sig~)
        - Banco polifónico (poly~ <voice_patcher_name> <polyphony>)
        - Etapa de salida estéreo (gain~ / ezdac~)
        """
        patch = TypedPatch(self.engine)

        midi_in = patch.add_box("notein", x=50.0, y=30.0)
        freq_sig = self._build_tuning_pipeline(patch, midi_in, control_ir)

        # Banco Polifónico
        poly_synth = patch.add_box(f"poly~ {voice_patcher_name} {polyphony}", x=50.0, y=260.0)
        patch.connect_semantic(freq_sig, "signal_out", poly_synth, "audio_or_signal_in")
        patch.connect_semantic(midi_in, "velocity", poly_synth, "target_voice_or_messages")

        # Etapa de salida estéreo con control de ganancia y dac
        gain_left = patch.add_box("gain~", x=50.0, y=320.0)
        gain_right = patch.add_box("gain~", x=180.0, y=320.0)

        patch.connect_semantic(poly_synth, "audio_out_1", gain_left, "audio_in")
        patch.connect_semantic(poly_synth, "audio_out_2", gain_right, "audio_in")

        dac = patch.add_box("ezdac~", x=50.0, y=380.0)
        patch.connect_semantic(gain_left, "audio_out", dac, "audio_left")
        patch.connect_semantic(gain_right, "audio_out", dac, "audio_right")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        patch.save(output_path)

        return {
            "success": True,
            "patcher_path": str(Path(output_path).resolve()),
            "boxes_count": len(patch.boxes),
            "lines_count": len(patch.lines)
        }
