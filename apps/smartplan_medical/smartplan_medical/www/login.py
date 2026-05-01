# SmartPlan Medical Login Page Context
# Delegates to Frappe's login.py for all context
import frappe
from frappe.www.login import get_context as _frappe_login_context

no_cache = 1

def get_context(context):
    return _frappe_login_context(context)
