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
from netforce.access import get_active_company, get_active_user, set_active_user
from . import utils
from decimal import Decimal
from datetime import datetime

class PurchaseOrder(Model):
    _name = "purchase.order"
    _string = "Purchase Order"
    _audit_log = True
    _name_field = "number"
    _multi_company = True
    _key = ["company_id", "number"]
    _fields = {
        "number": fields.Char("Number", required=True, search=True),
        "ref": fields.Char("Ref", search=True),
        "contact_id": fields.Many2One("contact", "Supplier", required=True, search=True),
        "customer_id": fields.Many2One("contact", "Customer", search=True),
        "date": fields.Date("Date", required=True, search=True),
        "date_required": fields.Date("Required Date"),
        "state": fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Completed"), ("voided", "Voided")], "Status", required=True, search=True),
        "lines": fields.One2Many("purchase.order.line", "order_id", "Lines"),
        "amount_subtotal": fields.Decimal("Subtotal", function="get_amount", function_multi=True, store=True),
        "amount_tax": fields.Decimal("Tax Amount", function="get_amount", function_multi=True, store=True),
        "amount_total": fields.Decimal("Total", function="get_amount", function_multi=True, store=True),
        "amount_total_cur": fields.Decimal("Total", function="get_amount", function_multi=True, store=True),
        "amount_total_words": fields.Char("Total Words", function="get_amount_total_words"),
        "qty_total": fields.Decimal("Total Quantity", function="get_qty_total"),
        "currency_id": fields.Many2One("currency", "Currency", required=True),
        "tax_type": fields.Selection([["tax_ex", "Tax Exclusive"], ["tax_in", "Tax Inclusive"], ["no_tax", "No Tax"]], "Tax Type", required=True),
        "invoice_lines": fields.One2Many("account.invoice.line", "purch_id", "Invoice Lines"),
        #"stock_moves": fields.One2Many("stock.move","purch_id","Stock Moves"),
        "invoices": fields.One2Many("account.invoice", "related_id", "Invoices"),
        "pickings": fields.Many2Many("stock.picking", "Stock Pickings", function="get_pickings"),
        "is_delivered": fields.Boolean("Delivered", function="get_delivered"),
        "is_paid": fields.Boolean("Paid", function="get_paid"),
        "invoice_status": fields.Char("Invoice", function="get_invoice_status"),
        "comments": fields.One2Many("message", "related_id", "Comments"),
        "delivery_date": fields.Date("Delivery Date"),
        "ship_method_id": fields.Many2One("ship.method", "Shipping Method"),  # XXX: deprecated
        "payment_terms": fields.Text("Payment Terms"),
        "ship_term_id": fields.Many2One("ship.term", "Shipping Terms"),
        "price_list_id": fields.Many2One("price.list", "Price List", condition=[["type", "=", "purchase"]]),
        "documents": fields.One2Many("document", "related_id", "Documents"),
        "company_id": fields.Many2One("company", "Company"),
        "purchase_type_id": fields.Many2One("purchase.type", "Purchase Type"),
        "other_info": fields.Text("Other Info"),
        "bill_address_id": fields.Many2One("address", "Billing Address"),
        "ship_address_id": fields.Many2One("address", "Shipping Address"),
        "sequence_id": fields.Many2One("sequence", "Number Sequence"),
        "stock_moves": fields.One2Many("stock.move", "related_id", "Stock Movements"),
        "agg_qty": fields.Decimal("Total Order Qty", agg_function=["sum_line", "qty", "order_id", "purchase_order_line"]),
        "agg_amount_total": fields.Decimal("Total Amount", agg_function=["sum", "amount_total"]),
        "year": fields.Char("Year", sql_function=["year", "date"]),
        "quarter": fields.Char("Quarter", sql_function=["quarter", "date"]),
        "month": fields.Char("Month", sql_function=["month", "date"]),
        "week": fields.Char("Week", sql_function=["week", "date"]),
        "agg_amount_subtotal": fields.Decimal("Total Amount w/o Tax", agg_function=["sum", "amount_subtotal"]),
        "user_id": fields.Many2One("base.user", "Owner", search=True),
        "emails": fields.One2Many("email.message", "related_id", "Emails"),
        "product_id": fields.Many2One("product", "Product", store=False, function_search="search_product", search=True),
        "currency_rates": fields.One2Many("custom.currency.rate","related_id","Currency Rates"),
        "related_id": fields.Reference([],"Related To"),
        "location_id": fields.Many2One("stock.location", "Location", function_search="search_location", search=True, store=False),
    }
    _order = "date desc,number desc"
    _constraints = ["check_fields"]
    _sql_constraints = [
        ("key_uniq", "unique (company_id, number)", "The number of each company must be unique!")
    ]

    def check_fields(self, ids, context={}):
        for obj in self.browse(ids):
            if context.get('is_draft'):
                continue
            dup=None
            sequence_item = []
            for line in obj.lines:
                if line.sequence:
                    sequence_item.append(line.sequence)
            dup_sequence = set()
            for i in sequence_item:
                if sequence_item.count(i)>=2:
                    dup_sequence.add(i)
                    dup=True
            if dup:
                raise Exception("Lines: Fields Item No. Duplicates : %s" % (str(list(dup_sequence))))

    def _get_number(self, context={}):
        seq_id = get_model("sequence").find_sequence(type="purchase_order")
        if not seq_id:
            return None
        while 1:
            num = get_model("sequence").get_next_number(seq_id,context=context)
            user_id = get_active_user()
            set_active_user(1)
            res = self.search([["number", "=", num]])
            set_active_user(user_id)
            if not res:
                return num
            get_model("sequence").increment_number(seq_id,context=context)

    def _get_currency(self, context={}):
        settings = get_model("settings").browse(1)
        return settings.currency_id.id

    def _get_currency_rates(self,context={}):
        settings = get_model("settings").browse(1)
        lines=[]
        date = time.strftime("%Y-%m-%d")
        line_vals={
            "currency_id": settings.currency_id.id,
            "rate": settings.currency_id and settings.currency_id.get_rate(date,"buy") or 1
        }
        if context.get("is_create"):
            lines.append(('create',line_vals))
        else:
            lines.append(line_vals)
        return lines

    _defaults = {
        "state": "draft",
        "date": lambda *a: time.strftime("%Y-%m-%d"),
        "number": _get_number,
        "currency_id": _get_currency,
        "tax_type": "tax_ex",
        "company_id": lambda *a: get_active_company(),
        "user_id": lambda *a: get_active_user(),
        "currency_rates": _get_currency_rates,
    }

    def get_currency_rate(self,context={}):
        data=context['data']
        currency_id = data["currency_id"]
        currency_rate=0
        for cr_rate in data['currency_rates']:
            if cr_rate['currency_id']==currency_id:
                currency_rate=cr_rate['rate'] or 0
                break
        if not currency_rate:
            currency=get_model("currency").browse(currency_id)
            currency_rate=currency.get_rate(date=data['date'],rate_type="buy") or 1
        return currency_rate

    def onchange_currency(self, context):
        data=context['data']
        currency_id = data["currency_id"]
        currency=get_model("currency").browse(currency_id)
        rate=currency.get_rate(date=data['date'],rate_type="buy") or 1
        for crr in data['currency_rates']:
            crr.update({
                'currency_id': currency_id,
                'rate': rate,
            })
            break
        data = self.update_line_currency(context)
        return data

    def onchange_pricelist(self, context):
        data=context['data']
        data = self.update_line_currency(context)
        return data

    def update_line_currency(self, context):
        settings=get_model("settings").browse(1)
        data=context['data']
        currency_id = data["currency_id"]
        pricelist_id = data["price_list_id"]
        for line in data['lines']:
            prod_cur_id = None
            price_list = 0
            prod_id=line.get('product_id')
            if not prod_id:
                continue
            prod = get_model("product").browse(prod_id)
            qty = line.get('qty') or 0
            if pricelist_id:
                price_list = get_model("price.list").get_price(pricelist_id, prod.id, qty)
                prod_cur_id = get_model("price.list").browse(pricelist_id).currency_id.id or None
                    #continue
            #price = prod.purchase_price or 0
            if price_list == 0:
                price = prod.purchase_price or 0
            else:
               price = price_list
            currency_id = data["currency_id"]
            currency_rate = self.get_currency_rate(context)
            if not prod_cur_id and prod.purchase_currency_id:
                prod_cur_id = prod.purchase_currency_id.id
            if prod_cur_id:
                if prod_cur_id != currency_id:
                    cur_id=get_model("currency").browse(prod_cur_id)
                    currency_from_rate=cur_id.get_rate(date=data['date'],rate_type="buy") or 1
                    price = get_model("currency").convert(price, prod_cur_id, currency_id, from_rate=currency_from_rate, to_rate=currency_rate)
                else:
                    price = get_model("currency").convert(price, prod_cur_id, currency_id, to_rate=currency_rate)
            else:
                price = get_model("currency").convert(price, settings.currency_id.id, currency_id, to_rate=currency_rate)
            line["unit_price"] = price
        data = self.update_amounts(context)
        return data

    def onchange_currency_rate(self, context={}):
        data=context['data']
        path=context['path']
        line=get_data_path(data, path, parent=True)
        currency=get_model("currency").browse(line['currency_id'])
        line['rate']=currency.get_rate(date=data['date'],rate_type="buy") or 1
        data = self.update_line_currency(context)
        return data

    def create(self, vals, **kw):
        context=kw.get('context',{})
        context['is_create']=True
        kw['context']=context
        id = super(PurchaseOrder, self).create(vals, **kw)
        self.function_store([id])
        return id

    def write(self, ids, vals, **kw):
        super(PurchaseOrder, self).write(ids, vals, **kw)
        self.function_store(ids)
        line_ids=get_model('purchase.order.line').search([['order_id','in', ids]])
        get_model("purchase.order.line").function_store(line_ids)

    def confirm(self, ids, context={}):
        settings = get_model("settings").browse(1)
        for obj in self.browse(ids):
            if obj.state != "draft":
                raise Exception("Invalid state")
            if not obj.amount_total:
                raise Exception("Cannot confirm PO if total amount is zero")
            service_count=0
            non_pro_count=0
            for line in obj.lines:
                prod = line.product_id
                if not prod:
                    non_pro_count +=1
                if prod and prod.type in ("stock", "consumable", "bundle", "master") and not line.location_id:
                    raise Exception("Missing location for product %s" % prod.code)
                if prod.purchase_min_qty and line.qty < prod.purchase_min_qty:
                    raise Exception("Minimum Purchases Qty for [%s] %s is %s"%(prod.code,prod.name,prod.purchase_min_qty))
                if prod.type=='service':
                    service_count+=1
            obj.write({"state": "confirmed"})
            if settings.purchase_copy_picking and service_count!=len(obj.lines) and non_pro_count!=len(obj.lines):
                if obj.pickings:
                    for pick in obj.pickings:
                        pick.delete()
                res=obj.copy_to_picking()
                if res:
                    picking_id=res["picking_id"]
                    get_model("stock.picking").pending([picking_id])
            if settings.purchase_copy_invoice:
                if obj.invoices:
                    for inv in obj.invoices:
                        inv.delete()
                obj.copy_to_invoice()
            obj.trigger("confirm")

    def done(self, ids, context={}):
        for obj in self.browse(ids):
            if obj.state != "confirmed":
                raise Exception("Invalid state")
            obj.write({"state": "done"})

    def reopen(self, ids, context={}):
        for obj in self.browse(ids):
            if obj.state != "done":
                raise Exception("Invalid state")
            obj.write({"state": "confirmed"})

    def to_draft(self, ids, context={}):
        for obj in self.browse(ids):
            non_pro = 0
            for line in obj.lines:
                if not line.product_id:
                    non_pro += 1
            if non_pro == len(obj.lines):
                obj.is_delivered = False
            cannot_draft=(obj.is_delivered and obj.pickings) or obj.is_paid
            if cannot_draft:
                raise Exception("Cannot to draft if order is delivered or paid!")
            for inv in obj.invoices:
                assert inv.state=="draft" or inv.state=="voided" or inv.state=="waiting_approval","Can not To Draft purchase order.The Invoice must be Draft."
            for pick in obj.pickings:
                assert pick.state == "draft" or pick.state=="voided","Can not To Draft purchase order.The Stock Picking must be Draft."
            obj.write({"state": "draft"})

    def get_amount(self, ids, context={}):
        settings = get_model("settings").browse(1)
        res = {}
        for obj in self.browse(ids):
            vals = {}
            subtotal = 0
            tax = 0
            for line in obj.lines:
                if line.tax_id:
                    line_tax = get_model("account.tax.rate").compute_tax(
                        line.tax_id.id, line.amount, tax_type=obj.tax_type)
                else:
                    line_tax = 0
                tax += line_tax
                if obj.tax_type == "tax_in":
                    subtotal += line.amount - line_tax
                else:
                    subtotal += line.amount
            vals["amount_subtotal"] = subtotal
            vals["amount_tax"] = tax
            vals["amount_total"] = subtotal + tax
            vals["amount_total_cur"] = get_model("currency").convert(
                vals["amount_total"], obj.currency_id.id, settings.currency_id.id)
            res[obj.id] = vals
        return res

    def get_qty_total(self, ids, context={}):
        res = {}
        for obj in self.browse(ids):
            qty = sum([line.qty for line in obj.lines])
            res[obj.id] = qty or 0
        return res

    def update_amounts(self, context):
        settings=get_model("settings").browse(1)
        data = context["data"]
        data["amount_subtotal"] = 0
        data["amount_tax"] = 0
        tax_type = data["tax_type"]
        for line in data["lines"]:
            if not line:
                continue
            amt = Decimal((line.get("qty") or 0) * (line.get("unit_price") or 0))
            if line.get("discount_percent"):
                disc = amt * line["discount_percent"] / Decimal(100)
                amt -= disc
            amt -= (line.get("discount_amount") or 0)
            line["amount"] = amt
            currency_rate=self.get_currency_rate(context)
            line['amount_cur']=get_model("currency").convert(amt, data['currency_id'], settings.currency_id.id, rate=currency_rate)
            tax_id = line.get("tax_id")
            if tax_id:
                tax = get_model("account.tax.rate").compute_tax(tax_id, amt, tax_type=tax_type)
                data["amount_tax"] += tax
            else:
                tax = 0
            if tax_type == "tax_in":
                data["amount_subtotal"] += amt - tax
            else:
                data["amount_subtotal"] += amt
        data["amount_total"] = data["amount_subtotal"] + data["amount_tax"]
        return data

    def onchange_product(self, context):
        data = context["data"]
        path = context["path"]
        settings=get_model("settings").browse(1)
        line = get_data_path(data, path, parent=True)
        prod_id = line.get("product_id")
        if not prod_id:
            return {}
        prod_cur_id = None
        prod = get_model("product").browse(prod_id)
        line["description"] = prod.description
        line["qty"] = prod.purchase_min_qty or 1
        line["uom_id"] = prod.purchase_uom_id.id or prod.uom_id.id
        pricelist_id = data["price_list_id"]
        price = 0
        if pricelist_id:
            price = get_model("price.list").get_price(pricelist_id, prod.id, 1) or 0
            prod_cur_id = get_model("price.list").browse(pricelist_id).currency_id.id or None
        if not price or price == 0:
            price = prod.purchase_price or 0
            if not prod_cur_id:
                prod_cur_id = prod.purchase_currency_id.id or None
        currency_id = data["currency_id"]
        currency_rate = self.get_currency_rate(context)
        if price:
            if prod_cur_id:
                if prod_cur_id != currency_id:
                    cur_id=get_model("currency").browse(prod_cur_id)
                    currency_from_rate=cur_id.get_rate(date=data['date'],rate_type="buy") or 1
                    price = get_model("currency").convert(price, prod_cur_id, currency_id, from_rate=currency_from_rate, to_rate=currency_rate)
                else:
                    price = get_model("currency").convert(price, prod_cur_id, currency_id, to_rate=currency_rate)
            else:
                price = get_model("currency").convert(price, settings.currency_id.id, currency_id, to_rate=currency_rate)

        line["unit_price"] = price
        ratio = get_model("uom").browse(int(line["uom_id"])).ratio
        line["unit_price"] = price * ratio
        if prod.purchase_uom_id:
            line["unit_price"] = price * ratio / prod.purchase_uom_id.ratio or 1
        if prod.categ_id and prod.categ_id.purchase_tax_id:
            line["tax_id"] = prod.categ_id.purchase_tax_id.id
        if prod.purchase_tax_id is not None:
            line["tax_id"] = prod.purchase_tax_id.id
        contact_id=data.get('contact_id')
        if contact_id:
            contact=get_model("contact").browse(contact_id)
            if contact.tax_payable_id:
                line["tax_id"] = contact.tax_payable_id.id
        if data.get("tax_type","")=="no_tax":
            line["tax_id"]=None

        if prod.location_id:
            line["location_id"] = prod.location_id.id
        elif prod.locations:
            line["location_id"] = prod.locations[0].location_id.id
            #TODO
        #amount_cur
        self.onchange_location(context)
        data = self.update_amounts(context)
        return data

    def onchange_location(self, context):
        data = context["data"]
        path = context["path"]
        line = get_data_path(data, path, parent=True)
        line["qty_stock"] = 0
        if "product_id" in line and 'location_id' in line:
            product_id=line['product_id']
            location_id=line['location_id']
            qty_stock=get_model("stock.balance").get_qty_stock(product_id, location_id)
            line["qty_stock"] = qty_stock
        return data

    def onchange_qty(self, context):
        data = context["data"]
        path = context["path"]
        line = get_data_path(data, path, parent=True)
        prod_id = line.get("product_id")
        if not prod_id:return {}
        prod = get_model("product").browse(prod_id)
        qty = line["qty"]
        price = line["unit_price"]
        if not price:
            settings = get_model("settings").browse(1)
            currency_id = data["currency_id"]
            currency_rate=self.get_currency_rate(context)
            price_cur = get_model("currency").convert(price, settings.currency_id.id, currency_id, from_rate=1, to_rate=currency_rate)
            line["unit_price"] = price_cur
            line['amount_cur']= price_cur*qty
        if prod.purchase_min_qty and qty < prod.purchase_min_qty:
            raise Exception("Minimum Sales Qty for [%s] %s is %s"%(prod.code,prod.name,prod.purchase_min_qty))
        data = self.update_amounts(context)
        return data

    def onchange_uom(self, context):
        data = context["data"]
        path = context["path"]
        line = get_data_path(data, path, parent=True)
        prod_id = line.get("product_id")
        uom_id = line.get("uom_id")
        pricelist_id = data["price_list_id"]
        price=None
        if not prod_id:return data
        prod = get_model("product").browse(prod_id)
        if not uom_id: return data
        uom = get_model("uom").browse(uom_id)
        if pricelist_id:
            price = get_model("price.list").get_price(pricelist_id, prod.id, 1)
        if price is None:
            price = prod.purchase_price
        if price is not None:
            if prod.purchase_currency_id and prod.purchase_currency_id.id != data['currency_id']:
                price=get_model("currency").convert(price, prod.purchase_currency_id.id, data['currency_id'])
        line["unit_price"] = price * uom.ratio / prod.uom_id.ratio
        if prod.purchase_uom_id:
            line["unit_price"] = price * uom.ratio / prod.purchase_uom_id.ratio or 1
        data = self.update_amounts(context)
        return data

    def copy_to_picking(self, ids, context={}):
        settings=get_model("settings").browse(1)
        obj = self.browse(ids[0])
        contact = obj.contact_id
        pick_vals = {
            "type": "in",
            "ref": obj.number,
            "related_id": "purchase.order,%s" % obj.id,
            "contact_id": contact.id,
            "currency_id": obj.currency_id.id,
            "ship_method_id": obj.ship_method_id.id,
            "lines": [],
        }
        if obj.delivery_date:
            pick_vals["date"]=obj.delivery_date+datetime.strftime(datetime.now()," %H:%M:%S")
        if contact and contact.pick_in_journal_id:
            pick_vals["journal_id"] = contact.pick_in_journal_id.id
        res = get_model("stock.location").search([["type", "=", "supplier"]],order="id")
        if not res:
            raise Exception("Supplier location not found")
        supp_loc_id = res[0]
        res = get_model("stock.location").search([["type", "=", "internal"]])
        if not res:
            raise Exception("Warehouse not found")
        wh_loc_id = res[0]
        if not settings.currency_id:
            raise Exception("Missing currency in financial settings")
        for line in obj.lines:
            prod = line.product_id
            if prod.type not in ("stock", "consumable", "bundle", "master"):
                continue
            remain_qty = (line.qty or 0) - line.qty_received
            #remain_qty = (line.qty_stock or line.qty) - line.qty_received
            if remain_qty <= 0:
                continue
            if not prod.unique_lot:
                unit_price=line.amount/line.qty if line.qty else 0
                if obj.tax_type=="tax_in":
                    if line.tax_id:
                        tax_amt = get_model("account.tax.rate").compute_tax(
                            line.tax_id.id, unit_price, tax_type=obj.tax_type)
                    else:
                        tax_amt = 0
                    cost_price_cur=unit_price-tax_amt
                else:
                    cost_price_cur=unit_price
                #if line.qty_stock:
                    #purch_uom=prod.uom_id
                    #if not prod.purchase_to_stock_uom_factor:
                        #raise Exception("Missing purchase order to stock UoM factor for product %s"%prod.code)
                    #cost_price_cur/=prod.purchase_to_stock_uom_factor
                #else:
                    #purch_uom=line.uom_id
                purch_uom=line.uom_id
                cost_price=get_model("currency").convert(cost_price_cur,obj.currency_id.id,settings.currency_id.id,date=pick_vals.get("date"))
                cost_amount=cost_price*remain_qty
                line_vals = {
                    "product_id": prod.id,
                    "qty": remain_qty,
                    "uom_id": purch_uom.id,
                    "cost_price_cur": 0 if prod.type == "bundle" else cost_price_cur,
                    "cost_price": 0 if prod.type == "bundle" else cost_price,
                    "cost_amount": 0 if prod.type == "bundle" else cost_amount,
                    "location_from_id": supp_loc_id,
                    "location_to_id": line.location_id.id or wh_loc_id,
                    "related_id": "purchase.order,%s" % obj.id,
                }
                pick_vals["lines"].append(("create", line_vals))
            else:
                for i in range(int(line.qty)):
                    if obj.tax_type=="tax_in":
                        if line.tax_id:
                            tax_amt = get_model("account.tax.rate").compute_tax(
                                line.tax_id.id, line.unit_price, tax_type=obj.tax_type)
                        else:
                            tax_amt = 0
                        cost_price_cur=line.unit_price-tax_amt
                    else:
                        cost_price_cur=line.unit_price
                    purch_uom=line.uom_id
                    cost_price=get_model("currency").convert(cost_price_cur,obj.currency_id.id,settings.currency_id.id,date=pick_vals.get("date"))
                    cost_amount=cost_price
                    line_spilt = {
                        "product_id": prod.id,
                        "qty": 1,
                        "uom_id": purch_uom.id,
                        "cost_price_cur": cost_price_cur,
                        "cost_price": cost_price,
                        "cost_amount": cost_amount,
                        "location_from_id": supp_loc_id,
                        "location_to_id": line.location_id.id or wh_loc_id,
                        "related_id": "purchase.order,%s" % obj.id,
                    }
                    pick_vals["lines"].append(("create", line_spilt))
        if not pick_vals["lines"]:
            return
        pick_id = get_model("stock.picking").create(pick_vals, {"pick_type": "in"})
        pick = get_model("stock.picking").browse(pick_id)
        pick.set_currency_rate()
        return {
            "next": {
                "name": "pick_in",
                "mode": "form",
                "active_id": pick_id,
            },
            "flash": "Goods receipt %s created from purchase order %s" % (pick.number, obj.number),
            "picking_id": pick_id,
        }

    def copy_to_invoice(self, ids, context={}):
        id = ids[0]
        obj = self.browse(id)
        contact = obj.contact_id
        inv_vals = {
            "type": "in",
            "inv_type": "invoice",
            "ref": obj.number,
            "related_id": "purchase.order,%s" % obj.id,
            "contact_id": obj.contact_id.id,
            "currency_id": obj.currency_id.id,
            "lines": [],
            "tax_type": obj.tax_type,
        }
        if contact.purchase_journal_id:
            inv_vals["journal_id"] = contact.purchase_journal_id.id
            if contact.purchase_journal_id.sequence_id:
                inv_vals["sequence_id"] = contact.purchase_journal_id.sequence_id.id
        if contact.purchase_payment_terms_id:
            inv_vals["payment_terms_id"] = contact.purchase_payment_terms_id.id,
            inv_vals["due_date"] = get_model("account.invoice").calc_date(time.strftime("%Y-%m-%d"),contact.purchase_payment_terms_id.days)
        ## get curruncy rate
        if obj.currency_id:
            inv_vals["currency_rate"] = obj.currency_id.get_rate(date=time.strftime("%Y-%m-%d"),rate_type="buy")
        for line in obj.lines:
            prod = line.product_id
            remain_qty = line.qty - line.qty_invoiced
            if remain_qty <= 0:
                continue
            # get account for purchase invoice
            purch_acc_id=None
            if prod:
                # 1. get from product
                purch_acc_id=prod.purchase_account_id and prod.purchase_account_id.id or None
                # 2. if not get from master / parent product
                if not purch_acc_id and prod.parent_id:
                    purch_acc_id=prod.parent_id.purchase_account_id.id
                # 3. if not get from product category
                categ=prod.categ_id
                if categ and not purch_acc_id:
                    purch_acc_id= categ.purchase_account_id and categ.purchase_account_id.id or None

            #if not purch_acc_id:
                #raise Exception("Missing purchase account configure for product [%s]" % prod.name)

            amt = Decimal((remain_qty * line.unit_price))
            disc = amt * ((line.discount_percent or 0) / Decimal(100))
            amt -= disc
            amt -= line.discount_amount or 0
            line_vals = {
                "product_id": prod.id,
                "description": line.description,
                "qty": remain_qty,
                "uom_id": line.uom_id.id,
                "unit_price": line.unit_price,
                "account_id": purch_acc_id,
                "tax_id": line.tax_id.id,
                "discount": line.discount_percent,
                "discount_amount": line.discount_amount,
                "amount": amt,
            }
            inv_vals["lines"].append(("create", line_vals))
        if not inv_vals["lines"]:
            raise Exception("Nothing left to invoice")
        inv_id = get_model("account.invoice").create(inv_vals, {"type": "in", "inv_type": "invoice"})
        inv = get_model("account.invoice").browse(inv_id)
        return {
            "next": {
                "name": "view_invoice",
                "active_id": inv_id,
            },
            "flash": "Invoice %s created from purchase order %s" % (inv.number, obj.number),
        }

    def get_delivered(self, ids, context={}):
        vals = {}
        for obj in self.browse(ids):
            if obj.state == "draft":
                vals[obj.id] = False
                return vals
            is_delivered = True
            count_line = 0
            for line in obj.lines:
                prod = line.product_id
                count_line += 1
                if not prod:
                    continue
                if prod.type not in ("stock", "consumable", "bundle", "master"):
                    continue
                remain_qty = line.qty - line.qty_received
                if remain_qty > 0:
                    is_delivered = False
                    break
            if not count_line:
                is_delivered = False
            vals[obj.id] = is_delivered
        return vals

    def get_paid(self, ids, context={}):
        vals = {}
        for obj in self.browse(ids):
            amt_paid = 0
            count_line = 0
            for inv in obj.invoices:
                if inv.state != "paid":
                    continue
                count_line += 1
                amt_paid += inv.amount_total
                if inv.deposit_notes:
                    amt_paid += inv.amount_deposit
            is_paid = amt_paid >= obj.amount_total and count_line
            vals[obj.id] = is_paid
            if obj.state=='confirmed':
                if is_paid==True and obj.is_delivered==True:
                    obj.done()
        return vals

    def get_invoice_status(self,ids,context={}):
        vals = {}
        for obj in self.browse(ids):
            inv_status = "No"
            amt_inv = 0
            for inv in obj.invoices:
                if inv.state == "voided" or inv.inv_type != 'invoice': continue
                amt_inv += inv.amount_total
                if inv.deposit_notes:
                    amt_inv += inv.amount_deposit
            if amt_inv >= obj.amount_total:
                inv_status = "Yes"
            elif amt_inv != 0:
                percent = round(Decimal(Decimal(amt_inv / obj.amount_total)*100))
                inv_status = "%s"%percent+"%"
            vals[obj.id] = inv_status
        return vals

    def void(self, ids, context={}):
        obj = self.browse(ids)[0]
        for pick in obj.pickings:
            if pick.state != "voided":
                raise Exception("There are still goods receipts for this purchase order")
        for inv in obj.invoices:
            if inv.state != "voided":
                raise Exception("There are still invoices for this purchase order")
        obj.write({"state": "voided"})

    def copy(self, ids, context):
        obj = self.browse(ids)[0]
        vals = {
            "contact_id": obj.contact_id.id,
            "date": obj.date,
            "ref": obj.ref,
            "currency_id": obj.currency_id.id,
            "tax_type": obj.tax_type,
            "lines": [],
        }
        for line in obj.lines:
            line_vals = {
                "product_id": line.product_id.id,
                "description": line.description,
                "qty": line.qty,
                "uom_id": line.uom_id.id,
                "unit_price": line.unit_price,
                "tax_id": line.tax_id.id,
                "location_id": line.location_id.id,
            }
            vals["lines"].append(("create", line_vals))
        new_id = self.create(vals)
        new_obj = self.browse(new_id)
        return {
            "next": {
                "name": "purchase",
                "mode": "form",
                "active_id": new_id,
            },
            "flash": "Purchase order %s copied to %s" % (obj.number, new_obj.number),
        }

    def get_invoices(self, ids, context={}):
        vals = {}
        for obj in self.browse(ids):
            inv_ids = []
            for inv_line in obj.invoice_lines:
                inv_id = inv_line.invoice_id.id
                if inv_id not in inv_ids:
                    inv_ids.append(inv_id)
            vals[obj.id] = inv_ids
        return vals

    def get_pickings(self, ids, context={}):
        vals = {}
        for obj in self.browse(ids):
            pick_ids = []
            for move in obj.stock_moves:
                pick_id = move.picking_id.id
                if pick_id not in pick_ids:
                    pick_ids.append(pick_id)
            vals[obj.id] = pick_ids
        return vals

    def onchange_contact(self, context):
        data = context["data"]
        contact_id = data.get("contact_id")
        if not contact_id:
            return {}
        contact = get_model("contact").browse(contact_id)
        data["payment_terms"] = contact.payment_terms
        data["price_list_id"] = contact.purchase_price_list_id.id
        
        data["bill_address_id"] = get_model("address").get_billing_address_company()
        data["ship_address_id"] = get_model("address").get_shipping_address_company()

        if contact.currency_id:
            data["currency_id"] = contact.currency_id.id
            data=self.onchange_currency(context)
        else:
            settings = get_model("settings").browse(1)
            data["currency_id"] = settings.currency_id.id
        data=self.onchange_currency(context)
        return data

    def check_received_qtys(self, ids, context={}):
        obj = self.browse(ids)[0]
        for line in obj.lines:
            if line.qty_received > (line.qty or line.qty_stock):
                raise Exception("Can not receive excess quantity for purchase order %s and product %s (order qty: %s, received qty: %s)" % (
                    obj.number, line.product_id.code, line.qty or line.qty_stock, line.qty_received))

    def get_purchase_form_template(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state == "draft":
            return "rfq_form"
        else:
            return "purchase_form"

    def get_amount_total_words(self, ids, context={}):
        vals = {}
        for obj in self.browse(ids):
            amount_total_words = utils.num2word(obj.amount_total)
            vals[obj.id] = amount_total_words
            return vals

    def onchange_sequence(self, context={}):
        data = context["data"]
        context['date'] = data['date']
        seq_id = data["sequence_id"]
        if not seq_id:
            seq_id = get_model("sequence").find_sequence(type="purchase_order")
        while 1:
            num = get_model("sequence").get_next_number(seq_id, context=context)
            user_id = get_active_user()
            set_active_user(1)
            res = self.search([["number", "=", num]])
            set_active_user(user_id)
            if not res:
                break
            get_model("sequence").increment_number(seq_id, context=context)
        data["number"] = num
        return data

    def delete(self, ids, **kw):
        for obj in self.browse(ids):
            if obj.state in ("confirmed", "done"):
                raise Exception("Can not delete purchase order in this status")
        super().delete(ids, **kw)

    def view_purchase(self, ids, context={}):
        obj=get_model("purchase.order.line").browse(ids)[0]
        return {
            'next': {
                'name': 'purchase',
                'active_id': obj.order_id.id,
                'mode': 'form',
            },
        }

    def copy_to_purchase_return(self,ids,context={}):
        seq_id = get_model("sequence").find_sequence(type="purchase_return")
        if not seq_id:
            raise Exception("Missing Sequence purchase return")
        for obj in self.browse(ids):
            order_vals = {}
            order_vals = {
                "contact_id":obj.contact_id.id,
                "date":obj.date,
                "ref":obj.number,
                "currency_id":obj.currency_id.id,
                "tax_type":obj.tax_type,
                "bill_address_id":obj.bill_address_id.id,
                "ship_address_id":obj.ship_address_id.id,
                "price_list_id": obj.price_list_id.id,
                "payment_terms": obj.payment_terms or obj.contact_id.payment_terms,
                "lines":[],
            }
            for line in obj.lines:
                line_vals = {
                    "product_id":line.product_id.id,
                    "description":line.description,
                    "qty":line.qty,
                    "uom_id":line.uom_id.id,
                    "unit_price":line.unit_price,
                    "tax_id":line.tax_id.id,
                    "amount":line.amount,
                    "location_id":line.location_id.id,
                }
                order_vals["lines"].append(("create", line_vals))
            purchase_id = get_model("purchase.return").create(order_vals)
            purchase = get_model("purchase.return").browse(purchase_id)
        return {
            "next": {
                "name": "purchase_return",
                "mode": "form",
                "active_id": purchase_id,
            },
            "flash": "Purchase Return %s created from purchases order %s" % (purchase.number, obj.number),
        }

    def onchange_tax_type(self, context={}):
        data=context['data']
        if data['tax_type']=='no_tax':
            for line in data['lines']:
                line['tax_id']=None
        else:
            for line in data['lines']:
                product_id=line.get('product_id')
                if not product_id:
                    continue
                if line['tax_id']:
                    continue

                contact_id=data.get('contact_id')
                if contact_id:
                    contact=get_model("contact").browse(contact_id)
                    if contact.tax_payable_id:
                        line["tax_id"] = contact.tax_payable_id.id
                product=get_model("product").browse(product_id)
                if product.purchase_tax_id and not line.get('tax_id'):
                    line["tax_id"] = product.purchase_tax_id.id
                if product.categ_id and product.categ_id.purchase_tax_id and not line.get('tax_id'):
                    line["tax_id"] = product.categ_id.purchase_tax_id.id
        data=self.update_amounts(context)
        return data

    def search_product(self, clause, context={}):
        op = clause[1]
        val = clause[2]
        if isinstance(val, int):
            return ["lines.product_id.id", op, val]
        return ["lines.product_id.name", op, val]

    def onchange_date(self, context={}):
        data=self.onchange_sequence(context)
        data=self.onchange_currency(context)
        return data

    def search_location(self, clause, context={}):
        op = clause[1]
        val = clause[2]
        if isinstance(val, int):
            return ["lines.location_id.id", op, val]
        return ["lines.location_id.name", op, val]

    def find_po_line(self, ids, product_id, context={}):
        obj = self.browse(ids)[0]
        for line in obj.lines:
            if line.product_id.id == product_id:
                return line.id
        return None

PurchaseOrder.register()
