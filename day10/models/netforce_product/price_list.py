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
from netforce import utils
import time


class PriceList(Model):
    _name = "price.list"
    _string = "Price List"
    _key = ["name"]
    _fields = {
        "name": fields.Char("Name", required=True, search=True),
        "type": fields.Selection([["sale", "Sales"], ["purchase", "Purchasing"]], "Type", required=True, search=True),
        "date": fields.Date("Date", search=True),
        "base_price": fields.Selection([["product", "List Price In Product"], ["other_pricelist", "Other Price List"], ["volume", "Product Volume"]], "Base Price"),
        "other_pricelist_id": fields.Many2One("price.list", "Other Price List"),
        "factor": fields.Decimal("Factor", scale=6),
        "discount": fields.Decimal("Discount"),  # XXX: deprecated
        "lines": fields.One2Many("price.list.item", "list_id", "Price List Items"),
        "comments": fields.One2Many("message", "related_id", "Comments"),
        "currency_id": fields.Many2One("currency", "Currency", required=True, search=True),
        "rounding": fields.Decimal("Rounding Multiple"),
        "rounding_method": fields.Selection([["nearest", "Nearest"], ["lower", "Lower"], ["upper", "Upper"]], "Rounding Method"),
        "sale_channels": fields.One2Many("sale.channel", "pricelist_id","Sales Channels"),
    }

    def _get_currency(self, context={}):
        settings = get_model("settings").browse(1)
        return settings.currency_id.id

    _defaults = {
        "date": lambda *a: time.strftime("%Y-%m-%d"),
        "currency_id": _get_currency,
    }

    def update_prices(self, ids, context={}):
        for obj in self.browse(ids):
            for line in obj.lines:
                prod = line.product_id
                factor = obj.factor or 1.0
                if obj.base_price == "product":
                    base_price = prod.sale_price
                elif obj.base_price == "other_pricelist":
                    if not obj.other_pricelist_id:
                        raise Exception("Missing base price list")
                    base_price = self.get_price(obj.other_pricelist_id.id, prod.id, 1)  # XXX: qty
                elif obj.base_price == "volume":
                    base_price = prod.volume or 0
                else:
                    raise Exception("Invalid base price type")
                price = utils.round_amount(base_price * factor, obj.rounding, obj.rounding_method)
                line.write({"price": price})

    def get_price(self, list_id, prod_id, qty, context={}):
        for item in get_model("price.list.item").search_browse([["list_id", "=", list_id], ["product_id", "=", prod_id]]):
            if item.min_qty and qty < item.min_qty:
                continue
            if item.max_qty and qty > item.max_qty:
                continue
            return item.price
        return 0

    def get_discount(self, list_id, prod_id, qty, context={}):
        print("get_discount", list_id, prod_id, qty)
        for item in get_model("price.list.item").search_browse([["list_id", "=", list_id], ["product_id", "=", prod_id]]):
            return item.discount_percent
        return None

PriceList.register()
