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


class BatchImportPurchaseInvoice(Model):
    _name = "batch.import.purchase.invoice"
    _fields = {
        "import_id": fields.Many2One("batch.import", "Import", required=True, on_delete="cascade"),
        "date": fields.Date("Date", required=True),
        "number": fields.Text("Invoice No."),
        "contact": fields.Char("Supplier Name"),
        "description": fields.Text("Description"),
        "amount": fields.Decimal("Amount"),
        "account_id": fields.Many2One("account.account", "Expense Account"),
        "tax_id": fields.Many2One("account.tax.rate", "Tax Rate"),
        "invoice_id": fields.Many2One("account.invoice", "Invoice"),
    }

BatchImportPurchaseInvoice.register()
