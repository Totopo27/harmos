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
		"rect" : [ 40.0, 40.0, 1340.0, 780.0 ],
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-title",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 15.0, 600.0, 24.0 ],
					"text" : "GENERADOR DE CÍRCULOS TET — Análisis de Simetrías e Imágenes Vectoriales SVG",
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
					"patching_rect" : [ 640.0, 15.0, 50.0, 22.0 ],
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
					"patching_rect" : [ 700.0, 15.0, 200.0, 22.0 ],
					"text" : "url http://localhost:5174/generadorTETAnalisisCirculos/"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-jweb",
					"maxclass" : "jweb",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 50.0, 880.0, 680.0 ],
					"rendermode" : 0,
					"url" : "http://localhost:5174/generadorTETAnalisisCirculos/"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-sec-core",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 50.0, 390.0, 20.0 ],
					"text" : "--- ANÁLISIS DE SIMETRÍAS Y CONTROL (tet_inversion.js) ---",
					"fontsize" : 13.0
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-divs",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 80.0, 130.0, 20.0 ],
					"text" : "Divisiones (3 a 72):"
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
					"patching_rect" : [ 1060.0, 80.0, 60.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-clip-divs",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 1060.0, 115.0, 62.0, 22.0 ],
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
					"patching_rect" : [ 1140.0, 80.0, 58.0, 22.0 ],
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
					"patching_rect" : [ 1210.0, 80.0, 29.5, 22.0 ],
					"text" : "19"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-sum",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 150.0, 130.0, 20.0 ],
					"text" : "Suma de Índices S:"
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
					"patching_rect" : [ 1060.0, 150.0, 60.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-tet-inversion",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 920.0, 190.0, 160.0, 22.0 ],
					"saved_object_attributes" : 					{
						"filename" : "tet_inversion.js",
						"parameter_enable" : 0
					}
,
					"text" : "js tet_inversion.js"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-pairs",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 230.0, 140.0, 20.0 ],
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
					"patching_rect" : [ 920.0, 255.0, 390.0, 22.0 ],
					"text" : ""
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-fixed",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 290.0, 140.0, 20.0 ],
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
					"patching_rect" : [ 920.0, 315.0, 180.0, 22.0 ],
					"text" : ""
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-lbl-count",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 920.0, 350.0, 140.0, 20.0 ],
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
					"patching_rect" : [ 1060.0, 350.0, 50.0, 22.0 ]
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
					"destination" : [ "obj-tet-inversion", 1 ],
					"source" : [ "obj-clip-divs", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-tet-inversion", 0 ],
					"source" : [ "obj-num-sum", 0 ]
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
					"destination" : [ "obj-jweb", 0 ],
					"source" : [ "obj-msg-reload", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-pairs", 1 ],
					"source" : [ "obj-tet-inversion", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-fixed", 1 ],
					"source" : [ "obj-tet-inversion", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-disp-count", 0 ],
					"source" : [ "obj-tet-inversion", 2 ]
				}

			}
 ]
	}

}
