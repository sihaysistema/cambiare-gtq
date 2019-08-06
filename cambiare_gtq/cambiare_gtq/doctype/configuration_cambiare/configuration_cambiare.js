// Copyright (c) 2019, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuration Cambiare', {
	refresh: function (frm) {
		console.log('Se refreso form');
		consulta_tipo_cambio_dia(frm)

		// Obtiene las monedas disponibles de la API banguat
		frappe.call({
			method: "cambiare_gtq.api_cambiare.preparar_peticion_banguat",
			args: {
				opt: '7'
			},
			freeze: true,
			freeze_message: __("Obteniendo y guardando monedas disponibles del Banco de Guatemala..."),
			callback: function (r) {
				if (!r.exc) {
					clearInterval(frm.page["interval"]);
					// console.log(r.message)

					frappe.meta.get_docfield('Available Currencies', 'moneda', cur_frm.doc.name).options = r.message
					cur_frm.refresh_field('moneda');
				}
			}
		});

		frm.add_custom_button(__('Button Name'), () => {
			frappe.call({
				method: "cambiare_gtq.api_cambiare.preparar_peticion_banguat",
				args: {
					opt: '6'
				},
				freeze: true,
				freeze_message: __("Obteniendo y guardando monedas disponibles del Banco de Guatemala..."),
				callback: function (r) {
					if (!r.exc) {
						clearInterval(frm.page["interval"]);
						console.log(r.message)
					}
				}
			});
		});

	}
});

let consulta_tipo_cambio_dia = function (frm) {
	frm.page.set_secondary_action(__("Tipo Cambio GTQ"), function () {
		frappe.call({
			method: "cambiare_gtq.api_cambiare.preparar_peticion_banguat",
			args: {
				opt: '1'
			},
			freeze: true,
			freeze_message: __("Consultado tipo cambio del dia..."),
			callback: function (r) {
				if (!r.exc) {
					clearInterval(frm.page["interval"]);
					// frm.page.set_indicator(__('Importacion Exitosa!!'), 'blue');
					// create_reset_button(frm);
					console.log(r.message)
				}
			}
		});
	}).addClass('btn btn-primary');
}


// Tabla hija
// frappe.ui.form.on('Available Currencies', {
// 	moneda: function (frm) {
// 		console.log('Selected');
// 	},
// 	monedas_add: function (frm) {
// 		console.log('Se agrego una fila');
// 	},
// 	form_render: function (frm) {
// 		console.log('Se renderizo');
// 	}
// });