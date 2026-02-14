/**
 * Customer Custom Script
 * - Filter City dropdown by selected Governorate
 * - Clear city when governorate changes
 */
frappe.ui.form.on("Customer", {
    refresh(frm) {
        // Filter city by selected governorate
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate,
                    },
                };
            }
            return {};
        });
    },

    setup(frm) {
        // Also set filter on setup for initial load
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate,
                    },
                };
            }
            return {};
        });
    },

    custom_governorate(frm) {
        // Clear city when governorate changes
        frm.set_value("custom_city", "");

        // Re-apply filter for new governorate
        frm.set_query("custom_city", function () {
            if (frm.doc.custom_governorate) {
                return {
                    filters: {
                        governorate: frm.doc.custom_governorate,
                    },
                };
            }
            return {};
        });
    },
});
