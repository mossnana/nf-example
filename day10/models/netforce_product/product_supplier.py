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

from netforce.model import Model, fields


class ProductSupplier(Model):
    _name = "product.supplier"
    _string = "Product Supplier"
    _key = ["product_id","sequence"]
    _fields = {
        "product_id": fields.Many2One("product", "Product", required=True, on_delete="cascade"),
        "sequence": fields.Integer("Sequence", required=True),
        "supplier_id": fields.Many2One("contact", "Supplier", required=True, condition=[["supplier","=",True]]),
        "supplier_product_code": fields.Char("Supplier Product Code"),
        "supplier_product_name": fields.Char("Supplier Product Name"),
    }

    _order = "sequence,id"

    def _get_sequence(self,context={}):
        seq = 0
        if context.get('data'):
            data = context['data']
            if data.get('suppliers'):
                for l in data['suppliers']:
                    if not l.get('sequence') or l['sequence'] <= seq: continue
                    seq = l['sequence']
        seq += 1
        return seq
      
    _defaults = {
        "sequence": _get_sequence,
    }

ProductSupplier.register()
