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
		"rect" : [ 30.0, 30.0, 1150.0, 850.0 ],
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 40.0, 15.0, 110.0, 22.0 ],
					"text" : "wilson.core 1 3 5 7"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-normal",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 40.0, 45.0, 115.0, 22.0 ],
					"text" : "cell_size 12, cols 39"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-ipad",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 170.0, 45.0, 155.0, 22.0 ],
					"text" : "cell_size 28, cols 16, rows 10"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-giant",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 340.0, 45.0, 150.0, 22.0 ],
					"text" : "cell_size 42, cols 10, rows 6"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-hex",
					"maxclass" : "wilson.hexslider",
					"numinlets" : 2,
					"numoutlets" : 3,
					"outlettype" : [ "float", "int", "list" ],
					"patching_rect" : [ 40.0, 75.0, 750.0, 240.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-fretboard",
					"maxclass" : "micro.fretboard",
					"numinlets" : 2,
					"numoutlets" : 4,
					"outlettype" : [ "float", "int", "list", "list" ],
					"patching_rect" : [ 40.0, 335.0, 750.0, 140.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-tt",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 805.0, 340.0, 125.0, 22.0 ],
					"text" : "true_temperament 1"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-std",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 805.0, 370.0, 125.0, 22.0 ],
					"text" : "true_temperament 0"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-edo19",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 805.0, 400.0, 60.0, 22.0 ],
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
					"patching_rect" : [ 875.0, 400.0, 60.0, 22.0 ],
					"text" : "edo 31."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-mpe",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 40.0, 500.0, 160.0, 22.0 ],
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
					"patching_rect" : [ 40.0, 540.0, 65.0, 22.0 ],
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
					"patching_rect" : [ 120.0, 580.0, 85.0, 22.0 ],
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
					"patching_rect" : [ 40.0, 580.0, 75.0, 22.0 ],
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
					"patching_rect" : [ 40.0, 640.0, 180.0, 22.0 ],
					"text" : "midiformat"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-midiout",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 40.0, 680.0, 120.0, 22.0 ],
					"text" : "midiout \"from Max 1\""
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-cents-disp",
					"maxclass" : "flonum",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 210.0, 540.0, 70.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-osc-format",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 400.0, 540.0, 180.0, 22.0 ],
					"text" : "sprintf /wilson/hex/hz %f"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-udpsend",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 400.0, 580.0, 160.0, 22.0 ],
					"text" : "udpsend 127.0.0.1 57120"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-udpreceive",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 600.0, 540.0, 110.0, 22.0 ],
					"text" : "udpreceive 57121"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-osc-monitor",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 600.0, 580.0, 180.0, 22.0 ],
					"text" : "esperando osc..."
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "obj-hex", 0 ],
					"source" : [ "obj-msg-normal", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-hex", 0 ],
					"source" : [ "obj-msg-ipad", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-hex", 0 ],
					"source" : [ "obj-msg-giant", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-tt", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-fretboard", 0 ],
					"source" : [ "obj-msg-std", 0 ]
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
					"destination" : [ "obj-mpe", 0 ],
					"source" : [ "obj-hex", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-osc-format", 0 ],
					"source" : [ "obj-hex", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 1 ],
					"source" : [ "obj-hex", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 0 ],
					"source" : [ "obj-fretboard", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-osc-format", 0 ],
					"source" : [ "obj-fretboard", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-mpe", 1 ],
					"source" : [ "obj-fretboard", 1 ]
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
					"destination" : [ "obj-cents-disp", 0 ],
					"source" : [ "obj-mpe", 2 ]
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
					"destination" : [ "obj-unpack-note", 0 ],
					"source" : [ "obj-route-pb", 1 ]
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
, 			{
				"patchline" : 				{
					"destination" : [ "obj-udpsend", 0 ],
					"source" : [ "obj-osc-format", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-osc-monitor", 1 ],
					"source" : [ "obj-udpreceive", 0 ]
				}

			}
 ]
	}

}
