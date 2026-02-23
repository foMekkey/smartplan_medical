import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ClassificationPriceList(Document):
    def validate(self):
        """Calculate discounted selling rates for all items."""
        for item in self.items:
            if item.standard_rate and item.selling_discount:
                item.discounted_rate = flt(item.standard_rate) * (
                    1 - flt(item.selling_discount) / 100
                )
            else:
                item.discounted_rate = flt(item.standard_rate)

    def before_save(self):
        """Validate date range."""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            frappe.throw(
                "تاريخ البدء يجب أن يكون قبل تاريخ الانتهاء"
                " (From Date must be before To Date)"
            )

    def on_submit(self):
        """Create/update ERPNext Price List and link to customers."""
        self._create_or_update_price_list()
        self._link_customers_to_price_list()

    def on_cancel(self):
        """Disable the Price List when CPL is cancelled."""
        pl_name = self._get_price_list_name()
        if frappe.db.exists("Price List", pl_name):
            frappe.db.set_value("Price List", pl_name, "enabled", 0)
            frappe.msgprint(
                f"تم تعطيل قائمة الأسعار: {pl_name}",
                alert=True,
                indicator="orange",
            )

    def _get_price_list_name(self):
        """Standard name for the auto-created Price List."""
        return f"قائمة أسعار - {self.classification}"

    def _create_or_update_price_list(self):
        """Create or update the ERPNext Price List + Item Prices."""
        pl_name = self._get_price_list_name()

        # Create Price List if not exists
        if not frappe.db.exists("Price List", pl_name):
            pl = frappe.new_doc("Price List")
            pl.price_list_name = pl_name
            pl.selling = 1
            pl.buying = 0
            pl.enabled = 1
            pl.currency = frappe.defaults.get_global_default("currency") or "EGP"
            pl.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Price List", pl_name, "enabled", 1)

        # Delete old Item Prices for this Price List (fresh sync)
        frappe.db.delete(
            "Item Price",
            {"price_list": pl_name, "selling": 1},
        )

        # Create new Item Prices from CPL items
        for item in self.items:
            ip = frappe.new_doc("Item Price")
            ip.item_code = item.item_code
            ip.price_list = pl_name
            ip.price_list_rate = flt(item.discounted_rate)
            ip.selling = 1
            ip.buying = 0
            ip.batch_no = item.batch_no or ""
            ip.valid_from = self.from_date
            ip.valid_upto = self.to_date
            ip.insert(ignore_permissions=True)

        frappe.db.commit()
        frappe.msgprint(
            f"تم إنشاء/تحديث قائمة الأسعار: {pl_name} ({len(self.items)} صنف)",
            alert=True,
            indicator="green",
        )

    def _link_customers_to_price_list(self):
        """Set default_price_list for all customers in this classification."""
        pl_name = self._get_price_list_name()
        customers = frappe.get_all(
            "Customer",
            filters={"custom_classification": self.classification},
            pluck="name",
        )

        for cust in customers:
            frappe.db.set_value("Customer", cust, "default_price_list", pl_name)

        frappe.db.commit()
        if customers:
            frappe.msgprint(
                f"تم ربط {len(customers)} عميل بقائمة الأسعار: {pl_name}",
                alert=True,
                indicator="blue",
            )
