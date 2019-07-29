// Copyright (c) 2019, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuration Cambiare', {
	refresh: function (frm) {
		console.log('Se refreso form');

		frappe.call({
			method: 'cambiare_gtq.api_cambiare.preparar_peticion_banguat',
			args: {
				opt: 7
			},
			callback: function (r) {
				console.log(r.message);
			}
		});
	}
});


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