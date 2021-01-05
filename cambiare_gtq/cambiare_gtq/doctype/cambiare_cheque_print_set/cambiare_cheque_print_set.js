// Copyright (c) 2021, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cambiare Cheque Print Set', {
    refresh: function(frm) {
        frm.add_custom_button(__("Get Cheque Payments"),
            function () {
            
            }).addClass("btn-primary");
    }
});
