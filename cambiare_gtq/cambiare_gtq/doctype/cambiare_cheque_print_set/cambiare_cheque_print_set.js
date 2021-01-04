// Copyright (c) 2021, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cambiare Cheque Print Set', {
    onload: function (frm) {
        // Filtro para generar listado solo de cuentas bancarias
        // que sean:
        frm.set_query('source_bank_account', () => {
            return {
                filters: {
                    is_company_account: 1,
                    company: frm.doc.company
                }
            };
        });
        cur_frm.refresh_field('source_bank_account');
    },
    get_cheque_payments: function (frm) {
        console.log('Hola Mundo');

        frappe.call({
            method: 'cambiare_gtq.cambiare_gtq.doctype.cambiare_cheque_print_set.cambiare_cheque_print_set.get_data',
            args: {
                params: {
                    company: frm.doc.company,
                    source_bank_acc: frm.doc.source_bank_account,
                    start_date: frm.doc.start_date,
                    end_date: frm.doc.end_date,
                    currency: frm.doc.currency
                },
            },
            // freeze: true,
            // freeze_message: __('Generando reporte, por favor espere...'),
            callback: function (r) {
                // if (!r.exc) {
                //     clearInterval(frm.page['interval']);
                //     frm.reload_doc();
                // }
                console.log(r.message);

                frm.doc.cheque_to_print = []
                frm.refresh_field("cheque_to_print");

                r.message.forEach(element => {
                    frm.add_child("cheque_to_print", {
                        transaction_id: element.transaction_id,
                        cheque_no: element.cheque_no,
                        amount: element.amount,
                        party_type: element.party_type,
                        third_party: element.third_party
                    });
                });
                frm.refresh_field("cheque_to_print");

                frm.save();
            }
        });
    }
});
