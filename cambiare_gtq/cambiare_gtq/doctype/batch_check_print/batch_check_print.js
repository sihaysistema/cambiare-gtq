// Copyright (c) 2021, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Batch Check Print', {
    onload_post_render: function (frm) {
        frm.get_field("generate_print_sets").$input.addClass("btn btn-primary"); //" fa fa-upload");
    },
    generate_print_sets: function (frm) {
        let status_data = []
        if (frm.doc.check_to_print.length > 0) {
            var status_crea = ''
            // Por cada fila de tabla hija
            frm.doc.check_to_print.forEach(element => {
                let params = {
                    company: frm.doc.company,
                    source_bank_acc: element.bank_account,
                    start_date: frm.doc.transaction_start_date,
                    end_date: frm.doc.transaction_end_date,
                    currency: element.bank_account_currency
                }
                status_crea = generate_prints(frm, params, element.idx);
                console.log(status_crea);
            });
        }
    }
});


function generate_prints(frm, params, idx) {
    // Obtencion de datos
    frappe.call({
        method: 'cambiare_gtq.cambiare_gtq.doctype.cambiare_cheque_print_set.cambiare_cheque_print_set.get_data',
        args: {
            params: params
        },
        callback: function (r) {
            if (r.message.length == 0) {
                frappe.msgprint(__('Registro para la fila') + ` <b> ${idx}</b>,` + __('no creado, no se encontraron datos segun los parametros seleccionados'));
                return
            } else {
                // Creacion de registros, si hay data!
                frappe.call({
                    method: 'cambiare_gtq.cambiare_gtq.doctype.batch_check_print.batch_check_print.create_set',
                    args: {
                        params: params,
                        data_reg: r.message
                    },
                    callback: function (r) {
                        if (r.message[0]) {
                            frappe.msgprint(__('Registro para la fila') + `<b> ${idx} </b>,` + __('creado, puedes verlo en el siguiente link') +
                                ` <p><a href="#Form/Cambiare%20Cheque%20Print%20Set/${r.message[1]}" target="_blank">Ver</a>.</p>`);
                            return
                        } else {
                            frappe.msgprint(__('Registro para la fila') + ` <b> ${idx} </b>,` +
                                __(`no creado, no se encontraron datos segun los parametros seleccionados,
                                 mas detalles en el siguiente log \n`) + `<code> ${r.message[1]} </code>`);
                            return
                        }
                    }
                });
            }
        }
    });
}