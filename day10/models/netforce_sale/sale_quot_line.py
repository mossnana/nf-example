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
import math
from decimal import *

class SaleQuotLine(Model):
    _name = "sale.quot.line"
    _fields = {
        "quot_id": fields.Many2One("sale.quot", "Quotation", required=True, on_delete="cascade", search=True),
        "product_id": fields.Many2One("product", "Product", search=True),
        "description": fields.Text("Description", required=True),
        "qty": fields.Decimal("Qty"),
        "uom_id": fields.Many2One("uom", "UoM"),
        "unit_price": fields.Decimal("Unit Price", scale=6),
        "discount": fields.Decimal("Disc %"),
        "discount_amount": fields.Decimal("Disc Amt"),
        "tax_id": fields.Many2One("account.tax.rate", "Tax Rate"),
        "amount": fields.Decimal("Amount",readonly=True),
        "contact_id": fields.Many2One("contact", "Contact", function="_get_related", function_search="_search_related", function_context={"path": "quot_id.contact_id"}, search=True),
        "date": fields.Date("Date", function="_get_related", function_search="_search_related", function_context={"path": "quot_id.date"}, search=True),
        "user_id": fields.Many2One("base.user", "Owner", function="_get_related", function_search="_search_related", function_context={"path": "quot_id.user_id"}, search=True),
        "state": fields.Selection([("draft", "Draft"), ("waiting_approval", "Awaiting Approval"), ("approved", "Approved"), ("won", "Won"), ("lost", "Lost"), ("revised", "Revised")], "Status", function="_get_related", function_search="_search_related", function_context={"path": "quot_id.state"}, search=True),
        "product_categ_id": fields.Many2Many("product.categ", "Product Category", function="_get_related", function_context={"path": "product_id.categ_id"}, function_search="_search_related", search=True),
        "agg_amount": fields.Decimal("Total Amount", agg_function=["sum", "amount"]),
        "agg_qty": fields.Decimal("Total Order Qty", agg_function=["sum", "qty"]),
        "sequence": fields.Char("Item No."),
        "retail_price": fields.Decimal("Retail Price"),
        "retail_amount": fields.Decimal("Retail Amount",function="get_retail_amount"),
        "est_cost_amount": fields.Decimal("Est. Cost Amount",function="get_est_profit",function_multi=True),
        "est_profit_amount": fields.Decimal("Est. Profit Amount",function="get_est_profit",function_multi=True),
        "est_margin_percent": fields.Decimal("Est. Margin %",function="get_est_profit",function_multi=True),
        "hide_sub": fields.Boolean("Hide Sub-items"),
        "is_hidden": fields.Boolean("Hidden",function="get_is_hidden",function_multi=True),
        "parent_sequence": fields.Char("Parent Sequence",function="get_is_hidden",function_multi=True),
        "est_margin_percent_input": fields.Decimal("Est. Margin % Input"),
    }
    _order_expression="case when tbl0.sequence is not null then (substring(tbl0.sequence, '^[0-9]+'))::int else tbl0.id end, tbl0.sequence"

    def create(self, vals, context={}):
        id = super(SaleQuotLine, self).create(vals, context)
        self.function_store([id])
        return id

    def write(self, ids, vals, context={}):
        super(SaleQuotLine, self).write(ids, vals, context)
        self.function_store(ids)

    def get_retail_amount(self, ids, context={}):
        vals = {}
        for line in self.browse(ids):
            vals[line.id] = (line.retail_price or 0) * (line.qty or 0)
        return vals

    def get_est_profit(self,ids,context={}):
        quot_ids=[]
        currency_rate = None
        settings = get_model('settings').browse(1)
        currency_id = settings.currency_id.id
        for line in self.browse(ids):
            quot_ids.append(line.quot_id.id)
        quot_ids=list(set(quot_ids))
        item_costs={}
        for quot in get_model("sale.quot").browse(quot_ids):
            for cost in quot.est_costs:
                est_comps=[]
                if cost.sequence:
                    for comp in cost.sequence.split("."):
                        est_comps.append(comp)
                        path=".".join(est_comps)
                        k=(quot.id,path)
                        item_costs.setdefault(k,0)
                        if quot.currency_id.id == currency_id:
                            item_costs[k]+=cost.amount
                        else:
                            item_costs[k]+=cost.amount_conv
        vals={}
        for line in self.browse(ids):
            profit=0
            k=(line.quot_id.id,line.sequence)
            cost_amount=item_costs.get(k,0)
            profit=(line.amount or 0) - cost_amount
            margin=(profit/line.amount)*100 if cost_amount else 0
            vals[line.id]={
                "est_cost_amount": cost_amount,
                "est_profit_amount": profit,
                "est_margin_percent": margin,
            }
        return vals

    def get_is_hidden(self,ids,context={}):
        quot_ids=[]
        for obj in self.browse(ids):
            quot_ids.append(obj.quot_id.id)
        quot_ids=list(set(quot_ids))
        vals={}
        for quot in get_model("sale.quot").browse(quot_ids):
            hide_parents=[]
            for line in quot.lines:
                if line.hide_sub and line.sequence:
                    hide_parents.append(line.sequence)
            for line in quot.lines:
                parent_seq=None
                if line.sequence:
                    for seq in hide_parents:
                        if line.sequence.startswith(seq+"."):
                            parent_seq=seq
                            break
                if line.id in ids:
                    vals[line.id]={
                        "is_hidden": parent_seq is not None,
                        "parent_sequence": parent_seq,
                    }
        return vals

SaleQuotLine.register()
