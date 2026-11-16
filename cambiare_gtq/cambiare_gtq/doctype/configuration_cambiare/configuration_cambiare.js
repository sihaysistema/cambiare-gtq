// Copyright (c) 2019, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on("Configuration Cambiare", {
  refresh: function (frm) {
    frm.set_intro(
      __(
        "The default exchange rate is USD to GTQ and GTQ to USD. So there is no need to configure it in this section."
      )
    );

    frm.add_custom_button(__("Fetch Today's Rates"), function () {
      frappe.call({
        method: "cambiare_gtq.api_cambiare.preparar_peticion_banguat",
        args: { opt: "6" },
        freeze: true,
        freeze_message: __("Fetching today's exchange rates from Banco de Guatemala..."),
        callback: function (r) {
          if (!r.exc) {
            frappe.show_alert({
              message: __("Exchange rates saved"),
              indicator: "green",
            });
          }
        },
      });
    });

    frm.add_custom_button(__("Backfill Exchange Rates"), function () {
      frappe.prompt(
        [
          {
            fieldname: "from_date",
            fieldtype: "Date",
            label: __("From Date"),
            reqd: 1,
          },
          {
            fieldname: "to_date",
            fieldtype: "Date",
            label: __("To Date"),
            reqd: 1,
            default: frappe.datetime.get_today(),
          },
          {
            fieldname: "currency",
            fieldtype: "Data",
            label: __("Currency"),
            description: __(
              "ISO code such as EUR. Leave empty to fetch USD and the currencies selected below."
            ),
          },
        ],
        function (values) {
          frappe.call({
            method: "cambiare_gtq.exchange_rates.backfill_exchange_rates",
            args: values,
            freeze: true,
            freeze_message: __("Fetching exchange rates from Banco de Guatemala..."),
            callback: function (r) {
              if (!r.exc) {
                frappe.show_alert({
                  message: __("Exchange rates saved"),
                  indicator: "green",
                });
              }
            },
          });
        },
        __("Backfill Exchange Rates"),
        __("Fetch")
      );
    });
  },
});

frappe.ui.form.on("Available Currencies", {
  currency: function (frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const parts = (row.currency || "").split("-");
    if (parts.length >= 3) {
      frappe.model.set_value(cdt, cdn, "code", parts[parts.length - 1].trim());
    }
  },
});
