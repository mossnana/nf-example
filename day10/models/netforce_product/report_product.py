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
from netforce.database import get_connection
from netforce.access import get_active_company
import time
from datetime import *
from pprint import pprint


class ReportProduct(Model):
    _name = "report.product"
    _store = False

    def products_per_categ(self, context={}):
        db = get_connection()
        company_id = get_active_company()
        res = db.query("SELECT product_categ_id FROM m2m_company_product_categ WHERE company_id IS NOT NULL AND company_id != %s",company_id)
        categ_ids = [r.product_categ_id for r in res]
        if not categ_ids:
            res = db.query(
                "SELECT c.name,COUNT(*) FROM product mc JOIN product_categ c ON mc.categ_id = c.id GROUP BY c.name")
        else:
            res = db.query(
                "SELECT c.name,COUNT(*) FROM product mc JOIN product_categ c ON mc.categ_id = c.id " \
                "WHERE c.id NOT IN %s "\
                "GROUP BY c.name",tuple(categ_ids))
        data = []
        for r in res:
            data.append((r.name, r.count))
        return {"value": data}


ReportProduct.register()
