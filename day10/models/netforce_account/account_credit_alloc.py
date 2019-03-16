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
import time


class CreditAlloc(Model):
    _name = "account.credit.alloc"
    _fields = {
        "invoice_id": fields.Many2One("account.invoice", "Invoice", required=True, on_delete="cascade"),
        "credit_id": fields.Many2One("account.invoice", "Credit Note", required=True, on_delete="cascade"),
        "credit_type": fields.Char("Credit Type", function="_get_related", function_context={"path": "credit_id.inv_type"}),
        "amount": fields.Decimal("Amount"),
        "move_id": fields.Many2One("account.move", "Journal Entry"),
        "date": fields.Date("Date", required=True),
    }
    _defaults = {
        "date": lambda *a: time.strftime("%Y-%m-%d"),
    }

    def create(self, vals, **kw):
        new_id = super().create(vals, **kw)
        inv_id = vals["invoice_id"]
        cred_id = vals["credit_id"]
        get_model("account.invoice").function_store([inv_id, cred_id])
        self.post([new_id])
        return new_id

    def delete(self, ids, **kw):
        inv_ids = []
        for obj in self.browse(ids):
            inv_ids.append(obj.invoice_id.id)
            inv_ids.append(obj.credit_id.id)
            if obj.move_id:
                obj.move_id.void()
                obj.move_id.delete()
        super().delete(ids, **kw)
        get_model("account.invoice").function_store(inv_ids)

    def post(self, ids, context={}):
        settings = get_model("settings").browse(1)
        obj = self.browse(ids)[0]
        inv = obj.invoice_id
        contact = inv.contact_id
        cred = obj.credit_id
        if cred.inv_type == "credit":
            if inv.account_id.id!=cred.account_id.id:
                raise Exception("Difference account code to reconcile (%s / %s)"%(inv.account_id.code,cred.account_id.code))
            desc = "Credit allocation: %s" % cred.contact_id.name
            move_vals={
                "journal_id": cred.journal_id.id,
                "date": obj.date,
                "narration": desc,
                "lines": [],
            }
            move_id = get_model("account.move").create(move_vals)
            cred_cur_total = get_model("currency").convert(obj.amount, cred.currency_id.id, settings.currency_id.id, rate=cred.currency_rate)
            inv_cur_total = get_model("currency").convert(obj.amount, inv.currency_id.id, settings.currency_id.id, rate=inv.currency_rate)
            if inv.type == "in":
                sign = 1
            else:
                sign = -1
            amt_cred = cred_cur_total 
            amt_inv = inv_cur_total
            amt_cur=None
            if inv.type == "in":
                if inv.account_id.currency_id and inv.account_id.currency_id.id != settings.currency_id.id:
                    amt_cur=abs(obj.amount) #XXX
                line_vals={
                    "move_id": move_id,
                    "description": desc,
                    "account_id": cred.account_id.id,
                    "debit": 0,
                    "credit": amt_cred,
                    "contact_id": contact.id,
                    "amount_cur": obj.amount if inv.currency_id.id != settings.currency_id.id else 0,
                }
                if inv.account_id.currency_id.id==settings.currency_id.id:
                    line_vals['amount_cur']=0
                line1_id=get_model("account.move.line").create(line_vals)
                line_vals={
                    "move_id": move_id,
                    "description": desc,
                    "account_id": inv.account_id.id,
                    "debit": amt_inv,
                    "credit": 0,
                    "contact_id": contact.id,
                    "amount_cur":obj.amount if cred.currency_id.id != settings.currency_id.id else 0,
                }
                if cred.account_id.currency_id.id==settings.currency_id.id:
                    line_vals['amount_cur']=0
                line2_id=get_model("account.move.line").create(line_vals)
                if amt_cred != amt_inv:
                    amt_diff = amt_cred - amt_inv
                    if amt_diff > 0:
                        if not settings.currency_loss_id:
                            raise Exception("Missing currency loss account")
                        acc_id = settings.currency_loss_id.id
                    else:
                        if not settings.currency_gain_id:
                            raise Exception("Missing currency gain account")
                        acc_id = settings.currency_gain_id.id
                    line_vals = {
                        "move_id": move_id,
                        "description": desc,
                        "account_id": acc_id,
                        "debit": amt_diff > 0 and amt_diff or 0,
                        "credit": amt_diff < 0 and -amt_diff or 0,
                    }
                    get_model("account.move.line").create(line_vals) 
            else:
                if inv.account_id.currency_id and inv.account_id.currency_id.id != settings.currency_id.id:
                    amt_cur=abs(obj.amount) #XXX
                line_vals={
                    "move_id": move_id,
                    "description": desc,
                    "account_id": cred.account_id.id,
                    "debit": amt_cred,
                    "credit": 0,
                    "contact_id": contact.id,
                    "amount_cur": obj.amount if inv.currency_id.id != settings.currency_id.id else 0,
                }
                if inv.account_id.currency_id.id==settings.currency_id.id:
                    line_vals['amount_cur']=0
                line1_id=get_model("account.move.line").create(line_vals)
                line_vals={
                    "move_id": move_id,
                    "description": desc,
                    "account_id": inv.account_id.id,
                    "debit": 0,
                    "credit": amt_inv,
                    "contact_id": contact.id,
                    "amount_cur":obj.amount if cred.currency_id.id != settings.currency_id.id else 0,
                }
                if cred.account_id.currency_id.id==settings.currency_id.id:
                    line_vals['amount_cur']=0
                line2_id=get_model("account.move.line").create(line_vals)
                if amt_cred != amt_inv:
                    amt_diff = amt_inv - amt_cred
                    if amt_diff > 0:
                        if not settings.currency_loss_id:
                            raise Exception("Missing currency loss account")
                        acc_id = settings.currency_loss_id.id
                    else:
                        if not settings.currency_gain_id:
                            raise Exception("Missing currency gain account")
                        acc_id = settings.currency_gain_id.id
                    line_vals = {
                        "move_id": move_id,
                        "description": desc,
                        "account_id": acc_id,
                        "debit": amt_diff > 0 and amt_diff or 0,
                        "credit": amt_diff < 0 and -amt_diff or 0,
                    }
                    get_model("account.move.line").create(line_vals) 
            get_model("account.move").post([move_id])
            obj.write({"move_id": move_id})
            if not inv.move_id or not inv.move_id.lines:
                raise Exception("Failed to find invoice journal entry line to reconcile")
            inv_line_id=None
            if inv.type=="out":
                inv_line_id=inv.move_id.lines[0]
            else:
                for jv_line in inv.move_id.lines:
                    if jv_line.account_id.id==inv.account_id.id and jv_line.credit!=0:
                        inv_line_id=jv_line
                        break
            if not inv_line_id:
                raise Exception("Failed to find invoice journal entry line to reconcile")
            get_model("account.move.line").reconcile([inv_line_id.id,line1_id])
            if not cred.move_id or not cred.move_id.lines:
                raise Exception("Failed to find credit note journal entry line to reconcile")
            cred_line_id=None
            if cred.type=="in":
                cred_line_id=cred.move_id.lines[0]
            else:
                for jv_line in cred.move_id.lines:
                    if jv_line.account_id.id==inv_line_id.account_id.id and jv_line.credit!=0:
                        cred_line_id=jv_line
                        break
            if not cred_line_id:
                raise Exception("Failed to find credit note journal entry line to reconcile")
            get_model("account.move.line").reconcile([cred_line_id.id,line2_id])
        elif cred.inv_type == "prepay":
            # TODO: try to simplify this stuff...
            desc = "Credit allocation: %s" % cred.contact_id.name
            if inv.type == "out":
                journal_id = settings.sale_journal_id.id
                if not journal_id:
                    raise Exception("Sales journal not found")
            elif inv.type == "in":
                journal_id = settings.purchase_journal_id.id
                if not journal_id:
                    raise Exception("Purchases journal not found")
            move_vals = {
                "journal_id": journal_id,
                "date": obj.date,
                "narration": desc,
                "ref": "%s,%s"%(cred.number,inv.number),
            }
            lines = []
            use_ratio = obj.amount / cred.amount_total
            cur_total = get_model("currency").convert(obj.amount, cred.currency_id.id, settings.currency_id.id, rate=inv.currency_rate)
            if inv.type == "in":
                sign = 1
            else:
                sign = -1
            amt = cur_total * sign
            line_vals = {
                "description": desc,
                "account_id": inv.account_id.id,
                "debit": amt > 0 and amt or 0,
                "credit": amt < 0 and -amt or 0,
                "contact_id": contact.id,
                "amount_cur": obj.amount if inv.account_id.currency_id.id != settings.currency_id.id else None,
            }
            lines.append(line_vals)
            taxes = {}
            for line in cred.lines:
                cur_amt = get_model("currency").convert(line.amount * use_ratio, cred.currency_id.id, settings.currency_id.id, rate=cred.payment_id.currency_rate)
                tax = line.tax_id
                if tax:
                    base_amt = get_model("account.tax.rate").compute_base(tax.id, cur_amt, tax_type=cred.tax_type)
                    tax_comps = get_model("account.tax.rate").compute_taxes(tax.id, base_amt, when="invoice")
                    for comp_id, tax_amt in tax_comps.items():
                        if comp_id in taxes:
                            tax_vals = taxes[comp_id]
                            tax_vals["amount_base"] += base_amt
                            tax_vals["amount_tax"] += tax_amt
                        else:
                            tax_vals = {
                                "tax_comp_id": comp_id,
                                "amount_base": base_amt,
                                "amount_tax": tax_amt,
                            }
                            taxes[comp_id] = tax_vals
                else:
                    base_amt = cur_amt
                acc_id = line.account_id.id
                if not acc_id:
                    raise Exception("Missing line account")
                amt = base_amt * sign
                line_vals = {
                    "description": desc,
                    "account_id": acc_id,
                    "credit": amt > 0 and amt or 0,
                    "debit": amt < 0 and -amt or 0,
                    "track_id": line.track_id.id,
                    "amount_cur": line.amount if line.account_id.currency_id.id != settings.currency_id.id else None,
                }
                lines.append(line_vals)
            for comp_id, tax_vals in taxes.items():
                comp = get_model("account.tax.component").browse(comp_id)
                acc_id = comp.account_id.id
                if not acc_id:
                    raise Exception("Missing account for tax component %s" % comp.name)
                amt = tax_vals["amount_tax"] * sign
                line_vals = {
                    "description": desc,
                    "account_id": acc_id,
                    "credit": amt > 0 and amt or 0,
                    "debit": amt < 0 and -amt or 0,
                    "tax_comp_id": comp_id,
                    "tax_base": tax_vals["amount_base"],
                    "contact_id": contact.id,
                    "tax_no": inv.tax_no,
                }
                lines.append(line_vals)
            # update rounding, check this
            # idea is update credit(from ratio allocated amount) to be the same as debit
            total_credit = 0
            total_debit = 0
            for line in lines:
                total_credit += round(line["credit"],2)
                total_debit += round(line["debit"],2)
            total_diff_amt=total_debit - total_credit
            if total_diff_amt:
                debit=0
                credit=0
                if total_debit > total_credit:
                    credit=abs(total_diff_amt)
                else:
                    debit=abs(total_diff_amt)
                if not settings.rounding_account_id:
                    raise Exception("Missing rounding account")
                account_id = settings.rounding_account_id.id
                if amt > 0:
                    if not settings.currency_loss_id:
                        raise Exception("Missing currency loss account")
                    account_id = settings.currency_loss_id.id
                else:
                    if not settings.currency_gain_id:
                        raise Exception("Missing currency gain account")
                    account_id = settings.currency_gain_id.id
                line_vals = {
                    "description": desc,
                    "account_id": account_id,
                    "debit": debit,
                    "credit": credit,
                }
                lines.append(line_vals)
            move_vals["lines"] = [("create", vals) for vals in lines]
            move_id = get_model("account.move").create(move_vals)
            get_model("account.move").post([move_id])
            obj.write({"move_id": move_id})
            move=get_model("account.move").browse(move_id)
            move_line_id=None
            inv_line_id=None
            if not inv.move_id or not inv.move_id.lines:
                raise Exception("Failed to find invoice journal entry line to reconcile")
            if inv.type=="out":
                inv_line_id=inv.move_id.lines[0]
                for jv_line in move.lines:
                    if jv_line.account_id.id==inv_line_id.account_id.id and jv_line.credit!=0:
                        move_line_id=jv_line
                        break
            else:
                move_line_id=move.lines[0]
                for jv_line in inv.move_id.lines:
                    if jv_line.account_id.id==inv.account_id.id and jv_line.credit!=0:
                        inv_line_id=jv_line
                        break
            if not move_line_id:
                raise Exception("Failed to find credit note journal entry line to reconcile")
            if not inv_line_id:
                raise Exception("Failed to find credit note journal entry line to reconcile")
            get_model("account.move.line").reconcile([inv_line_id.id,move_line_id.id])

CreditAlloc.register()
