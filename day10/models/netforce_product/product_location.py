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
from netforce.access import get_active_company


class ProductLocation(Model):
    _name = "product.location"
    _string = "Product Location"
    _key = ["product_id","sequence"]
    _multi_company = True
    _fields = {
        "product_id": fields.Many2One("product","Product",required=True,on_delete="cascade"),
        "sequence": fields.Integer("Sequence",required=True),
        "location_id": fields.Many2One("stock.location","Warehouse",required=True),
        "bin_location": fields.Char("Bin Location"),
        "stock_qty": fields.Decimal("Stock Qty",function="get_stock_qty"),
        "company_id": fields.Many2One("company","Company", search=True),
    }
    _order = "sequence"
    _defaults={
        "sequence": 1,
        'company_id': lambda *a: get_active_company(),
    }

    def get_stock_qty(self,ids,context={}):
        keys = []
        for obj in self.browse(ids):
            if obj.product_id.type == "bundle":
                for comp in obj.product_id.components:
                    key = (comp.component_id.id, None, obj.location_id.id, None)
                    keys.append(key)
            else:
                key = (obj.product_id.id, None, obj.location_id.id, None)
                keys.append(key)
        bals = get_model("stock.balance").compute_key_balances(keys,context={"virt_stock":True})
        vals = {}
        for obj in self.browse(ids):
            if obj.product_id.type == "bundle":
                comps_qty = []
                for comp in obj.product_id.components:
                    key = (comp.component_id.id, None, obj.location_id.id, None) 
                    qty = bals[key][0]
                    comps_qty.append(int(qty/comp.qty))
                vals[obj.id] = min(comps_qty or [0])
            else:
                key = (obj.product_id.id, None, obj.location_id.id, None)
                qty = bals[key][0]
                vals[obj.id] = qty
        return vals

ProductLocation.register()
