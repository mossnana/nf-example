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

from decimal import Decimal
from netforce.model import Model, fields, get_model


class PurchaseOrderLine(Model):
    _name = "purchase.order.line"
    _name_field = "order_id"
    _fields = {
        "order_id": fields.Many2One("purchase.order", "Purchase Order", required=True, on_delete="cascade"),
        "product_id": fields.Many2One("product", "Product"),
        "description": fields.Text("Description", required=True),
        "qty": fields.Decimal("Qty", required=True, scale=6),
        "uom_id": fields.Many2One("uom", "UoM", required=True),
        "unit_price": fields.Decimal("Unit Price", required=True, scale=6),
        "tax_id": fields.Many2One("account.tax.rate", "Tax Rate"),
        "amount": fields.Decimal("Amount", function="get_amount", function_multi=True, store=True, function_order=1),
        "amount_cur": fields.Decimal("Amount (Cur)", function="get_amount", function_multi=True, store=True, function_order=1),
        "qty_received": fields.Decimal("Received Qty", function="get_qty_received"),
        "qty_invoiced": fields.Decimal("Invoiced Qty", function="get_qty_invoiced"),
        "contact_id": fields.Many2One("contact", "Contact", function="_get_related", function_search="_search_related", function_context={"path": "order_id.contact_id"}),
        "date": fields.Date("Date", function="_get_related", function_search="_search_related", function_context={"path": "order_id.date"}),
        "state": fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Completed"), ("voided", "Voided")], "Status", function="_get_related", function_search="_search_related", function_context={"path": "order_id.state"}),
        "sale_id": fields.Many2One("sale.order", "Sales Order"),
        "location_id": fields.Many2One("stock.location", "Location", condition=[["type", "=", "internal"]]),
        "product_categs": fields.Many2Many("product.categ", "Product Categories", function="_get_related", function_context={"path": "product_id.categs"}, function_search="_search_related", search=True),
        "product_categ_id": fields.Many2Many("product.categ", "Product Category", function="_get_related", function_context={"path": "product_id.categ_id"}, function_search="_search_related", search=True),
        "agg_amount": fields.Decimal("Total Amount", agg_function=["sum", "amount"]),
        "agg_qty": fields.Decimal("Total Order Qty", agg_function=["sum", "qty"]),
        "agg_amount_cur": fields.Decimal("Total Amount Cur", agg_function=["sum", "amount_cur"]),
        "ship_method_id": fields.Many2One("ship.method", "Shipping Method"),
        "discount_amount": fields.Decimal("Disc Amt"),
        "discount_percent": fields.Decimal("Disc %"),
        "qty_stock": fields.Decimal("Qty (Stock UoM)"),
    }

    _order = "order_id desc,id"

    def create(self, vals, context={}):
        if not vals.get('qty_stock'):
            product_id=vals.get('product_id')
            location_id=vals.get('location_id')
            if product_id and location_id:
                vals['qty_stock']=get_model('stock.balance').get_qty_stock(product_id, location_id)
        id = super(PurchaseOrderLine, self).create(vals, context)
        self.function_store([id])
        return id

    def write(self, ids, vals, context={}):
        super(PurchaseOrderLine, self).write(ids, vals, context)
        self.function_store(ids)

    def get_amount(self, ids, context={}):
        settings = get_model("settings").browse(1)
        vals = {}
        objs = self.browse(ids)
        currency_rate=None
        if objs:
            for cr_rate in objs[0].order_id.currency_rates:
                currency_id = cr_rate.currency_id.id
                if cr_rate.currency_id.id==currency_id:
                    currency_rate=cr_rate.rate or 0
                    break
                if not currency_rate:
                    currency=get_model("currency").browse(currency_id)
                    currency_rate=currency.get_rate(date=objs[0].date,rate_type="buy") or 1
        for line in objs:
            amt = (line.qty * line.unit_price)
            if line.discount_percent:
                disc = amt*Decimal(line.discount_percent)/100
                amt -= disc
            amt -= (line.discount_amount or 0)
            order = line.order_id

            #default
            new_cur=get_model("currency").convert(amt, order.currency_id.id, settings.currency_id.id, rate=currency_rate)
            if line.product_id:
                product=line.product_id
                if product.purchase_currency_id:
                    new_cur=get_model("currency").convert(amt, order.currency_id.id, settings.currency_id.id, rate=currency_rate)
            vals[line.id] = {
                "amount": round(amt,2), #XXX
                "amount_cur": new_cur,
            }
        return vals

    def get_qty_received(self, ids, context={}):
        order_ids = []
        for obj in self.browse(ids):
            order_ids.append(obj.order_id.id)
        order_ids = list(set(order_ids))
        vals = {}
        for order in get_model("purchase.order").browse(order_ids):
            received_qtys = {}
            for move in order.stock_moves:
                if move.state != "done":
                    continue
                prod_id = move.product_id.id
                k = (prod_id, move.location_to_id.id)
                received_qtys.setdefault(k, 0)
                received_qtys[k] += move.qty  # XXX: uom
                k = (prod_id, move.location_from_id.id)
                received_qtys.setdefault(k, 0)
                received_qtys[k] -= move.qty  # XXX: uom
            for line in order.lines:
                if line.id not in ids:
                    continue
                k = (line.product_id.id, line.location_id.id)
                received_qty = received_qtys.get(k, 0)  # XXX: uom
                used_qty = min(line.qty, received_qty)
                vals[line.id] = used_qty
                if k in received_qtys:
                    received_qtys[k] -= used_qty
            for line in reversed(order.lines):
                k = (line.product_id.id, line.location_id.id)
                remain_qty = received_qtys.get(k, 0)  # XXX: uom
                if remain_qty:
                    vals[line.id] += remain_qty
                    received_qtys[k] -= remain_qty
        vals = {x: vals[x] for x in ids}
        return vals

    def get_qty_invoiced(self, ids, context={}):
        order_ids = []
        for obj in self.browse(ids):
            order_ids.append(obj.order_id.id)
        order_ids = list(set(order_ids))
        vals = {}
        for order in get_model("purchase.order").browse(order_ids):
            inv_qtys = {}
            for inv in order.invoices:
                if inv.state not in ("draft","waiting_payment","paid"):
                    continue
                for line in inv.lines:
                    prod_id = line.product_id.id
                    inv_qtys.setdefault(prod_id, 0)
                    inv_qtys[prod_id] += line.qty or 0
            for line in order.lines:
                if line.id not in ids:
                    continue
                prod_id = line.product_id.id
                inv_qty = inv_qtys.get(prod_id, 0)  # XXX: uom
                used_qty = min(line.qty, inv_qty)
                vals[line.id] = used_qty
                if prod_id in inv_qtys:
                    inv_qtys[prod_id] -= used_qty
            for line in reversed(order.lines):
                prod_id = line.product_id.id
                remain_qty = inv_qtys.get(prod_id, 0)  # XXX: uom
                if remain_qty:
                    vals[line.id] += remain_qty
                    inv_qtys[prod_id] -= remain_qty
        vals = {x: vals[x] for x in ids}
        return vals

    def onchange_product(self, context={}):
        data=context['data']
        path=context['path']
        line=get_data_path(data, path, parent=True)
        product_id=line['product_id']
        product=get_model('product').browse(product_id)

        return data


PurchaseOrderLine.register()
