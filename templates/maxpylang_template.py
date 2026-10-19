"""Plantilla generadora de parches para Max/MSP y dispositivos Max for Live.

Uso:
    python maxpylang_template.py
"""

import maxpylang as mp


def build_stereo_audio_effect(output_filename="effect.maxpat"):
    """Construye una cadena estéreo básica con oscilador modulador y filtro."""
    patch = mp.MaxPatch()

    # Constantes de layout
    Y_STEP = 40
    COL_WIDTH = 160

    # 1. Fuente de sonido principal
    patch.set_position(50, 50)
    carrier = patch.place("cycle~ 220")[0]

    # 2. Modulador LFO en columna adyacente
    patch.set_position(50 + COL_WIDTH, 50)
    lfo = patch.place("cycle~ 2")[0]

    patch.set_position(50 + COL_WIDTH, 50 + Y_STEP)
    lfo_scale = patch.place("*~ 50")[0]

    patch.set_position(50 + COL_WIDTH, 50 + (Y_STEP * 2))
    lfo_offset = patch.place("+~ 300")[0]

    # 3. Filtro resonante
    patch.set_position(50, 150)
    filt = patch.place("lores~ 500 0.7")[0]

    # 4. Control de ganancia
    patch.set_position(50, 200)
    gain = patch.place("gain~")[0]

    # 5. Salida de audio DAC
    patch.set_position(50, 270)
    dac = patch.place("ezdac~")[0]

    # Conexiones LFO -> Frecuencia de corte
    patch.connect(
        [lfo.outs[0], lfo_scale.ins[0]],
        [lfo_scale.outs[0], lfo_offset.ins[0]],
        [lfo_offset.outs[0], filt.ins[1]],  # Inlet 1 controla cutoff
    )

    # Conexiones Cadena Principal de Audio
    patch.connect(
        [carrier.outs[0], filt.ins[0]],
        [filt.outs[0], gain.ins[0]],
        [gain.outs[0], dac.ins[0]],  # Salida izquierda
        [gain.outs[0], dac.ins[1]],  # Salida derecha
    )

    patch.save(output_filename)
    print(f"Parche generado exitosamente: {output_filename}")


if __name__ == "__main__":
    build_stereo_audio_effect("synth_lfo_filter.maxpat")
