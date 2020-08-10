# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

from cambiare_gtq.fixtures import fill_fixtures

app_name = "cambiare_gtq"
app_title = "Cambiare GTQ"
app_publisher = "Si Hay Sistema"
app_description = "Currency exchange API sourcing data from Guatemala's Central Bank webservice"
app_icon = "octicon octicon-graph"
app_color = "#27AE60"
app_email = "m.monroyc22@gmail.com"
app_license = "GNU General Public License v3.0"

# This needs to be enabled and bench restarted before running bench export-fixtures such that the Custom Fields listed below can be exported.
fixtures = fill_fixtures()
# [
#     {"dt": "Translation", "filters": [
#         [
#             "source_name", "in", [
#                 "Could not create USD to GTQ exchange rate, please try generating GTQ manually",
#             ]
#         ]
#     ]
#     }
# ]
# '''
# fixtures = [
#     {"dt": "Custom Field", "filters": [
#         [
#             "name", "in", [
#                 "Currency Exchange-validity_date_ranges",
#                 "Currency Exchange-valid_to",
#                 "Currency Exchange-col_break",
#                 "Currency Exchange-valid_from"
#             ]
#         ]
#     ]
#     }
# ]
# '''
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cambiare_gtq/css/cambiare_gtq.css"
# app_include_js = "/assets/cambiare_gtq/js/cambiare_gtq.js"

# include js, css files in header of web template
# web_include_css = "/assets/cambiare_gtq/css/cambiare_gtq.css"
# web_include_js = "/assets/cambiare_gtq/js/cambiare_gtq.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "cambiare_gtq.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "cambiare_gtq.install.before_install"
# after_install = "cambiare_gtq.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cambiare_gtq.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    # Se ejecuta cada 4 minuts
    # "all": [
    # 	"cambiare_gtq.tasks.all"
    # ],
    # Se ejecuta cada dia 00:00
    "daily": [
        "cambiare_gtq.task.daily"
    ],
    # Se ejecuta a cada hora
    "hourly": [
        "cambiare_gtq.task.hourly"
    ],
    # Cron linux especificacion freq
    # "cron": {
    # 	# Cada minuto
    # 	"0/01 * * * *": [
    # 		"cambiare_gtq.task.test"
    # 	]
    # },
    # Se ejecuta acada semana
    "weekly": [
        "cambiare_gtq.task.weekly"
    ],
    # # Se ejecuta cada mes
    "monthly": [
        "cambiare_gtq.task.monthly"
    ]
}

# Testing
# -------

# before_tests = "cambiare_gtq.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "cambiare_gtq.event.get_events"
# }

