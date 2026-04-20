# Copyright (c) 2026, Smartplan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "delivery_rep",
            "label": _("مندوب التوصيل"),
            "fieldtype": "Link",
            "options": "Delivery Representative",
            "width": 150
        },
        {
            "fieldname": "rep_name",
            "label": _("اسم المندوب"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "dispatch_count",
            "label": _("عدد الصرفيات"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "dispatch_amount",
            "label": _("قيمة الصرف"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "collection_count",
            "label": _("عدد التحصيلات"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "collection_amount",
            "label": _("قيمة التحصيل"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "difference",
            "label": _("الفرق"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "collection_rate",
            "label": _("نسبة التحصيل %"),
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "fieldname": "pending_amount",
            "label": _("المبلغ المعلق"),
            "fieldtype": "Currency",
            "width": 120
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    # بيانات الصرف
    dispatch_data = frappe.db.sql("""
        SELECT 
            wd.delivery_representative as delivery_rep,
            dr.representative_name as rep_name,
            COUNT(DISTINCT wd.name) as dispatch_count,
            SUM(wd.total_amount) as dispatch_amount
        FROM `tabWarehouse Dispatch` wd
        LEFT JOIN `tabDelivery Representative` dr ON wd.delivery_representative = dr.name
        WHERE wd.docstatus = 1
            {conditions}
        GROUP BY wd.delivery_representative
    """.format(conditions=conditions.replace("dc.", "wd.").replace("collection_date", "posting_date")), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "delivery_rep": filters.get("delivery_rep")
    }, as_dict=True)
    
    # بيانات التحصيل
    collection_data = frappe.db.sql("""
        SELECT 
            dc.delivery_representative as delivery_rep,
            COUNT(DISTINCT dc.name) as collection_count,
            SUM(dc.collected_amount) as collection_amount
        FROM `tabDelivery Collection` dc
        WHERE dc.docstatus = 1
            {conditions}
        GROUP BY dc.delivery_representative
    """.format(conditions=conditions), {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "delivery_rep": filters.get("delivery_rep")
    }, as_dict=True)
    
    # دمج البيانات
    collection_map = {d["delivery_rep"]: d for d in collection_data}
    
    result = []
    for row in dispatch_data:
        coll = collection_map.get(row["delivery_rep"], {})
        
        row["collection_count"] = coll.get("collection_count", 0)
        row["collection_amount"] = flt(coll.get("collection_amount", 0))
        row["difference"] = flt(row["dispatch_amount"]) - flt(row["collection_amount"])
        row["collection_rate"] = (flt(row["collection_amount"]) / flt(row["dispatch_amount"]) * 100) if row["dispatch_amount"] else 0
        row["pending_amount"] = max(0, row["difference"])
        
        result.append(row)
    
    # إضافة تحصيلات بدون صرف
    for rep, coll in collection_map.items():
        if not any(r["delivery_rep"] == rep for r in result):
            result.append({
                "delivery_rep": rep,
                "rep_name": frappe.db.get_value("Delivery Representative", rep, "representative_name"),
                "dispatch_count": 0,
                "dispatch_amount": 0,
                "collection_count": coll.get("collection_count", 0),
                "collection_amount": flt(coll.get("collection_amount", 0)),
                "difference": -flt(coll.get("collection_amount", 0)),
                "collection_rate": 100,
                "pending_amount": 0
            })
    
    return sorted(result, key=lambda x: x.get("dispatch_amount", 0), reverse=True)


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND dc.posting_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND dc.posting_date <= %(to_date)s")
    
    if filters.get("delivery_rep"):
        conditions.append("AND dc.delivery_representative = %(delivery_rep)s")
    
    return " ".join(conditions)


def get_chart(data):
    if not data:
        return None
    
    labels = [d.get("rep_name", d.get("delivery_rep", "")) for d in data[:10]]
    dispatch_values = [d.get("dispatch_amount", 0) for d in data[:10]]
    collection_values = [d.get("collection_amount", 0) for d in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("الصرف"), "values": dispatch_values},
                {"name": _("التحصيل"), "values": collection_values}
            ]
        },
        "type": "bar",
        "colors": ["#7cd6fd", "#5e64ff"]
    }


def get_summary(data):
    total_dispatch = sum(d.get("dispatch_amount", 0) for d in data)
    total_collection = sum(d.get("collection_amount", 0) for d in data)
    total_pending = sum(d.get("pending_amount", 0) for d in data)
    overall_rate = (total_collection / total_dispatch * 100) if total_dispatch else 0
    
    return [
        {
            "value": total_dispatch,
            "indicator": "Blue",
            "label": _("إجمالي الصرف"),
            "datatype": "Currency"
        },
        {
            "value": total_collection,
            "indicator": "Green",
            "label": _("إجمالي التحصيل"),
            "datatype": "Currency"
        },
        {
            "value": total_pending,
            "indicator": "Orange",
            "label": _("المعلق"),
            "datatype": "Currency"
        },
        {
            "value": overall_rate,
            "indicator": "Green" if overall_rate >= 80 else "Orange",
            "label": _("نسبة التحصيل الكلية"),
            "datatype": "Percent"
        }
    ]
