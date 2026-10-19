"""Canonical MaxPyLang Patterns for Max/MSP (.maxpat) and Max for Live (.amxd)."""

import maxpylang as mp

# ==============================================================================
# Patrón A: Cadena Básica de Audio en Max (.maxpat)
# ==============================================================================
def create_simple_synth(output_path: str = "simple_synth.maxpat") -> None:
    patch = mp.MaxPatch()

    patch.set_position(50, 50)
    osc = patch.place("cycle~ 220")[0]

    patch.set_position(50, 90)
    gain = patch.place("gain~")[0]

    patch.set_position(50, 160)
    dac = patch.place("ezdac~")[0]

    patch.connect(
        [osc.outs[0], gain.ins[0]],
        [gain.outs[0], dac.ins[0]],
        [gain.outs[0], dac.ins[1]],
    )

    patch.save(output_path)


# ==============================================================================
# Patrón B: Dispositivo de Instrumento Max for Live (.amxd)
# ==============================================================================
def create_m4l_instrument(output_path: str = "m4l_synth.amxd") -> None:
    patch = mp.MaxPatch()

    # Entrada MIDI
    patch.set_position(50, 40)
    notein = patch.place("notein")[0]

    patch.set_position(50, 80)
    mtof = patch.place("mtof")[0]

    # Generador de Tono
    patch.set_position(50, 120)
    osc = patch.place("cycle~")[0]

    # Envolvente / Ganancia con velocidad MIDI
    patch.set_position(120, 80)
    strip_vel = patch.place("/ 127.")[0]

    patch.set_position(50, 160)
    mult = patch.place("*~")[0]

    # Limitador de seguridad obligatorio para Live
    patch.set_position(50, 200)
    limiter = patch.place("clip~ -1. 1.")[0]

    # Salida a Live
    patch.set_position(50, 240)
    plugout = patch.place("plugout~")[0]

    # Conexiones
    patch.connect(
        [notein.outs[0], mtof.ins[0]],       # Pitch a mtof
        [notein.outs[1], strip_vel.ins[0]],  # Velocity normalizada
        [mtof.outs[0], osc.ins[0]],          # Frecuencia a oscilador
        [osc.outs[0], mult.ins[0]],          # Audio a multiplicador
        [strip_vel.outs[0], mult.ins[1]],    # Amplitud por velocidad
        [mult.outs[0], limiter.ins[0]],      # Limitador
        [limiter.outs[0], plugout.ins[0]],   # Canal Izquierdo
        [limiter.outs[0], plugout.ins[1]],   # Canal Derecho
    )

    patch.save(output_path, device_type="instrument")


# ==============================================================================
# Patrón C: Síntesis Aditiva Masiva (Iteración en Bucle)
# ==============================================================================
def create_additive_synth(
    output_path: str = "additive_synth.maxpat",
    num_voices: int = 8,
    base_freq: float = 110.0,
) -> None:
    patch = mp.MaxPatch()

    patch.set_position(50, 250)
    master_gain = patch.place("gain~")[0]
    patch.set_position(50, 320)
    dac = patch.place("ezdac~")[0]

    patch.connect(
        [master_gain.outs[0], dac.ins[0]],
        [master_gain.outs[0], dac.ins[1]],
    )

    for i in range(num_voices):
        x_pos = 50 + (i * 120)
        freq = base_freq * (i + 1)

        patch.set_position(x_pos, 50)
        osc = patch.place(f"cycle~ {freq}")[0]

        patch.set_position(x_pos, 100)
        amp = patch.place(f"*~ {1.0 / (i + 1):.3f}")[0]

        patch.connect(
            [osc.outs[0], amp.ins[0]],
            [amp.outs[0], master_gain.ins[0]],  # Entradas MSP auto-summing
        )

    patch.save(output_path)


if __name__ == "__main__":
    create_simple_synth()
    create_m4l_instrument()
    create_additive_synth()
