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

class AccountReconcileVATLine(Model):
    _name = "account.reconcile.vat.line"
    _name_field = "rec_id"
    _fields = {
        "rec_id": fields.Many2One("account.reconcile.vat","Reconcile ID",required=True,on_delete="cascade"),
        "tax_date": fields.Date("Tax Date"),
        "related_id": fields.Reference([["account.invoice", "Invoice"], ["account.payment", "Payment"], ["account.move","Move"]],"Related To",required=True),
        "tax_no": fields.Char("Tax No."),
        "contact_id": fields.Many2One("contact","Contact",required=True),
        "tax_base": fields.Decimal("Tax Base",required=True),
        "tax_amount": fields.Decimal("Tax Amount",required=True),
        "move_line_id": fields.Many2One("account.move.line","Move Line ID",required=True), #Use To Reconcile
    }

    _order = "tax_date desc"

AccountReconcileVATLine.register()
