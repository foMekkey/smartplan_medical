app_name = "smartplan_medical"
app_version = "1.0.0"
app_title = "Smartplan Medical"
app_publisher = "SmartPlan"
app_description = "Medical and Pharmaceutical Management System"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@eg-smartplan.solutions"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/smartplan_medical/css/smartplan_medical.css"
# app_include_js = "/assets/smartplan_medical/js/smartplan_medical.js"

# include js, css files in header of web template
# web_include_css = "/assets/smartplan_medical/css/smartplan_medical.css"
# web_include_js = "/assets/smartplan_medical/js/smartplan_medical.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "smartplan_medical/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Order": "public/js/sales_order_custom.js"
}
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

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "smartplan_medical.install.before_install"
# after_install = "smartplan_medical.install.after_install"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "smartplan_medical.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Order": {
        "before_save": "smartplan_medical.sales_order_events.before_save",
        "after_save": "smartplan_medical.sales_order_events.after_save",
        "on_cancel": "smartplan_medical.sales_order_events.after_cancel",
        "before_insert": "smartplan_medical.sales_order_events.before_insert",
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "smartplan_medical.smartplan_medical.tasks.check_expiring_batches",
        "smartplan_medical.smartplan_medical.tasks.escalate_pending_approvals"
    ],
    "hourly": [
        "smartplan_medical.smartplan_medical.tasks.retry_failed_processes"
    ]
}

# Document Events
# ---------------
doc_events = {
    "Warehouse Dispatch": {
        # "on_submit": "smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log.create_process_log_on_dispatch",
        "validate": "smartplan_medical.smartplan_medical.utils.validate_dispatch"
    },
    "Delivery Collection": {
        # "on_submit": "smartplan_medical.smartplan_medical.doctype.pharma_process_log.pharma_process_log.create_process_log_on_collection",
        "validate": "smartplan_medical.smartplan_medical.utils.validate_collection"
    },
    "Tele Sales Order": {
        "validate": "smartplan_medical.smartplan_medical.utils.validate_tele_sales_order"
    }
}

# Testing
# -------

# before_tests = "smartplan_medical.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "smartplan_medical.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "smartplan_medical.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"smartplan_medical.auth.validate"
# ]
