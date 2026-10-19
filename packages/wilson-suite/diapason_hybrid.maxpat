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
		"rect" : [ 30.0, 30.0, 1200.0, 920.0 ],
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-title",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 15.0, 650.0, 24.0 ],
					"text" : "DIAPASÓN MICROTONAL (Tolgahan Çoğulu) — Traducción Híbrida de Alta Fidelidad en Max",
					"fontsize" : 16.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-reload",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 700.0, 15.0, 50.0, 22.0 ],
					"text" : "reload"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-url",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 760.0, 15.0, 160.0, 22.0 ],
					"text" : "url http://localhost:5175"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-jweb",
					"maxclass" : "jweb",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 45.0, 1140.0, 620.0 ],
					"rendermode" : 0,
					"url" : "http://localhost:5175"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-sec-audio",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 680.0, 400.0, 20.0 ],
					"text" : "--- MOTOR DE AUDIO DSP Y RECEPTOR DE NOTAS ---",
					"fontsize" : 13.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-udpreceive",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 710.0, 110.0, 22.0 ],
					"text" : "udpreceive 57120"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-route-osc",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "" ],
					"patching_rect" : [ 20.0, 745.0, 85.0, 22.0 ],
					"text" : "route /mnote"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-unpack-note",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "float", "float" ],
					"patching_rect" : [ 20.0, 780.0, 85.0, 22.0 ],
					"text" : "unpack 0. 0."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mtof",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 815.0, 36.0, 22.0 ],
					"text" : "mtof"
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
					"patching_rect" : [ 70.0, 815.0, 70.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-cycle",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 20.0, 850.0, 66.0, 22.0 ],
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
					"patching_rect" : [ 110.0, 850.0, 120.0, 26.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-ezdac",
					"maxclass" : "ezdac~",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 250.0, 840.0, 45.0, 45.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-sec-mpe",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 420.0, 680.0, 350.0, 20.0 ],
					"text" : "--- ENRUTAMIENTO MPE HACIA VST / DAW EXTERNO ---",
					"fontsize" : 13.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 420.0, 710.0, 160.0, 22.0 ],
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
					"patching_rect" : [ 420.0, 745.0, 65.0, 22.0 ],
					"text" : "route pb"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe-note",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "int", "int", "int" ],
					"patching_rect" : [ 500.0, 780.0, 85.0, 22.0 ],
					"text" : "unpack 0 0 1"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe-pb",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 420.0, 780.0, 75.0, 22.0 ],
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
					"patching_rect" : [ 420.0, 815.0, 180.0, 22.0 ],
					"text" : "midiformat"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-midiout",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 420.0, 855.0, 120.0, 22.0 ],
					"text" : "midiout \"from Max 1\""
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "obj-jweb", 0 ],
					"source" : [ "obj-msg-reload", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-jweb", 0 ],
					"source" : [ "obj-msg-url", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-route-osc", 0 ],
					"source" : [ "obj-udpreceive", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-unpack-note", 0 ],
					"source" : [ "obj-route-osc", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mtof", 0 ],
					"order" : 1,
					"source" : [ "obj-unpack-note", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 0 ],
					"order" : 0,
					"source" : [ "obj-unpack-note", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 1 ],
					"source" : [ "obj-unpack-note", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-hz", 0 ],
					"order" : 0,
					"source" : [ "obj-mtof", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-cycle", 0 ],
					"order" : 1,
					"source" : [ "obj-mtof", 0 ]
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
					"destination" : [ "obj-mpe-note", 0 ],
					"source" : [ "obj-mpe", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe-pb", 0 ],
					"source" : [ "obj-route-pb", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 5 ],
					"source" : [ "obj-mpe-pb", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 0 ],
					"source" : [ "obj-mpe-note", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 1 ],
					"source" : [ "obj-mpe-note", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-midiformat", 6 ],
					"source" : [ "obj-mpe-note", 2 ]
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
