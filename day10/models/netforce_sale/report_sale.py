# Copyright (c) 2012-2015 Netforce Co. Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from netforce.model import Model, fields, get_model
from netforce import database
from netforce.database import get_connection
from netforce.utils import get_file_path
import time
from datetime import *
from netforce.access import get_active_company
from . import utils


def get_past_months(num_months):
    months = []
    d = date.today()
    m = d.month
    y = d.year
    months.append((y, m))
    for i in range(num_months - 1):
        if (m > 1):
            m -= 1
        else:
            m = 12
            y -= 1
        months.append((y, m))
    return reversed(months)


def get_future_months(num_months):
    months = []
    d = date.today()
    m = d.month
    y = d.year
    months.append((y, m))
    for i in range(num_months - 1):
        if (m < 12):
            m += 1
        else:
            m = 1
            y += 1
        months.append((y, m))
    return months


class ReportSale(Model):
    _name = "report.sale"
    _store = False

    def sales_per_month(self, context={}):
        db = get_connection()
        company_id=get_active_company()
        res = db.query(
            "SELECT to_char(date,'YYYY-MM') AS month,SUM(amount_total_cur) as amount FROM sale_order as o WHERE state in ('confirmed','done') and o.company_id=%s GROUP BY month",company_id)
        amounts = {}
        for r in res:
            amounts[r.month] = r.amount
        data = []
        months = get_past_months(6)
        for y, m in months:
            amt = amounts.get("%d-%.2d" % (y, m), 0)
            d = date(year=y, month=m, day=1)
            data.append((d.strftime("%B"), amt))
        return {"value": data}

    def sales_per_product(self, context={}):
        db = get_connection()
        company_id=get_active_company()
        res = db.query(
            "SELECT p.name,SUM(l.amount_cur) as amount FROM sale_order_line l,sale_order o,product p WHERE p.id=l.product_id AND o.id=l.order_id AND o.state in ('confirmed','done') and o.company_id=%s GROUP BY p.name ORDER BY amount DESC",company_id)
        data = []
        for r in res[:5]:
            data.append((r.name, r.amount))
        amt = 0
        for r in res[5:]:
            amt += r.amount
        if amt > 0:
            data.append(("Other", amt))
        return {"value": data}

    def sales_per_product_categ(self, context={}):
        db = get_connection()
        company_id=get_active_company()
        res = db.query(
            "SELECT c.name,SUM(l.amount_cur) as amount FROM sale_order_line l,sale_order o,product p,product_categ c WHERE c.id=p.categ_id AND p.id=l.product_id AND o.id=l.order_id AND o.state in ('confirmed','done') and o.company_id=%s GROUP BY c.name ORDER BY amount DESC",company_id)
        data = []
        for r in res[:5]:
            data.append((r.name, r.amount))
        amt = 0
        for r in res[5:]:
            amt += r.amount
        if amt > 0:
            data.append(("Other", amt))
        return {"value": data}

    def sales_per_customer(self, context={}):
        db = get_connection()
        company_id=get_active_company()
        res = db.query(
            "SELECT c.name,SUM(o.amount_total) as amount FROM sale_order o,contact c WHERE c.id=o.contact_id AND o.state in ('confirmed','done') and o.company_id=%s GROUP BY c.name ORDER BY amount DESC",company_id)
        data = []
        for r in res[:5]:
            data.append((r.name, r.amount))
        amt = 0
        for r in res[5:]:
            amt += r.amount
        if amt > 0:
            data.append(("Other", amt))
        return {"value": data}

    def expected_revenue(self, context={}):
        data = []
        return {"value": []}

    def get_data_quot_form(self, context={}):
        company_id = get_active_company()
        comp = get_model("company").browse(company_id)
        obj_id = int(context["refer_id"])
        obj = get_model("sale.quot").browse(obj_id)
        dbname = database.get_active_db()
        settings = get_model("settings").browse(1)
        comp_name = comp.name
        comp_phone = settings.phone
        comp_fax = settings.fax
        comp_addr = settings.get_address_str()
        comp_tax_no = settings.tax_no
        contact = obj.contact_id
        cust_name = contact.name
        cust_fax = contact.fax
        cust_phone = contact.phone
        cust_tax_no = contact.tax_no
        cust_addr = contact.get_address_str()
        data = {
            "comp_name": comp_name,
            "comp_addr": comp_addr,
            "comp_phone": comp_phone or "-",
            "comp_fax": comp_fax or "-",
            "comp_tax_no": comp_tax_no or "-",
            "cust_name": cust_name,
            "cust_addr": cust_addr,
            "cust_phone": cust_phone or "-",
            "cust_fax": cust_fax or "-",
            "cust_tax_no": cust_tax_no or "-",
            "date": obj.date or "-",
            "number": obj.number or "-",
            "ref": obj.ref or "-",
            "exp_date": obj.exp_date or "-",
            "lines": [],
        }

        index = 0
        item = 0
        for line in obj.lines:
            if line.tax_id:
                break
            index += 1
        if not index:
            tax_rate = obj.lines[index].tax_id.rate
            tax_rate = tax_rate and tax_rate or "0"
        else:
            tax_rate = "0"

        if settings.logo:
            data["logo"] = get_file_path(settings.logo)
        for line in obj.lines:
            item += 1
            data["lines"].append({
                "item": item,
                "description": line.description,
                "image": get_file_path(line.product_id.image),
                "code": line.product_id.code or "-",
                "name": line.product_id.name or "-",
                "qty": line.qty,
                "uom": line.uom_id.name,
                "unit_price": line.unit_price,
                "discount": line.discount,
                "tax_rate": line.tax_id.rate,
                "amount": line.amount,
            })
        data.update({
            "amount_discount": obj.amount_discount,
            "amount_subtotal": obj.amount_subtotal,
            "amount_tax": obj.amount_tax,
            "amount_total": obj.amount_total,
            "amount_total_words": utils.num2word(obj.amount_total),
            "currency_code": obj.currency_id.code,
            "payment_terms": obj.payment_terms or "-",
            "other_info": obj.other_info or "-",
            "tax_rate": int(tax_rate),
            "qty_total": obj.qty_total,
            "owner": obj.user_id.name or "-"
        })
        return data

    def get_data_sale_form(self, context={}):
        obj_id = int(context["refer_id"])
        obj = get_model("sale.order").browse(obj_id)
        dbname = database.get_active_db()
        settings = get_model("settings").browse(1)
        comp_name = settings.name
        comp_phone = settings.phone
        comp_fax = settings.fax
        comp_addr = settings.get_address_str()
        comp_tax_no = settings.tax_no
        contact = obj.contact_id
        cust_name = contact.name
        cust_fax = contact.fax
        cust_phone = contact.phone
        cust_tax_no = contact.tax_no
        cust_addr = contact.get_address_str()
        data = {
            "comp_name": comp_name,
            "comp_addr": comp_addr,
            "comp_phone": comp_phone or "-",
            "comp_fax": comp_fax or "-",
            "comp_tax_no": comp_tax_no or "-",
            "cust_name": cust_name,
            "cust_addr": cust_addr,
            "cust_phone": cust_phone or "-",
            "cust_fax": cust_fax or "-",
            "cust_tax_no": cust_tax_no or "-",
            "date": obj.date or "-",
            "number": obj.number or "-",
            "ref": obj.ref or "-",
            "delivery_date": obj.delivery_date or "-",
            "ship_method": obj.ship_method_id.name or "-",
            "payment_terms": obj.payment_terms or "-",
            "lines": [],
        }

        index = 0
        item = 0
        for line in obj.lines:
            if line.tax_id:
                break
            index += 1
        if not index:
            tax_rate = obj.lines[index].tax_id.rate
            tax_rate = tax_rate and tax_rate or "0"
        else:
            tax_rate = "0"

        if settings.logo:
            data["logo"] = get_file_path(settings.logo)
        for line in obj.lines:
            item += 1
            data["lines"].append({
                "item": item,
                "code": line.product_id.code,
                "name": line.product_id.name or "-",
                "description": line.description,
                "qty": line.qty,
                "uom": line.uom_id.name,
                "unit_price": line.unit_price,
                "tax_rate": line.tax_id.rate,
                "amount": line.amount,
            })
        data.update({
            "amount_subtotal": obj.amount_subtotal,
            "amount_tax": obj.amount_tax,
            "amount_total": obj.amount_total,
            "amount_total_words": utils.num2word(obj.amount_total),
            "other_info": obj.other_info or "-",
            "currency_code": obj.currency_id.code,
            "tax_rate": int(tax_rate),
            "qty_total": obj.qty_total
        })
        return data

    def opport_stage(self, context={}):
        db = get_connection()
        company_id=get_active_company()
        res = db.query(
            "SELECT s.name,SUM(o.amount*o.probability/100) AS amount,COUNT(*) AS num FROM sale_opportunity o,sale_stage s WHERE s.id=o.stage_id AND o.state in ('open','won') and o.company_id=%s GROUP BY s.name",company_id)
        amounts = {}
        counts = {}
        for r in res:
            amounts[r.name] = r.amount
            counts[r.name] = r.num
        data = []
        for stage in get_model("sale.stage").search_browse([]):
            amt = amounts.get(stage.name, 0)
            count = counts.get(stage.name, 0)
            #label="%s (%d)"%(stage.name,count)
            label = stage.name
            data.append((label, amt))
        return {"value": data}

    def expected_revenue(self, context={}):
        company_id=get_active_company()
        db = get_connection()
        res = db.query(
            "SELECT date_trunc('month',o.date_close) AS month,SUM(o.amount*o.probability/100),COUNT(*) FROM sale_opportunity o WHERE o.state in ('open','won') and o.company_id=%s GROUP BY month",company_id)
        amounts = {}
        months = get_future_months(6)
        last_month = "%d-%.2d" % months[-1]
        for r in res:
            if not r.month:
                continue
            m = r.month[:7]
            if m > last_month:
                amounts["future"] = r.sum
            else:
                amounts[m] = r.sum
        data = []
        for y, m in months:
            amt = amounts.get("%d-%.2d" % (y, m), 0)
            d = date(year=y, month=m, day=1)
            data.append((d.strftime("%b"), amt))
        data.append(("Future", amounts.get("future", 0)))
        return {"value": data}

ReportSale.register()
