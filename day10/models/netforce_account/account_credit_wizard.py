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

import time
from netforce.model import Model, fields, get_model
from netforce.utils import get_data_path
import time

class CreditWizard(Model):
    _name = "account.credit.wizard"
    _transient = True
    _fields = {
        "invoice_id": fields.Many2One("account.invoice", "Invoice", required=True, on_delete="cascade"),
        "contact_id": fields.Many2One("contact", "Contact", required=True, on_delete="cascade"),
        "currency_id": fields.Many2One("currency", "Currency", required=True, on_delete="cascade"),
        "date": fields.Date("Date Allocate"),
        "type": fields.Char("Type"),
        "lines": fields.One2Many("account.credit.wizard.line", "wiz_id", "Lines"),
        "amount_due": fields.Decimal("Amount Due on Invoice", readonly=True),
        "amount_alloc": fields.Decimal("Total Amount to Credit", readonly=True),
        "amount_remain": fields.Decimal("Remaining Due", readonly=True),
    }

    def default_get(self, field_names={}, context={}, **kw):
        if "invoice_id" not in context:
            return {}
        inv_id = int(context["invoice_id"])
        inv = get_model("account.invoice").browse(inv_id)
        contact_id = inv.contact_id.id
        lines = []
        for cred in get_model("account.invoice").search_browse([["type", "=", inv.type], ["inv_type", "in", ("credit", "prepay", "overpay")], ["contact_id", "=", contact_id], ["state", "=", "waiting_payment"], ["currency_id", "=", inv.currency_id.id]]):
            lines.append({
                "credit_id": [cred.id, cred.name_get()[0][1]],
                "date": cred.date,
                "amount_credit_remain": cred.amount_credit_remain,
            })
        vals = {
            "invoice_id": [inv.id, inv.name_get()[0][1]],
            "lines": lines,
            "type": inv.type,
            "contact_id": inv.contact_id.id,
            "currency_id": inv.currency_id.id,
            "date": time.strftime("%Y-%m-%d"),
            "amount_due": inv.amount_due,
            "amount_alloc": 0,
            "amount_remain": inv.amount_due,
            "date": time.strftime("%Y-%m-%d"),
        }
        return vals

    def allocate(self, ids, context={}):
        obj = self.browse(ids)[0]
        assert obj.invoice_id.inv_type in ("invoice","credit","debit")
        for line in obj.lines:
            if not line.amount:
                continue
            vals = {
                "invoice_id": obj.invoice_id.id,
                "credit_id": line.credit_id.id,
                "amount": line.amount,
                "date": obj.date,
            }
            get_model("account.credit.alloc").create(vals)
        return {
            "next": {
                "name": "view_invoice",
                "active_id": obj.invoice_id.id,
            },
            "flash": "Invoice updated.",
        }

    def update_amounts(self, context={}):
        data = context["data"]
        amt = 0
        for line in data["lines"]:
            amt += line.get("amount") or 0
        data["amount_alloc"] = amt
        data["amount_remain"] = data["amount_due"] - amt
        return data

    def onchange_credit(self,context={}):
        data = context['data']
        path = context['path']
        line = get_data_path(data,path,parent=True)
        if line.get("credit_id"):
            credit_id = int(line["credit_id"])
            cred = get_model("account.invoice").browse(credit_id)
            line["date"] = cred.date
            line["amount_credit_remain"] = cred.amount_credit_remain
        self.update_amounts(context=context)
        return data

CreditWizard.register()
