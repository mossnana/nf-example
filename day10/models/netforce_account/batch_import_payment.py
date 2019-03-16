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


class BatchImportPayment(Model):
    _name = "batch.import.payment"
    _fields = {
        "import_id": fields.Many2One("batch.import", "Import", required=True, on_delete="cascade"),
        "type": fields.Selection([["cash", "Cash"], ["bank", "Bank"]], "Type", required=True),
        "date": fields.Date("Date", required=True),
        "description": fields.Text("Description"),
        "received": fields.Decimal("Received"),
        "spent": fields.Decimal("Spent"),
        "invoice_no": fields.Char("Invoice No."),
        "other_account_id": fields.Many2One("account.account", "Other Account"),
        "payment_id": fields.Many2One("account.payment", "Payment"),
    }

BatchImportPayment.register()
