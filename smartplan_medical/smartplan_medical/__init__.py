import frappe


def reload_warehouse_dispatch():
	"""Utility used from bench execute to reload the Warehouse Dispatch DocType after JSON edits."""
	frappe.reload_doc('smartplan_medical', 'doctype', 'warehouse_dispatch', force=True)
	return "reloaded"
