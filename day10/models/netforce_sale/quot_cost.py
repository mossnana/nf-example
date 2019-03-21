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
from decimal import Decimal

class QuotCost(Model):
    _name = "quot.cost"
    _string = "Cost"
    _fields = {
        "quot_id": fields.Many2One("sale.quot","Quotation",required=True,on_delete="cascade"),
        "sequence": fields.Char("Apply To Item No."),
        "product_id": fields.Many2One("product","Cost Product"),
        "description": fields.Text("Description",required=True,search=True),
        "unit_price": fields.Decimal("Unit Price"), # XXX deprecated
        "list_price": fields.Decimal("Supplier List Price"),
        "purchase_price": fields.Decimal("Purchase Price"),
        "purchase_duty_percent": fields.Decimal("Import Duty (%)"),
        "purchase_ship_percent": fields.Decimal("Shipping Charge (%)"),
        "landed_cost": fields.Decimal("Landed Cost"),
        "qty": fields.Decimal("Qty"),
        "uom_id": fields.Many2One("uom","UoM"), # XXX deprecated
        "amount": fields.Decimal("Cost Amount",function="get_amount"),
        "amount_conv": fields.Decimal("Cost Amount(Cur)",function="get_amount_conv"),
        "currency_id": fields.Many2One("currency","Currency"),
        "currency_rate": fields.Decimal("Currency Rate", scale=8), # XXX deprecated
        "supplier_id": fields.Many2One("contact","Supplier"),
    }

    _defaults={
        'sequence': '',
    }

    def get_amount(self,ids,context={}):
        vals={}
        settings = get_model('settings').browse(1)
        currency_id = settings.currency_id.id
        for obj in self.browse(ids):
            amount = (obj.qty or 0)*(obj.landed_cost or 0)
            prod = obj.product_id
            if prod.purchase_currency_id:
                if prod.purchase_currency_id.id == settings.currency_id.id:
                    amount = amount
                else:
                    cost_conv = get_model("currency").convert(amount, prod.purchase_currency_id.id, currency_id, date=obj.quot_id.date)
                    amount = cost_conv
            else:
                amount = amount
            vals[obj.id]=amount
        return vals

    def get_amount_conv(self,ids,context={}):
        vals={}
        conv_amount=0
        settings = get_model('settings').browse(1)
        for obj in self.browse(ids):
            prod = obj.product_id
            if prod.purchase_currency_id:
                if prod.purchase_currency_id.id == settings.currency_id.id:
                    if obj.quot_id.currency_id.id == settings.currency_id.id:
                        conv_amount = obj.amount
                    else:
                        cost_conv = get_model("currency").convert(obj.amount, settings.currency_id.id, obj.quot_id.currency_id.id, date=obj.quot_id.date)
                        conv_amount = cost_conv
                else:
                    #cost = get_model("currency").convert(obj.amount, prod.purchase_currency_id.id, settings.currency_id.id, date=obj.quot_id.date)
                    cost_conv = get_model("currency").convert(obj.amount, settings.currency_id.id, obj.quot_id.currency_id.id, date=obj.quot_id.date)
                    conv_amount = cost_conv
            else:
                if obj.quot_id.currency_id.id != settings.currency_id.id:
                    cost = get_model("currency").convert(obj.amount, obj.quot_id.currency_id.id, settings.currency_id.id, date=obj.quot_id.date)
                    cost_conv = get_model("currency").convert(cost, settings.currency_id.id, obj.quot_id.currency_id.id, date=obj.quot_id.date)
                    conv_amount = cost_conv
                else:
                    conv_amount = obj.amount
            vals[obj.id]=conv_amount
        return vals


QuotCost.register()
