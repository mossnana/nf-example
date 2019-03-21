# Copyright (c) 2012-2015 Netforce Co. Ltd.
#-
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#-
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#-
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from netforce.model import Model,fields,get_model
from netforce.access import get_active_company

class PettyCashFund(Model):
    _name = "petty.cash.fund"
    _multi_company = True
    _key = ["name","company_id"]
    _fields = {
        "name":fields.Char("Name",required=True,search=True),
        "code":fields.Char("Code",required=True,search=True),
        "max_amt":fields.Decimal("Max Amount",required=True),
        "min_amt":fields.Decimal("Minimum Amount",required=True),
        "account_id":fields.Many2One("account.account","Petty Cash Account", required=True, search=True),
        "acc_bal":fields.Decimal("Current Balance",function="get_balance"),
        "company_id":fields.Many2One("company","Company"),
        "track_id": fields.Many2One("account.track.categ", "Track-1", condition=[["type", "=", "1"]], search=True),
        "track2_id": fields.Many2One("account.track.categ", "Track-2", condition=[["type", "=", "2"]], search=True),
        "number_receive":fields.Many2One("petty.cash","Petty Cash Receive"),
        # Fix Issued 477
        "state": fields.Selection([("draft", "Draft"), ("approved", "Approved"), ("voided", "Voided")], "Status", required=True),
        "currency_id": fields.Many2One("currency", "Currency", required=True),
        }

    _defaults = {
        "company_id":lambda *a: get_active_company(),
        "state": "draft",
        }

    
    def write(self, ids, vals, **kw):
        context=kw.get('context')
        max_amount = vals.get("max_amt") or self.browse(ids)[0].max_amt
        min_amount = vals.get("min_amt") or self.browse(ids)[0].min_amt
        if min_amount > max_amount:
            raise Exception("Max Amount can't less than Minimum Amount")
        super().write(ids, vals, **kw)
        self.function_store(ids)
        return ids

    def create(self, vals, **kw): 
        context=kw.get('context')
        max_amount = vals.get("max_amt")
        min_amount = vals.get("min_amt")
        if min_amount > max_amount:
            raise Exception("Max Amount can't less than Minimum Amount")
        new_id = super().create(vals, **kw)
        return new_id

    def get_balance(self,ids,context={}):
        val = {}
        for obj in self.browse(ids):
            ctx = {
                "track_id": obj.track_id.id,
                "track2_id": obj.track2_id.id,
                "active_test": False,
            }
            res = get_model("account.account").search_read(["id", "=", obj.account_id.id], ["balance"], context=ctx)
            res = res[0]["balance"]
            val[obj.id] = res 
        return val

    def delete(self, ids, context={}):
        state = self.browse(ids[0])
        number_receive = get_model("petty.cash").search_read(["fund_id", "=", ids[0]], ["fund_id"], context=context) or None
        if number_receive:
            raise Exception("Have Petty Cash Received")
        else:
            if state.state not in ("approved", "voided"):
                super().delete(ids)
            else:
                raise Exception("Petty Cash Fund approved or voided")
        return {
            "flash": "Petty Cash Fund deleted"
        }

    def onchange_account(self,context={}):
        data = context["data"]
        ctx = {
            "track_id": data["track_id"],
            "track2_id": data["track2_id"],
            "active_test": False,
        }
        res = get_model("account.account").search_read(["id", "=", data["account_id"]], ["balance"], context=ctx)
        res2 = get_model("account.account").search_read(["id", "=", data["account_id"]], ["currency_id"], context=ctx)
        if res:
            data["acc_bal"] = res[0]["balance"]
            if res2:
                data["currency_id"] = res2[0]["currency_id"]
        return data

    def approve(self, ids, context={}):
        obj = self.browse(ids)[0]
        if not obj.state == "draft":
            raise Exception("Invalid state")
        else:
            obj.write({"state": "approved"})
            return {
                "flash": "Document approved",
            }

    def to_draft(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state == "draft":
            raise Exception("{} is drafting".format(obj.name))
        else:
            obj.write({"state": "draft"})
        return {
            "flash": "To Draft",
        }

    def void(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state != "voided":
            if not obj.number_receive or obj.number_receive == " ":
                obj.write({"state": "voided"})
            else:
                raise Exception("This Petty Cash Fund is related with Petty Cash Received")
        else:
            raise Exception("{} can't voided".format(obj.name))
        return {
            "flash": "Voided",
        }

PettyCashFund.register()

