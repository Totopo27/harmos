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
		"rect" : [ 40.0, 40.0, 1180.0, 720.0 ],
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-title",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 15.0, 750.0, 24.0 ],
					"text" : "GENERADOR TET — Objeto Vectorial Nativo en Lienzo Max MSP (SDK First)",
					"fontsize" : 16.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-tet-canvas",
					"maxclass" : "jsui",
					"numinlets" : 2,
					"numoutlets" : 4,
					"outlettype" : [ "", "", "", "" ],
					"patching_rect" : [ 20.0, 50.0, 540.0, 540.0 ],
					"filename" : "tet_circle.js"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-sec-controls",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 50.0, 400.0, 20.0 ],
					"text" : "--- CONTROLES Y PARÁMETROS DEL CÍRCULO NATIVO ---",
					"fontsize" : 13.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-divs",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 85.0, 150.0, 20.0 ],
					"text" : "Divisiones n-TET (3..72):"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-num-divs",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 740.0, 85.0, 60.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-clip-divs",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 740.0, 115.0, 62.0, 22.0 ],
					"text" : "clip 3 72"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-loadbang",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 820.0, 85.0, 58.0, 22.0 ],
					"text" : "loadbang"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-msg-init-divs",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 890.0, 85.0, 29.5, 22.0 ],
					"text" : "19"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-sum",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 150.0, 150.0, 20.0 ],
					"text" : "Suma de Índices S (Eje):"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-num-sum",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 740.0, 150.0, 60.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-btn-export",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 580.0, 190.0, 130.0, 22.0 ],
					"text" : "export_svg"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-btn-toggle",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 720.0, 190.0, 120.0, 22.0 ],
					"text" : "toggle_inversion"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-sec-outputs",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 230.0, 400.0, 20.0 ],
					"text" : "--- SALIDAS DE SIMETRÍA NATIVAS ---",
					"fontsize" : 13.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-pairs",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 260.0, 150.0, 20.0 ],
					"text" : "Pares de Inversión:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-pairs",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 580.0, 285.0, 480.0, 22.0 ],
					"text" : ""
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-fixed",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 320.0, 150.0, 20.0 ],
					"text" : "Puntos Fijos (Ejes):"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-fixed",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 580.0, 345.0, 200.0, 22.0 ],
					"text" : ""
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-count",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 380.0, 150.0, 20.0 ],
					"text" : "Conteo de Simetrías:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-count",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 740.0, 380.0, 50.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-notify",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 580.0, 415.0, 150.0, 20.0 ],
					"text" : "Estado Exportación:"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-disp-notify",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 580.0, 440.0, 480.0, 22.0 ],
					"text" : ""
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "obj-msg-init-divs", 0 ],
					"source" : [ "obj-loadbang", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-num-divs", 0 ],
					"source" : [ "obj-msg-init-divs", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-clip-divs", 0 ],
					"source" : [ "obj-num-divs", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-tet-canvas", 1 ],
					"source" : [ "obj-clip-divs", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-tet-canvas", 0 ],
					"source" : [ "obj-num-sum", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-tet-canvas", 0 ],
					"source" : [ "obj-btn-export", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-tet-canvas", 0 ],
					"source" : [ "obj-btn-toggle", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-pairs", 1 ],
					"source" : [ "obj-tet-canvas", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-fixed", 1 ],
					"source" : [ "obj-tet-canvas", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-count", 0 ],
					"source" : [ "obj-tet-canvas", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-notify", 1 ],
					"source" : [ "obj-tet-canvas", 3 ]
				}

			}
 ]
	}

}
