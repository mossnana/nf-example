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
from netforce.access import get_active_company

class AccountReconcileVAT(Model):
    _name = "account.reconcile.vat"
    _string = "Reconcile VAT"
    _audit_log = True
    _name_field = "number"
    _fields = {
        "number": fields.Char("Number",required=True,search=True),
        "type": fields.Selection([["out", "Receivable"], ["in", "Payable"]],"Type",required=True,search=True),
        "tax_type": fields.Selection([["vat", "VAT"], ["vat_defer", "Deferred VAT"]],"Tax Type",required=True,search=True),
        "tax_comp_id": fields.Many2One("account.tax.component","Tax Comp.",search=True,condition=[["type","in",["vat","vat_defer"]]]),
        "state": fields.Selection([["draft", "Draft"], ["posted", "Posted"]],"Status",required=True,search=True),
        "memo": fields.Char("Memo",search=True),
        "date_from": fields.Date("Date From"),
        "date_to": fields.Date("Date To"),
        "claim_date": fields.Date("Claim Date",required=True,search=True),
        "doc_date": fields.Date("Document Date",required=True,search=True),
        "account_id": fields.Many2One("account.account","Revert Account",required=True,search=True),
        "account_ids": fields.Text("Account IDS"),
        "company_id": fields.Many2One("company","Company",required=True),
        "lines": fields.One2Many("account.reconcile.vat.line", "rec_id", "Lines"),
        "move_id": fields.Many2One("account.move","Move ID"),
        "moves": fields.One2Many("account.move","related_id","Journal Entries"),
    }

    _order = "number desc"

    def _get_number(self, context={}):
        seq_id = context.get("sequence_id")
        if not seq_id:
            seq_id = get_model("sequence").find_sequence(type="rec_vat")
        if not seq_id:
            return None
        while 1:
            num = get_model("sequence").get_next_number(seq_id, context=context)
            res = self.search([["number", "=", num]])
            if not res:
                return num
            get_model("sequence").increment_number(seq_id, context=context)

    _defaults = {
        "number": _get_number,
        "tax_type": "vat_defer",
        "company_id": lambda *a: get_active_company(),
        "state": "draft",
    }

    def delete(self,ids,context={}):
        for obj in self.browse(ids):
            if obj.state not in ["draft"]:
                raise Exception("Can't delete with this status in number ",obj.number)
        super().delete(ids,context)

    def post(self,ids,context={}):
        obj = self.browse(ids)[0]
        setting = get_model("settings").browse(1)
        if not setting.general_journal_id:
            raise Exception("Missing general journal in setting")
        if obj.tax_comp_id and obj.tax_comp_id.tax_type == obj.tax_type:
            raise Exception("Can't post transaction of same tax type (%s,%s)"%(obj.tax_comp_id.tax_type,obj.tax_type))
        if obj.memo:
            desc = obj.memo
        elif obj.type == "out" and obj.tax_type == "vat":
            desc = "Reverse Output Vat to Output Vat Suspense"
        elif obj.type == "out" and obj.tax_type == "vat_defer":
            desc = "Reverse Output Vat Suspense to Output Vat"
        elif obj.type == "in" and obj.tax_type == "vat":
            desc = "Reverse Input Vat to Input Vat Suspense"
        else:
            desc = "Reverse Input Vat Suspense to Input Vat"
        reconcile_ids = []
        cond = [["type","=",obj.type]]
        tax_comp_id = None
        if not obj.tax_comp_id:
            vat = []
            if obj.tax_type == "vat":
                tax_comp_type = "vat_defer"
            else:
                tax_comp_type = "vat"
            for tax in get_model("account.tax.rate").search_browse(cond):
                for l in tax.components:
                    if l.type not in ["vat","vat_defer"]: continue
                    vat.append(l.tax_type)
                    if l.type == tax_comp_type:
                        tax_comp_id = l.id
                if "vat" in vat and "vat_defer" in vat: break
                else: vat = []
        else:
            tax_comp_id = obj.tax_comp_id.id
        if not tax_comp_id:
            raise Exception("Missing tax component")
        vals = {
            "journal_id":setting.general_journal_id.id,
            "narration": desc,
            "date": obj.doc_date,
            "related_id":"%s,%s"%(obj._model,obj.id),
        }
        move_id = get_model("account.move").create(vals,context=vals)
        for line in obj.lines:
            amt = line.tax_amount or 0
            if obj.type == "in":
                amt = -amt
            if not line.tax_no:
                raise Exception("Missing tax invoice number in line ")
            line_vals = {
                "move_id": move_id,
                "description": line.move_line_id.description,
                "account_id": line.move_line_id.account_id.id,
                "debit": amt > 0 and amt or 0,
                "credit": amt < 0 and -amt or 0,
                "track_id": line.move_line_id.track_id.id,
                "track2_id": line.move_line_id.track2_id.id,
                "amount_cur": line.move_line_id.amount_cur,
                "contact_id": line.move_line_id.contact_id.id,
                "tax_comp_id": line.move_line_id.tax_comp_id.id,
                "tax_base": line.tax_base,
                "tax_date": line.tax_date,
                "revert_reconcile_id": obj.id,
            }
            move_line_id = get_model("account.move.line").create(line_vals)
            reconcile_ids.append([move_line_id, line.move_line_id.id])
            amt = -amt
            line_vals = {
                "move_id": move_id,
                "description": line.move_line_id.description,
                "account_id": obj.account_id.id,
                "debit": amt > 0 and amt or 0,
                "credit": amt < 0 and -amt or 0,
                "track_id": line.move_line_id.track_id.id,
                "track2_id": line.move_line_id.track2_id.id,
                "amount_cur": line.move_line_id.amount_cur,
                "contact_id": line.contact_id.id,
                "tax_comp_id": tax_comp_id,
                "tax_base": line.tax_base,
                "tax_date": line.tax_date,
                "tax_no": line.tax_no,
            }
            move_line_id = get_model("account.move.line").create(line_vals)
        for rec_lines in reconcile_ids:
            get_model("account.move.line").reconcile(rec_lines)
        get_model("account.move").post([move_id])
        obj.write({"state":"posted","move_id":move_id})
        return {
            "next": {
                "name" : "view_journal",
                "active_id" : move_id,
            },
            "flash": "Reverse vat success"
        }

    def fill_tax(self,ids,context={}):
        obj=self.browse(ids)[0]
        cond = [["move_state","=","posted"],["tax_comp_id.type","=",obj.tax_type],["tax_comp_id.trans_type","=",obj.type]]
        if obj.date_from:
            cond+=[["move_date",">=",obj.date_from]]
        if obj.date_to:
            cond+=[["move_date","<=",obj.date_to]]
        else:
            cond+=[["move_date","<=",obj.doc_date]]
        if obj.lines:
            obj.lines.delete()
        print(cond)
        move_ids = [rec_line.move_line_id.id for rec_line in get_model("account.reconcile.vat.line").search_browse([])]
        count = 0
        for line in get_model("account.move.line").search_browse(cond):
            if line.reconcile_id and line.reconcile_id.balance == 0: continue
            if line.id in move_ids: continue
            if obj.type == "in":
                tax_amount = line.debit or 0
            else:
                tax_amount = line.credit or 0
            if not tax_amount: continue
            tax_no = line.tax_no
            if line.invoice_id:
                ref = line.invoice_id
            elif line.related_id:
                ref = line.related_id
            elif line.move_id.related_id:
                ref = line.move_id.related_id 
            else:
                ref = line
            if ref.get('tax_no') and not tax_no:
                tax_no = ref.get('tax_no')
            if not line.contact_id: continue
            contact_id = line.contact_id.id
            related = "%s,%s"%(ref._model,ref.id)
            vals = {
                "tax_date": line.tax_date,
                "rec_id": obj.id,
                "related_id": related,
                "contact_id": contact_id,
                "tax_base": line.tax_base,
                "tax_amount": tax_amount,
                "tax_no": tax_no,
                "move_line_id": line.id,
            }
            get_model("account.reconcile.vat.line").create(vals)
            count += 1
        if not count or count <= 0:
            message = "Don't have data."
        else:
            message = "Filter success.Get %s items"%count
        return {
            "next" : {
                "name" : "account_reconcile_vat",
                "mode" : "form",
                "active_id": obj.id,
            },"flash": message
        }

    def clear_tax(self,ids,context={}):
        for obj in self.browse(ids):
            obj.lines.delete()

    def get_tax_comp(self,tax_comp=None,tax_type=None,context={}):
        if not tax_comp:
            raise Exception("Missing tax component")
        if not tax_type:
            raise Exception("Missing tax type")
        for line in tax_comp.tax_rate_id.components:
            if line.type != tax_type: continue
            return line.id

    def view_journal_entry(self, ids, context={}):
        obj = self.browse(ids)[0]
        return {
            "next": {
                "name": "journal_entry",
                "mode": "form",
                "active_id": obj.move_id.id,
            }
        }

    def to_draft(self,ids,context={}):
        obj=self.browse(ids)[0]
        if obj.move_id:
            obj.move_id.void()
            obj.move_id.delete()
        obj.write({"state":"draft"})
        return {
            "next" : {
                "name" : "account_reconcile_vat",
                "mode" : "form",
                "active_id": obj.id,
            },
        }

    def onchange_date(self,context={}):
        data = context['data']
        if data.get('doc_date'):
            ctx = {
                "date": data['doc_date']
            }
            data['number'] = self._get_number(context=ctx)
        return data

    def update_account_ids(self,context={}):
        data = context['data']
        if not data.get('type'): return data
        acc_ids = []
        for comp in get_model("account.tax.component").search_browse([["tax_rate_id.type","=",data['type']]]):
            if comp.type not in ["vat","vat_exempt","vat_defer"]: continue 
            if not comp.account_id: continue
            if comp.account_id.id not in acc_ids:
                acc_ids.append(comp.account_id.id)
        data['account_ids'] = acc_ids
        return data

AccountReconcileVAT.register()
