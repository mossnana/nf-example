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
from netforce.action import get_action


class ConvSaleInvoice(Model):
    _name = "conv.sale.invoice"
    _transient = True
    _fields = {
        "conv_id": fields.Many2One("conv.bal", "Conversion", required=True),
        "number": fields.Char("Number", required=True),
        "ref": fields.Char("Reference"),
        "contact_id": fields.Many2One("contact", "Contact", required=True, on_delete="cascade"),
        "date": fields.Date("Date", required=True),
        "due_date": fields.Date("Due Date", required=True),
        "amount_due": fields.Decimal("Amount Due", required=True),
        "move_line_id": fields.Many2One("account.move.line", "Move Line"),
        "account_id": fields.Many2One("account.account", "Account", required=True),
        "amount_cur": fields.Decimal("Currency Amt"),
        "track_id": fields.Many2One("account.track.categ", "Track-1", condition=[["type", "=", "1"]]),
        "track2_id": fields.Many2One("account.track.categ", "Track-2", condition=[["type", "=", "2"]]),
    }

ConvSaleInvoice.register()
