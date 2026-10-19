{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 9,
			"minor" : 0,
			"revision" : 0,
			"architecture" : "x64",
			"modern" : 1
		}
,
		"classnamespace" : "box",
		"rect" : [ 50.0, 50.0, 1080.0, 720.0 ],
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-title",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 40.0, 20.0, 520.0, 24.0 ],
					"text" : "DIAPASÓN MICROTONAL (Tolgahan Çoğulu) — Port a Max MSP vía Traductor",
					"fontsize" : 16.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-dalessandro",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 40.0, 60.0, 160.0, 22.0 ],
					"text" : "tuning_system dalessandro"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-partch",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 210.0, 60.0, 125.0, 22.0 ],
					"text" : "tuning_system partch"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-12tet",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 345.0, 60.0, 120.0, 22.0 ],
					"text" : "tuning_system 12tet"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-edo19",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 475.0, 60.0, 60.0, 22.0 ],
					"text" : "edo 19."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-edo31",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 545.0, 60.0, 60.0, 22.0 ],
					"text" : "edo 31."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-tt1",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 620.0, 60.0, 125.0, 22.0 ],
					"text" : "true_temperament 1"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-tt0",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 755.0, 60.0, 125.0, 22.0 ],
					"text" : "true_temperament 0"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-fretboard",
					"maxclass" : "micro.fretboard",
					"numinlets" : 2,
					"numoutlets" : 4,
					"outlettype" : [ "float", "int", "list", "list" ],
					"patching_rect" : [ 40.0, 100.0, 980.0, 220.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-hz",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 40.0, 340.0, 60.0, 20.0 ],
					"text" : "Freq (Hz):"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-hz",
					"maxclass" : "flonum",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 105.0, 340.0, 85.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-vel",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 340.0, 55.0, 20.0 ],
					"text" : "Velocity:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-vel",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 270.0, 340.0, 50.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-meta",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 340.0, 340.0, 75.0, 20.0 ],
					"text" : "Metadatos:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-meta",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 420.0, 340.0, 320.0, 22.0 ],
					"text" : "meta info..."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-chord",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 760.0, 340.0, 55.0, 20.0 ],
					"text" : "Acordes:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-chord",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 820.0, 340.0, 200.0, 22.0 ],
					"text" : "chord hz..."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-synth-comment",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 40.0, 385.0, 300.0, 20.0 ],
					"text" : "--- SÍNTESIS DE AUDIO DIRECTA (CYCLE~) ---"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-cycle",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 40.0, 415.0, 66.0, 22.0 ],
					"text" : "cycle~ 440."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-gain",
					"maxclass" : "gain~",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 40.0, 455.0, 130.0, 30.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-ezdac",
					"maxclass" : "ezdac~",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 40.0, 505.0, 45.0, 45.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe-comment",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 350.0, 385.0, 300.0, 20.0 ],
					"text" : "--- SALIDA MPE (MICRO.MPE -> MIDI/DAW) ---"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 350.0, 415.0, 160.0, 22.0 ],
					"text" : "micro.mpe"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-route-pb",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 2,
					"outlettype" : [ "", "" ],
					"patching_rect" : [ 350.0, 455.0, 65.0, 22.0 ],
					"text" : "route pb"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-unpack-note",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "int", "int", "int" ],
					"patching_rect" : [ 430.0, 495.0, 85.0, 22.0 ],
					"text" : "unpack 0 0 1"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-unpack-pb",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 350.0, 495.0, 75.0, 22.0 ],
					"text" : "unpack 8192 1"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-midiformat",
					"maxclass" : "newobj",
					"numinlets" : 7,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 350.0, 545.0, 180.0, 22.0 ],
					"text" : "midiformat"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-midiout",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 350.0, 585.0, 120.0, 22.0 ],
					"text" : "midiout \"from Max 1\""
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-dalessandro", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-partch", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-12tet", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-edo19", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-edo31", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-tt1", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-tt0", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-hz", 0 ],
					"order" : 2,
					"source" : [ "obj-fretboard", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-cycle", 0 ],
					"order" : 1,
					"source" : [ "obj-fretboard", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 0 ],
					"order" : 0,
					"source" : [ "obj-fretboard", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-vel", 0 ],
					"order" : 1,
					"source" : [ "obj-fretboard", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 1 ],
					"order" : 0,
					"source" : [ "obj-fretboard", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-meta", 1 ],
					"source" : [ "obj-fretboard", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-chord", 1 ],
					"source" : [ "obj-fretboard", 3 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-gain", 0 ],
					"source" : [ "obj-cycle", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-ezdac", 1 ],
					"order" : 0,
					"source" : [ "obj-gain", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-ezdac", 0 ],
					"order" : 1,
					"source" : [ "obj-gain", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-route-pb", 0 ],
					"source" : [ "obj-mpe", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-unpack-note", 0 ],
					"source" : [ "obj-mpe", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-unpack-pb", 0 ],
					"source" : [ "obj-route-pb", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 5 ],
					"source" : [ "obj-unpack-pb", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 0 ],
					"source" : [ "obj-unpack-note", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 1 ],
					"source" : [ "obj-unpack-note", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 6 ],
					"source" : [ "obj-unpack-note", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiout", 0 ],
					"source" : [ "obj-midiformat", 0 ]
				}

			}
 ]
	}

}
