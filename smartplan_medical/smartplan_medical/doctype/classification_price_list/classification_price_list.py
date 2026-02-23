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
        """Create/update ERPNext Price Lists (selling + buying) and link customers."""
        self._create_or_update_selling_price_list()
        self._create_or_update_buying_price_list()
        self._link_customers_to_price_list()

    def on_cancel(self):
        """Disable both Price Lists when CPL is cancelled."""
        for pl_name in [self._get_selling_pl_name(), self._get_buying_pl_name()]:
            if frappe.db.exists("Price List", pl_name):
                frappe.db.set_value("Price List", pl_name, "enabled", 0)
        frappe.msgprint(
            "تم تعطيل قوائم الأسعار (بيع + شراء)",
            alert=True,
            indicator="orange",
        )

    # ---- Name helpers ----
    def _get_selling_pl_name(self):
        return f"قائمة أسعار بيع - {self.classification}"

    def _get_buying_pl_name(self):
        return f"قائمة أسعار شراء - {self.classification}"

    # ---- Selling Price List ----
    def _create_or_update_selling_price_list(self):
        """Create/update selling Price List + Item Prices (discounted_rate)."""
        pl_name = self._get_selling_pl_name()
        self._ensure_price_list(pl_name, selling=1, buying=0)

        # Fresh sync — delete old, insert new
        frappe.db.delete("Item Price", {"price_list": pl_name, "selling": 1})

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
            f"✅ قائمة أسعار البيع: {pl_name} ({len(self.items)} صنف)",
            alert=True,
            indicator="green",
        )

    # ---- Buying Price List ----
    def _create_or_update_buying_price_list(self):
        """Create/update buying Price List + Item Prices (standard_rate = purchase rate)."""
        pl_name = self._get_buying_pl_name()
        self._ensure_price_list(pl_name, selling=0, buying=1)

        # Fresh sync
        frappe.db.delete("Item Price", {"price_list": pl_name, "buying": 1})

        for item in self.items:
            # Use purchase rate (standard_rate) with purchase discount applied
            purchase_rate = flt(item.standard_rate)
            if item.purchase_discount:
                purchase_rate = purchase_rate * (1 - flt(item.purchase_discount) / 100)

            ip = frappe.new_doc("Item Price")
            ip.item_code = item.item_code
            ip.price_list = pl_name
            ip.price_list_rate = purchase_rate
            ip.selling = 0
            ip.buying = 1
            ip.batch_no = item.batch_no or ""
            ip.valid_from = self.from_date
            ip.valid_upto = self.to_date
            ip.insert(ignore_permissions=True)

        frappe.db.commit()
        frappe.msgprint(
            f"✅ قائمة أسعار الشراء: {pl_name} ({len(self.items)} صنف)",
            alert=True,
            indicator="blue",
        )

    # ---- Helpers ----
    def _ensure_price_list(self, pl_name, selling=0, buying=0):
        """Create the Price List if it doesn't exist, or re-enable it."""
        if not frappe.db.exists("Price List", pl_name):
            pl = frappe.new_doc("Price List")
            pl.price_list_name = pl_name
            pl.selling = selling
            pl.buying = buying
            pl.enabled = 1
            pl.currency = frappe.defaults.get_global_default("currency") or "EGP"
            pl.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Price List", pl_name, "enabled", 1)

    def _link_customers_to_price_list(self):
        """Set default_price_list for all customers in this classification."""
        pl_name = self._get_selling_pl_name()
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
