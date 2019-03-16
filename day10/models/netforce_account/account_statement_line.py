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
from decimal import Decimal

class StatementLine(Model):
    _name = "account.statement.line"
    _order = "date,id"
    _name_field = "description"
    _fields = {
        "statement_id": fields.Many2One("account.statement", "Statement", required=True, on_delete="cascade"),
        "state": fields.Selection([["not_reconciled", "Not Reconciled"], ["reconciled", "Reconciled"]], "Status", required=True),
        "date": fields.Date("Date", required=True),
        "description": fields.Char("Description", size=256),
        "spent": fields.Decimal("Spent", required=True),
        "received": fields.Decimal("Received", required=True),
        "balance": fields.Decimal("Balance", required=True, readonly=True),
        "bank_reconcile_id": fields.Many2One("account.bank.reconcile", "Bank Reconciliation"),
        "move_lines": fields.Many2Many("account.move.line", "Account Entries"),
        "account_id": fields.Many2One("account.account", "Account", function="_get_related", function_context={"path": "statement_id.account_id"}),
        "account_balance": fields.Decimal("Accounting Balance", function="get_account_balance", function_multi=True),
        "account_balance_cur": fields.Decimal("Accounting Balance Currency", function="get_account_balance", function_multi=True),
    }
    _defaults = {
        "state": "not_reconciled",
        "spent": 0,
        "received": 0,
        'balance': 0,
    }

    def get_reconcile_lines(self, ids):
        st_line_ids = set(ids)
        new_st_line_ids = set(ids)
        acc_line_ids = set()
        while 1:
            new_acc_line_ids = set()
            for st_line in get_model("account.statement.line").browse(list(new_st_line_ids)):
                for acc_line in st_line.move_lines:
                    if acc_line.id not in acc_line_ids and acc_line.id not in new_acc_line_ids:
                        new_acc_line_ids.add(acc_line.id)
            if not new_acc_line_ids:
                break
            acc_line_ids |= new_acc_line_ids
            new_st_line_ids = set()
            for acc_line in get_model("account.move.line").browse(list(new_acc_line_ids)):
                for st_line in acc_line.statement_lines:
                    if st_line.id not in st_line_ids and st_line.id not in new_st_line_ids:
                        new_st_line_ids.add(st_line.id)
            if not new_st_line_ids:
                break
            st_line_ids |= new_st_line_ids
        return list(st_line_ids), list(acc_line_ids)

    def reconcile(self, ids, context={}):
        settings = get_model('settings').browse(1)
        st_line_ids, acc_line_ids = self.get_reconcile_lines(ids)
        total_st = 0
        for st_line in get_model("account.statement.line").browse(st_line_ids):
            total_st += st_line.received - st_line.spent
        total_acc = 0
        for acc_line in get_model("account.move.line").browse(acc_line_ids):
            if settings.currency_id.id == acc_line.account_id.currency_id.id: # account currency is the same as default currency
                total_acc += acc_line.debit - acc_line.credit
            else: # account currency is different from default currency
                total_acc += acc_line.amount_cur or 0.0
        if total_st - Decimal(total_acc) != 0:
            return {
                "next": {
                    "name": "reconcile_adjust",
                    "line_id": ids[0],
                }
            }
        get_model("account.statement.line").write(st_line_ids, {"state": "reconciled"})
        get_model("account.move.line").write(acc_line_ids, {"state": "reconciled"})

    def unreconcile(self, ids, context={}):
        st_line_ids, acc_line_ids = self.get_reconcile_lines(ids)
        get_model("account.statement.line").write(st_line_ids, {"state": "not_reconciled"})
        get_model("account.move.line").write(acc_line_ids, {"state": "not_reconciled"})

    def get_account_balance(self, ids, context={}):
        vals = {}
        settings = get_model('settings').browse(1)
        for obj in self.browse(ids):
            bal = 0
            bal_cur = 0
            line_ids = set()
            for line in obj.move_lines:
                if line.id in line_ids:
                    continue
                bal += line.debit - line.credit
                if settings.currency_id.id != line.account_id.currency_id.id and line.debit: # account currency is different from default currency
                    bal_cur += line.amount_cur or 0.0
                elif settings.currency_id.id != line.account_id.currency_id.id and line.credit: # account currency is different from default currency
                    bal_cur -= line.amount_cur or 0.0
                line_ids.add(line.id)
            vals[obj.id] = { "account_balance": bal, "account_balance_cur": bal_cur }
        return vals

    def onchange_move_lines(self, context={}):
        data = context["data"]
        move_line_ids = data["move_lines"]
        move_line_ids = list(set(move_line_ids))
        bal = 0
        for line in get_model("account.move.line").browse(move_line_ids):
            bal += line.debit - line.credit
        data["account_balance"] = bal
        return data

StatementLine.register()
