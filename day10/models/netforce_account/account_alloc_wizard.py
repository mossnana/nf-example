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


class AllocWizard(Model):
    _name = "account.alloc.wizard"
    _transient = True
    _fields = {
        "credit_id": fields.Many2One("account.invoice", "Credit Note", required=True, on_delete="cascade"),
        "type": fields.Char("Type"),
        "lines": fields.One2Many("account.alloc.wizard.line", "wiz_id", "Lines"),
        "amount_credit": fields.Decimal("Outstanding Credit", readonly=True),
        "amount_alloc": fields.Decimal("Total Amount to Credit", readonly=True),
        "amount_remain": fields.Decimal("Remaining Credit", readonly=True),
    }

    def default_get(self,field_names={},context={},**kw):
        if "credit_id" not in context:
            return {}
        credit_id = int(context["credit_id"])
        cred = get_model("account.invoice").browse(credit_id)
        contact_id = cred.contact_id.id
        lines = []
        for inv in get_model("account.invoice").search_browse([["type", "=", cred.type], ["inv_type", "=", "invoice"], ["contact_id", "=", contact_id], ["state", "=", "waiting_payment"], ["currency_id", "=", cred.currency_id.id]]):
            lines.append({
                "invoice_id": [inv.id, inv.name_get()[0][1]],
                "date": inv.date,
                "amount_total": inv.amount_total,
                "amount_due": inv.amount_due,
            })
        vals = {
            "credit_id": [cred.id, cred.name_get()[0][1]],
            "lines": lines,
            "type": cred.type,
            "amount_credit": cred.amount_credit_remain,
            "amount_alloc": 0,
            "amount_remain": cred.amount_credit_remain,
        }
        return vals

    def allocate(self, ids, context={}):
        obj = self.browse(ids)[0]
        for line in obj.lines:
            if not line.amount:
                continue
            vals = {
                "credit_id": obj.credit_id.id,
                "invoice_id": line.invoice_id.id,
                "amount": line.amount,
            }
            get_model("account.credit.alloc").create(vals)
        return {
            "next": {
                "name": "view_invoice",
                "active_id": obj.credit_id.id,
            },
            "flash": "Credit allocated.",
        }

    def onchange_amount(self, context={}):
        data = context["data"]
        amt = 0
        for line in data["lines"]:
            amt += line.get("amount", 0)
        data["amount_alloc"] = amt
        data["amount_remain"] = data["amount_credit"] - amt
        return data

AllocWizard.register()
