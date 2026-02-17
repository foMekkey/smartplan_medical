import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ClassificationPriceList(Document):
    def validate(self):
        """Calculate discounted rates for all items."""
        for item in self.items:
            if item.standard_rate and item.discount_percentage:
                item.discounted_rate = flt(item.standard_rate) * (
                    1 - flt(item.discount_percentage) / 100
                )
            else:
                item.discounted_rate = flt(item.standard_rate)

    def before_save(self):
        """Validate date range."""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            frappe.throw("تاريخ البدء يجب أن يكون قبل تاريخ الانتهاء (From Date must be before To Date)")
