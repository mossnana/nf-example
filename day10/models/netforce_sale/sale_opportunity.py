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
from netforce.utils import get_data_path
import time
from netforce.access import get_active_company


class Opportunity(Model):
    _name = "sale.opportunity"
    _string = "Opportunity"
    _audit_log = True
    _key = ["name","user_id"]
    _multi_company = True
    _fields = {
        "user_id": fields.Many2One("base.user", "Opportunity Owner", required=True),
        "name": fields.Char("Opportunity Name", required=True, search=True),
        "contact_id": fields.Many2One("contact", "Contact", required=True, search=True),
        "campaign_id": fields.Many2One("mkt.campaign", "Marketing Campaign"),
        "date_close": fields.Date("Close Date", search=True),
        "stage_id": fields.Many2One("sale.stage", "Stage", search=True),
        "probability": fields.Decimal("Probability (%)"),
        "amount": fields.Decimal("Amount", search=True),
        "lead_source": fields.Char("Lead Source", search=True),
        "next_step": fields.Char("Next Step"),
        "description": fields.Text("Description"),
        "state": fields.Selection([["open", "Open"], ["won", "Won"], ["lost", "Lost"]], "Status"),
        "product_id": fields.Many2One("product", "Product"),
        "qty": fields.Decimal("Qty"),
        "quotations": fields.One2Many("sale.quot", "opport_id", "Quotations"),
        "comments": fields.One2Many("message", "related_id", "Comments"),
        "activities": fields.One2Many("activity", "related_id", "Activities"),
        "emails": fields.One2Many("email.message", "related_id", "Emails"),
        "competitors": fields.One2Many("opport.compet", "opport_id", "Competitors"),
        "company_id": fields.Many2One("company", "Company"),
        "region_id": fields.Many2One("region", "Region", search=True),
        "industry_id": fields.Many2One("industry", "Industry", search=True),
        "year": fields.Char("Year", sql_function=["year", "date_close"]),
        "quarter": fields.Char("Quarter", sql_function=["quarter", "date_close"]),
        "month": fields.Char("Month", sql_function=["month", "date_close"]),
        "week": fields.Char("Week", sql_function=["week", "date_close"]),
        "agg_amount": fields.Decimal("Total Amount", agg_function=["sum", "amount"]),
        "documents": fields.One2Many("document", "related_id", "Documents"),
    }
    _defaults = {
        "state": "open",
        "user_id": lambda self, context: int(context["user_id"]),
        "company_id": lambda *a: get_active_company(),
    }
    _order = "date_close desc"

    def copy_to_quotation(self, ids, context):
        id = ids[0]
        obj = self.browse(id)
        vals = {
            "opport_id": obj.id,
            "contact_id": obj.contact_id.id,
            "lines": [],
            "user_id": obj.user_id.id,
        }
        if obj.contact_id.currency_id:
            vals["currency_id"] = obj.contact_id.currency_id.id
        prod = obj.product_id
        if prod:
            qty=obj.qty or 1
            unit_price=obj.amount or prod.sale_price or 0
            amount=qty*unit_price
            line_vals = {
                "product_id": prod.id,
                "description": prod.name_get()[0][1],
                "qty": qty,
                "uom_id": prod.uom_id.id,
                "unit_price": unit_price,
                "amount": amount,
            }
            if prod.sale_tax_id:
                line_vals['tax_id']=prod.sale_tax_id.id
            vals["lines"].append(("create", line_vals))
        quot_id = get_model("sale.quot").create(vals, context=context)
        quot = get_model("sale.quot").browse(quot_id)
        return {
            "next": {
                "name": "quot",
                "mode": "form",
                "active_id": quot_id,
            },
            "flash": "Quotation %s created from opportunity" % quot.number
        }

    def copy(self, ids, context):
        obj = self.browse(ids)[0]
        vals = {
            "user_id": obj.user_id.id,
            "name": obj.name,
            "contact_id": obj.contact_id.id,
            "contact_id": obj.contact_id.id,
            "date_close": obj.date_close,
            "stage_id": obj.stage_id.id,
            "probability": obj.probability,
            "amount": obj.amount,
            "lead_source": obj.lead_source,
            "product_id": obj.product_id.id,
            "next_step": obj.next_step,
            "description": obj.description,
        }
        new_id = self.create(vals, context=context)
        new_obj = self.browse(new_id)
        return {
            "next": {
                "name": "opport_edit",
                "active_id": new_id,
            },
            "flash": "Opportunity copied",
        }

Opportunity.register()
