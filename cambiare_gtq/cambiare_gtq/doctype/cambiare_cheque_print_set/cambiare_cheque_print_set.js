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
            callback: function (r) {
                frm.doc.cheque_to_print = []
                frm.refresh_field("cheque_to_print");

                r.message.forEach(element => {
                    frm.add_child("cheque_to_print", {
                        transaction_id: element.transaction_id,
                        cheque_no: element.cheque_no,
                        amount: element.amount,
                        party_type: element.party_type,
                        third_party: element.third_party,
                        id: element.id
                    });
                });
                frm.refresh_field("cheque_to_print");

                frm.save();
            }
        });
    },
    refresh: function (frm) {
        frm.add_custom_button(__('TEST'), () => {
            let data_je = [];
            let data_pe = [];

            frm.doc.cheque_to_print.forEach(element => {
                if (element.transaction_id == 'Journal Entry') {
                    data_je.push(element.id);
                }

                if (element.transaction_id == 'Payment Entry') {
                    data_pe.push(element.id);
                }
            });

            console.log(data_je, data_pe);



            const dialog = new frappe.ui.Dialog({
                title: __('Print Documents'),
                fields: [{
                    'fieldtype': 'Check',
                    'label': __('With Letterhead'),
                    'fieldname': 'with_letterhead'
                },
                {
                    'fieldtype': 'Select',
                    'label': __('Print Format'),
                    'fieldname': 'print_sel',
                    options: frappe.meta.get_print_formats(frm.doc.doctype)
                }]
            });

            dialog.set_primary_action(__('Print'), args => {
                if (!args) return;

                // Primero se imprimen los cheques para payment entry
                for (const iterator of ['Payment Entry', 'Journal Entry']) {
                    console.log(iterator)

                    const default_print_format = 'Standard'; // frappe.get_meta(iterator).default_print_format;
                    const with_letterhead = args.with_letterhead ? 1 : 0;
                    const print_format = args.print_sel ? args.print_sel : 'Standard'; //default_print_format;
                    const json_string = JSON.stringify(data_pe);

                    const w = window.open('/api/method/frappe.utils.print_format.download_multi_pdf?' +
                        'doctype=' + encodeURIComponent(iterator) +
                        '&name=' + encodeURIComponent(json_string) +
                        '&format=' + encodeURIComponent(print_format) +
                        '&no_letterhead=' + (with_letterhead ? '0' : '1'));
                    if (!w) {
                        frappe.msgprint(__('Please enable pop-ups'));
                        return;
                    }

                }
            });

            dialog.show();


        }).addClass('btn btn-primary');
    }
});
