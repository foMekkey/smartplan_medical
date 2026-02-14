# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class CashDenomination(Document):
    def validate(self):
        self.total = flt(self.denomination_value) * flt(self.count)
