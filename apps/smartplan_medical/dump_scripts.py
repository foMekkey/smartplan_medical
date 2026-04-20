import frappe
from frappe.utils import add_to_date
import os

frappe.init(site="reunion.eg-smartplan.solutions")
frappe.connect()

dump_dir = "/home/frappe/frappe-bench/apps/smartplan_medical/scripts_dump"
os.makedirs(dump_dir, exist_ok=True)

# Client scripts
for doc in frappe.get_all("Client Script", filters={"dt": "Sales Order"}, fields=["name", "script"]):
    safe_name = doc.name.replace(" ", "_").replace("/", "_")
    with open(f"{dump_dir}/CLIENT_{safe_name}.js", "w") as f:
        f.write(doc.script or "")

# Server scripts
for doc in frappe.get_all("Server Script", filters={"name": ["like", "%Reservation%"]}, fields=["name", "script"]):
    safe_name = doc.name.replace(" ", "_").replace("/", "_")
    with open(f"{dump_dir}/SERVER_{safe_name}.py", "w") as f:
        f.write(doc.script or "")
