frappe.pages["currency-converter"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Currency Converter"),
    single_column: true,
  });
  const $main = $(page.main || page.body || wrapper);
  $main.html(
    '<div class="cambiare-converter" style="max-width: 36rem;">' +
      field("amount", __("Amount"), "number") +
      field("from_currency", __("From Currency"), "text") +
      field("to_currency", __("To Currency"), "text") +
      '<div class="form-group"><label>' + __("Method") + "</label>" +
      '<select class="form-control method">' +
      '<option value="daily">' + __("Daily Rate") + "</option>" +
      '<option value="average">' + __("Average Rate") + "</option>" +
      "</select></div>" +
      field("date", __("Date"), "date") +
      field("from_date", __("From Date"), "date") +
      field("to_date", __("To Date"), "date") +
      '<div class="checkbox"><label><input type="checkbox" class="fetch" checked> ' +
      __("Fetch if missing") + "</label></div>" +
      '<button class="btn btn-primary convert">' + __("Convert") + "</button>" +
      '<p class="stamp text-muted" style="margin-top: 1rem;"></p>' +
      '<pre class="result"></pre>' +
      "</div>"
  );

  $main.find(".convert").on("click", function () {
    frappe.call({
      method: "cambiare_gtq.convert.convert",
      args: {
        amount: $main.find(".amount").val(),
        from_currency: ($main.find(".from_currency").val() || "").toUpperCase(),
        to_currency: ($main.find(".to_currency").val() || "").toUpperCase(),
        date: $main.find(".date").val(),
        from_date: $main.find(".from_date").val(),
        to_date: $main.find(".to_date").val(),
        method: $main.find(".method").val(),
        fetch_if_missing: $main.find(".fetch").is(":checked") ? 1 : 0,
      },
      freeze: true,
      callback: function (response) {
        var message = response.message || {};
        var stamp = message.rate_timestamp_utc;
        if (!stamp && message.rate_timestamp_utc_from) {
          stamp = message.rate_timestamp_utc_from;
          if (message.rate_timestamp_utc_to && message.rate_timestamp_utc_to !== stamp) {
            stamp += " – " + message.rate_timestamp_utc_to;
          }
        }
        $main.find(".stamp").text(stamp ? __("Rate Timestamp (UTC)") + ": " + stamp : "");
        $main.find(".result").text(JSON.stringify(message, null, 2));
      },
    });
  });
};

function field(name, label, type) {
  return (
    '<div class="form-group"><label>' + label + "</label>" +
    '<input class="form-control ' + name + '" type="' + type + '"></div>'
  );
}
