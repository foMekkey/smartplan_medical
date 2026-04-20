frappe.ui.form.on("Sales Order", {
    customer(frm) {
        load_customer_balance(frm);
        show_customer_invoices_summary(frm);
    },
    
    refresh(frm) {
        load_customer_balance(frm);
        
        // زرار طباعة بس لو submitted
        if (frm.doc.docstatus === 1 && !frm.is_new()) {
            frm.add_custom_button(__('طباعة الفاتورة والتسليم'), function() {
                show_print_dialog(frm);
            }, __('Print'));
        }
    },
    
    onload(frm) {
        load_customer_balance(frm);
    },
    
    // بس بعد الـ Submit - مش Save عادي
    on_submit(frm) {
        setTimeout(() => {
            load_customer_balance(frm);
            frappe.show_alert({
                message: __('✅ تم تحديث رصيد العميل'),
                indicator: 'green'
            }, 3);
            
            // فتح dialog الطباعة بعد Submit
            show_print_dialog(frm);
        }, 800);
    },
    
    after_cancel(frm) {
        setTimeout(() => {
            load_customer_balance(frm);
            frappe.show_alert({
                message: __('✅ تم تحديث رصيد العميل بعد الإلغاء'),
                indicator: 'orange'
            }, 3);
        }, 500);
    }
});

function load_customer_balance(frm) {
    if (!frm.doc.customer) return;
    
    frappe.call({
        method: "erpnext.accounts.utils.get_balance_on",
        args: {
            party_type: "Customer",
            party: frm.doc.customer,
            company: frm.doc.company
        },
        callback(r) {
            let balance = r.message || 0;
            frm.set_value("custom_customer_balance", balance);
            
            setTimeout(() => {
                apply_balance_color(frm, balance);
            }, 300);
        }
    });
}

function apply_balance_color(frm, balance) {
    let field = frm.fields_dict.custom_customer_balance;
    if (!field) return;
    
    let input = field.$wrapper.find("input");
    let wrapper = field.$wrapper;
    
    wrapper.removeClass("text-danger text-success");
    
    if (balance > 0) {
        input.css({
            "color": "#d9534f",
            "font-weight": "bold",
            "background-color": "#fff5f5"
        });
        wrapper.addClass("text-danger");
    } else if (balance < 0) {
        input.css({
            "color": "#000",
            "font-weight": "normal",
            "background-color": "#fff"
        });
    } else {
        input.css({
            "color": "#000",
            "font-weight": "normal",
            "background-color": "#fff"
        });
    }
}

function show_customer_invoices_summary(frm) {
    if (!frm.doc.customer) return;
    
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Sales Order",
            filters: {
                customer: frm.doc.customer,
                docstatus: 1,
                outstanding_amount: [">", 0]
            },
            fields: [
                "name", 
                "posting_date", 
                "grand_total", 
                "outstanding_amount",
                "paid_amount",
                "due_date",
                "status"
            ],
            order_by: "posting_date desc",
            limit: 100
        },
        callback(r) {
            if (!r.message || r.message.length === 0) {
                frappe.show_alert({
                    message: __('✅ العميل ليس عليه أي فواتير مستحقة'),
                    indicator: 'green'
                }, 5);
                return;
            }
            
            let invoices = r.message;
            
            let promises = invoices.map(inv => {
                return new Promise((resolve) => {
                    frappe.db.get_doc('Sales Order', inv.name)
                        .then(doc => {
                            let sales_person = '-';
                            if (doc.sales_team && doc.sales_team.length > 0) {
                                sales_person = doc.sales_team[0].sales_person;
                            }
                            inv.sales_person = sales_person;
                            resolve(inv);
                        })
                        .catch(() => {
                            inv.sales_person = '-';
                            resolve(inv);
                        });
                });
            });
            
            Promise.all(promises).then(invoices_with_sales_person => {
                let total_outstanding = 0;
                let total_invoices = invoices_with_sales_person.length;
                let overdue_invoices = 0;
                
                invoices_with_sales_person.forEach(inv => {
                    total_outstanding += inv.outstanding_amount;
                    if (inv.due_date && frappe.datetime.get_diff(frappe.datetime.get_today(), inv.due_date) > 0) {
                        overdue_invoices++;
                    } else if (!inv.due_date) {
                        let days_since_posting = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.posting_date);
                        if (days_since_posting > 30) {
                            overdue_invoices++;
                        }
                    }
                });
                
                show_invoices_dialog(frm, invoices_with_sales_person, total_outstanding, total_invoices, overdue_invoices);
            });
        }
    });
}

function show_invoices_dialog(frm, invoices, total_outstanding, total_invoices, overdue_invoices) {
    let html = `
        <style>
            .customer-summary-container {
                font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                direction: rtl;
                background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
                padding: 10px;
                border-radius: 12px;
            }
            .summary-header {
                background: linear-gradient(135deg, #0d47a1 0%, #1976d2 50%, #42a5f5 100%);
                color: white;
                padding: 25px;
                border-radius: 12px 12px 0 0;
                margin: -15px -15px 25px -15px;
                box-shadow: 0 4px 12px rgba(13, 71, 161, 0.3);
                position: relative;
            }
            .summary-header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%23ffffff" fill-opacity="0.1" d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,144C960,149,1056,139,1152,128C1248,117,1344,107,1392,101.3L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>');
                background-size: cover;
                border-radius: 12px 12px 0 0;
            }
            .summary-header h3 {
                margin: 0 0 12px 0;
                font-size: 24px;
                font-weight: bold;
                position: relative;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .summary-header .customer-name {
                font-size: 19px;
                opacity: 0.95;
                margin-bottom: 8px;
                position: relative;
                font-weight: 600;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
                margin: 25px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid transparent;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                position: relative;
                overflow: hidden;
            }
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, transparent, currentColor, transparent);
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 16px rgba(0,0,0,0.12);
            }
            .stat-card.danger {
                border-color: #f44336;
                color: #f44336;
            }
            .stat-card.danger::before {
                background: linear-gradient(90deg, transparent, #f44336, transparent);
            }
            .stat-card.warning {
                border-color: #ff9800;
                color: #ff9800;
            }
            .stat-card.warning::before {
                background: linear-gradient(90deg, transparent, #ff9800, transparent);
            }
            .stat-card.success {
                border-color: #4caf50;
                color: #4caf50;
            }
            .stat-card.success::before {
                background: linear-gradient(90deg, transparent, #4caf50, transparent);
            }
            .stat-icon {
                font-size: 32px;
                margin-bottom: 8px;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }
            .stat-number {
                font-size: 32px;
                font-weight: bold;
                margin: 8px 0;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            .stat-label {
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            .invoices-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border-radius: 12px;
                overflow: hidden;
            }
            .invoices-table thead {
                background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%);
                color: white;
            }
            .invoices-table th {
                padding: 14px 10px;
                text-align: center;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .invoices-table td {
                padding: 12px 10px;
                text-align: center;
                border-bottom: 1px solid #e0e0e0;
                font-size: 13px;
                background: white;
            }
            .invoices-table tbody tr {
                transition: all 0.2s ease;
            }
            .invoices-table tbody tr:hover {
                background: #f0f7ff !important;
                transform: scale(1.01);
            }
            .invoices-table tbody tr:last-child td {
                border-bottom: none;
            }
            .invoice-link {
                color: #1976d2;
                font-weight: bold;
                text-decoration: none;
                transition: all 0.2s;
            }
            .invoice-link:hover {
                color: #0d47a1;
                text-decoration: underline;
            }
            .status-badge {
                padding: 5px 12px;
                border-radius: 16px;
                font-size: 11px;
                font-weight: bold;
                display: inline-block;
                text-transform: uppercase;
                letter-spacing: 0.3px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .status-overdue {
                background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
                color: white;
            }
            .status-unpaid {
                background: linear-gradient(135deg, #f57c00 0%, #ff9800 100%);
                color: white;
            }
            .status-partial {
                background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%);
                color: white;
            }
            .amount-outstanding {
                color: #d32f2f;
                font-weight: bold;
                font-size: 14px;
            }
            .amount-paid {
                color: #388e3c;
                font-weight: 600;
            }
            .section-title {
                font-size: 17px;
                font-weight: bold;
                color: #1976d2;
                margin: 25px 0 15px 0;
                padding: 12px 15px;
                background: linear-gradient(90deg, #e3f2fd 0%, transparent 100%);
                border-right: 4px solid #1976d2;
                border-radius: 4px;
            }
            .table-footer {
                background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%) !important;
                font-weight: bold;
                font-size: 15px;
                box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
            }
            .copyright {
                text-align: center;
                margin-top: 20px;
                padding: 12px 15px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                border-radius: 10px;
                color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(255, 215, 0, 0.3);
            }
            .copyright::before {
                content: '';
                position: absolute;
                top: -1px;
                left: -1px;
                right: -1px;
                bottom: -1px;
                background: linear-gradient(45deg, #ffd700, #ffed4e, #ffd700, #ffed4e);
                background-size: 400% 400%;
                border-radius: 10px;
                z-index: -1;
                animation: borderGlow 3s ease infinite;
                opacity: 0.4;
            }
            @keyframes borderGlow {
                0%, 100% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
            }
            .copyright::after {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
                animation: shine 3s infinite;
            }
            @keyframes shine {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            .copyright-content {
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            .copyright-logo {
                font-size: 18px;
                animation: float 3s ease-in-out infinite;
            }
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-3px); }
            }
            .copyright-brand {
                font-size: 16px;
                font-weight: 900;
                background: linear-gradient(135deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 2px;
                animation: glow 2s ease-in-out infinite;
            }
            @keyframes glow {
                0%, 100% { filter: brightness(1); }
                50% { filter: brightness(1.2); }
            }
            .copyright-text {
                font-size: 11px;
                color: #e0e0e0;
                font-weight: 500;
            }
            .copyright-year {
                color: #b0b0b0;
                font-size: 10px;
            }
            .row-overdue {
                background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 100%) !important;
                border-right: 4px solid #f44336 !important;
            }
            .sales-person-badge {
                background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 100%);
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                display: inline-block;
                box-shadow: 0 2px 4px rgba(74, 20, 140, 0.3);
            }
        </style>
        
        <div class="customer-summary-container">
            <div class="summary-header">
                <h3>📊 ملخص حساب العميل</h3>
                <div class="customer-name">🏢 ${frm.doc.customer}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card danger">
                    <div class="stat-icon">💰</div>
                    <div class="stat-label">إجمالي المستحق</div>
                    <div class="stat-number">${format_currency(total_outstanding)}</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">📝</div>
                    <div class="stat-label">عدد الفواتير المستحقة</div>
                    <div class="stat-number">${total_invoices}</div>
                </div>
                <div class="stat-card ${overdue_invoices > 0 ? 'danger' : 'success'}">
                    <div class="stat-icon">${overdue_invoices > 0 ? '⚠️' : '✅'}</div>
                    <div class="stat-label">فواتير متأخرة</div>
                    <div class="stat-number">${overdue_invoices}</div>
                </div>
            </div>
            
            <div class="section-title">📋 تفاصيل الفواتير المستحقة</div>
            
            <table class="invoices-table">
                <thead>
                    <tr>
                        <th>رقم الفاتورة</th>
                        <th>التاريخ</th>
                        <th>تاريخ الاستحقاق</th>
                        <th>المندوب</th>
                        <th>الإجمالي</th>
                        <th>المدفوع</th>
                        <th>المتبقي</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    invoices.forEach(inv => {
        let is_overdue = false;
        let days_overdue = 0;
        
        if (inv.due_date) {
            days_overdue = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.due_date);
            is_overdue = days_overdue > 0;
        } else {
            let days_since_posting = frappe.datetime.get_diff(frappe.datetime.get_today(), inv.posting_date);
            is_overdue = days_since_posting > 30;
            days_overdue = days_since_posting;
        }
        
        let status_html = '';
        if (is_overdue) {
            status_html = `<span class="status-badge status-overdue">متأخر ${days_overdue} يوم</span>`;
        } else if (inv.paid_amount > 0) {
            status_html = `<span class="status-badge status-partial">مدفوع جزئياً</span>`;
        } else {
            status_html = `<span class="status-badge status-unpaid">غير مدفوع</span>`;
        }
        
        let sales_person_html = inv.sales_person && inv.sales_person !== '-' 
            ? `<span class="sales-person-badge">👤 ${inv.sales_person}</span>` 
            : '<span style="color: #999;">-</span>';
        
        html += `
            <tr class="${is_overdue ? 'row-overdue' : ''}">
                <td>
                    <a href="/app/sales-invoice/${inv.name}" target="_blank" class="invoice-link">
                        ${inv.name}
                    </a>
                </td>
                <td>${frappe.datetime.str_to_user(inv.posting_date)}</td>
                <td>${inv.due_date ? frappe.datetime.str_to_user(inv.due_date) : '<span style="color: #999;">-</span>'}</td>
                <td>${sales_person_html}</td>
                <td>${format_currency(inv.grand_total)}</td>
                <td class="amount-paid">${format_currency(inv.paid_amount || 0)}</td>
                <td class="amount-outstanding">${format_currency(inv.outstanding_amount)}</td>
                <td>${status_html}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
                <tfoot>
                    <tr class="table-footer">
                        <td colspan="6" style="text-align: right; padding: 15px;">
                            <strong>الإجمالي المستحق:</strong>
                        </td>
                        <td class="amount-outstanding" style="font-size: 17px;">
                            <strong>${format_currency(total_outstanding)}</strong>
                        </td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
            
            <div class="copyright">
                <div class="copyright-content">
                    <span class="copyright-logo">🚀</span>
                    <span class="copyright-brand">SPS</span>
                    <span class="copyright-text">Smart Plan Solutions</span>
                    <span class="copyright-year">© ${new Date().getFullYear()}</span>
                </div>
            </div>
        </div>
    `;
    
    let dialog = frappe.msgprint({
        title: `💼 حساب العميل - ${frm.doc.customer}`,
        message: html,
        indicator: total_outstanding > 0 ? 'red' : 'green',
        wide: true
    });
    
    setTimeout(() => {
        dialog.$wrapper.find('.modal-dialog').css('max-width', '1300px');
    }, 100);
}

// Dialog الطباعة
function show_print_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('طباعة المستندات'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'print_options',
                options: `
                    <div style="padding: 20px; text-align: center;">
                        <h4 style="margin-bottom: 20px;">✅ تم حفظ الفاتورة بنجاح!</h4>
                        <p style="margin-bottom: 20px;">هل تريد طباعة المستندات؟</p>
                    </div>
                `
            },
            {
                fieldtype: 'Check',
                fieldname: 'print_invoice',
                label: 'طباعة الفاتورة',
                default: 1
            },
            {
                fieldtype: 'Check',
                fieldname: 'print_delivery',
                label: 'طباعة إيصال التسليم',
                default: 1,
                depends_on: 'eval:doc.update_stock'
            }
        ],
        primary_action_label: __('طباعة'),
        primary_action(values) {
            if (values.print_invoice) {
                frappe.utils.print(
                    frm.doc.doctype,
                    frm.doc.name,
                    null, // print format - null يستخدم الافتراضي
                    null, // letterhead
                    'ar'  // language
                );
            }
            
            if (values.print_delivery && frm.doc.update_stock) {
                // طباعة كإيصال تسليم
                setTimeout(() => {
                    frappe.utils.print(
                        frm.doc.doctype,
                        frm.doc.name,
                        'Delivery Note Style', // أو اسم Print Format مخصص
                        null,
                        'ar'
                    );
                }, 1000);
            }
            
            d.hide();
        },
        secondary_action_label: __('إلغاء')
    });
    
    d.show();
}

function format_currency(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
}

frappe.ui.form.on("Sales Order", {
    custom_customer_balance(frm) {
        if (frm.doc.custom_customer_balance) {
            apply_balance_color(frm, frm.doc.custom_customer_balance);
        }
    }
});