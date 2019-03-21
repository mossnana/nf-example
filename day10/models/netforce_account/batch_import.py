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
from netforce.utils import get_file_path
from io import StringIO
import csv
from datetime import *
from dateutil.relativedelta import *
import time


def parse_date(s, fmt):
    s = s.strip()
    if not s:
        return None
    d = datetime.strptime(s, fmt)
    return d.strftime("%Y-%m-%d")


def parse_float(s):
    s = s.strip()
    if not s:
        return None
    s = s.replace(",", "")
    return float(s)


def get_account(s):
    s = s.strip()
    if not s:
        return None
    res = get_model("account.account").search([["code", "=", s]])
    if not res:
        raise Exception("Account not found: %s" % s)
    return res[0]


def get_tax_rate(s):
    s = s.strip()
    if not s:
        return None
    res = get_model("account.tax.rate").search([["code", "=", s]])
    if not res:
        raise Exception("Tax rate not found: %s" % s)
    return res[0]


def get_invoice(s):
    s = s.strip()
    if not s:
        return None
    res = get_model("account.invoice").search([["number", "=", s]])
    if not res:
        raise Exception("Invoice not found: %s" % s)
    return res[0]


def merge_contact(s):
    s = s.strip()
    if not s:
        return None
    res = get_model("contact").search([["name", "=", s]])
    if res:
        return res[0]
    vals = {
        "name": s,
    }
    new_id = get_model("contact").create(vals)
    return new_id


class BatchImport(Model):
    _name = "batch.import"
    _string = "Batch Import"
    _fields = {
        "from_date": fields.Date("From Date", required=True, search=True),
        "to_date": fields.Date("To Date", required=True),
        "cash_account_id": fields.Many2One("account.account", "Cash Account"),
        "bank_account_id": fields.Many2One("account.account", "Bank Account"),
        "cash_payments": fields.One2Many("batch.import.payment", "import_id", "Cash Payments", condition=[["type", "=", "cash"]]),
        "bank_payments": fields.One2Many("batch.import.payment", "import_id", "Bank Payments", condition=[["type", "=", "bank"]]),
        "sale_invoices": fields.One2Many("batch.import.sale.invoice", "import_id", "Sales Invoices"),
        "purchase_invoices": fields.One2Many("batch.import.purchase.invoice", "import_id", "Purchase Invoices"),
        "cash_file": fields.File("Cash File"),
        "bank_file": fields.File("Bank File"),
        "sale_file": fields.File("Sales File"),
        "purchase_file": fields.File("Purchases File"),
        "date_fmt": fields.Char("Date Format"),
        "state": fields.Selection([["draft", "Draft"], ["posted", "Posted"]], "Status", required=True),
    }
    _order = "from_date,id"

    def _get_cash_account(self, context={}):
        res = get_model("account.account").search([["type", "=", "cash"]], order="code")
        if not res:
            return None
        return res[0]

    def _get_bank_account(self, context={}):
        res = get_model("account.account").search([["type", "=", "bank"]], order="code")
        if not res:
            return None
        return res[0]

    _defaults = {
        "state": "draft",
        "date_fmt": "%m/%d/%Y",
        "from_date": lambda *a: time.strftime("%Y-%m-01"),
        "to_date": lambda *a: (date.today() + relativedelta(day=31)).strftime("%Y-%m-%d"),
        "cash_account_id": _get_cash_account,
        "bank_account_id": _get_bank_account,
    }

    def clear_data(self, ids, context={}):
        obj = self.browse(ids)[0]
        obj.cash_payments.delete()
        obj.bank_payments.delete()
        obj.sale_invoices.delete()
        obj.purchase_invoices.delete()

    def import_files(self, ids, context={}):
        obj = self.browse(ids)[0]
        obj.clear_data()
        if obj.cash_file:
            obj.import_cash_file()
        if obj.bank_file:
            obj.import_bank_file()
        if obj.sale_file:
            obj.import_sale_file()
        if obj.purchase_file:
            obj.import_purchase_file()

    def import_cash_file(self, ids, context={}):
        obj = self.browse(ids)[0]
        path = get_file_path(obj.cash_file)
        data = open(path).read()
        rd = csv.reader(StringIO(data))
        headers = next(rd)
        headers = [h.strip() for h in headers]
        for row in rd:
            print("row", row)
            line = dict(zip(headers, row))
            print("line", line)
            vals = {
                "import_id": obj.id,
                "type": "cash",
                "date": parse_date(line["Date"], obj.date_fmt),
                "description": line["Description"],
                "received": parse_float(line["Received"]),
                "spent": parse_float(line["Spent"]),
                "invoice_no": line["Invoice No."],
                "other_account_id": get_account(line["Other Account"]),
            }
            get_model("batch.import.payment").create(vals)

    def import_bank_file(self, ids, context={}):
        obj = self.browse(ids)[0]
        path = get_file_path(obj.bank_file)
        data = open(path).read()
        rd = csv.reader(StringIO(data))
        headers = next(rd)
        headers = [h.strip() for h in headers]
        for row in rd:
            print("row", row)
            line = dict(zip(headers, row))
            print("line", line)
            vals = {
                "import_id": obj.id,
                "type": "bank",
                "date": parse_date(line["Date"], obj.date_fmt),
                "description": line["Description"],
                "received": parse_float(line["Received"]),
                "spent": parse_float(line["Spent"]),
                "invoice_no": line["Invoice No."],
                "other_account_id": get_account(line["Other Account"]),
            }
            get_model("batch.import.payment").create(vals)

    def import_sale_file(self, ids, context={}):
        obj = self.browse(ids)[0]
        path = get_file_path(obj.sale_file)
        data = open(path).read()
        rd = csv.reader(StringIO(data))
        headers = next(rd)
        headers = [h.strip() for h in headers]
        for row in rd:
            print("row", row)
            line = dict(zip(headers, row))
            print("line", line)
            vals = {
                "import_id": obj.id,
                "date": parse_date(line["Date"], obj.date_fmt),
                "number": line["Invoice No."],
                "contact": line["Customer Name"],
                "description": line["Description"],
                "amount": parse_float(line["Amount"]),
                "account_id": get_account(line["Income Account"]),
                "tax_id": get_tax_rate(line["Tax Rate"]),
            }
            get_model("batch.import.sale.invoice").create(vals)

    def import_purchase_file(self, ids, context={}):
        obj = self.browse(ids)[0]
        path = get_file_path(obj.purchase_file)
        data = open(path).read()
        rd = csv.reader(StringIO(data))
        headers = next(rd)
        headers = [h.strip() for h in headers]
        for row in rd:
            print("row", row)
            line = dict(zip(headers, row))
            print("line", line)
            vals = {
                "import_id": obj.id,
                "date": parse_date(line["Date"], obj.date_fmt),
                "number": line["Invoice No."],
                "contact": line["Supplier Name"],
                "description": line["Description"],
                "amount": parse_float(line["Amount"]),
                "account_id": get_account(line["Expense Account"]),
                "tax_id": get_tax_rate(line["Tax Rate"]),
            }
            get_model("batch.import.purchase.invoice").create(vals)

    def post(self, ids, context={}):
        obj = self.browse(ids)[0]
        for line in obj.sale_invoices:
            if line.invoice_id:
                continue
            vals = {
                "date": line.date,
                "due_date": line.date,  # XXX
                "number": line.number,
                "contact_id": merge_contact(line.contact),
                "type": "out",
                "inv_type": "invoice",
                "lines": [],
            }
            line_vals = {
                "description": line.description,
                "amount": line.amount,
                "account_id": line.account_id.id,
                "tax_id": line.tax_id.id,
            }
            vals["lines"].append(("create", line_vals))
            inv_id = get_model("account.invoice").create(
                vals, context={"type": vals["type"], "inv_type": vals["inv_type"]})
            get_model("account.invoice").post([inv_id])
            line.write({"invoice_id": inv_id})
        for line in obj.purchase_invoices:
            if line.invoice_id:
                continue
            vals = {
                "date": line.date,
                "due_date": line.date,  # XXX
                "number": line.number,
                "contact_id": merge_contact(line.contact),
                "type": "in",
                "inv_type": "invoice",
                "lines": [],
            }
            line_vals = {
                "description": line.description,
                "amount": line.amount,
                "account_id": line.account_id.id,
                "tax_id": line.tax_id.id,
            }
            vals["lines"].append(("create", line_vals))
            inv_id = get_model("account.invoice").create(
                vals, context={"type": vals["type"], "inv_type": vals["inv_type"]})
            get_model("account.invoice").post([inv_id])
            line.write({"invoice_id": inv_id})
        for line in obj.cash_payments:
            if line.payment_id:
                continue
            vals = {
                "date": line.date,
                "account_id": obj.cash_account_id.id,
                "lines": [],
            }
            if line.received:
                vals["type"] = "in"
            elif line.spent:
                vals["type"] = "out"
            else:
                raise Exception("Missing amount in cash payment")
            amt = line.received or line.spent
            if line.invoice_no:
                vals["pay_type"] = "invoice"
                line_vals = {
                    "type": "invoice",
                    "description": line.description,
                    "invoice_id": get_invoice(line.invoice_no),
                    "amount": amt,
                }
            else:
                vals["pay_type"] = "direct"
                line_vals = {
                    "type": "direct",
                    "description": line.description,
                    "amount": amt,
                    "account_id": line.other_account_id.id,
                }
            vals["lines"].append(("create", line_vals))
            pmt_id = get_model("account.payment").create(vals, context={"type": vals["type"]})
            get_model("account.payment").post([pmt_id])
            line.write({"payment_id": pmt_id})
        for line in obj.bank_payments:
            if line.payment_id:
                continue
            vals = {
                "date": line.date,
                "account_id": obj.bank_account_id.id,
                "lines": [],
            }
            if line.received:
                vals["type"] = "in"
            elif line.spent:
                vals["type"] = "out"
            else:
                raise Exception("Missing amount in bank payment")
            amt = line.received or line.spent
            if line.invoice_no:
                vals["pay_type"] = "invoice"
                line_vals = {
                    "type": "invoice",
                    "description": line.description,
                    "invoice_id": get_invoice(line.invoice_no),
                    "amount": amt,
                }
            else:
                vals["pay_type"] = "direct"
                line_vals = {
                    "type": "direct",
                    "description": line.description,
                    "amount": amt,
                    "account_id": line.other_account_id.id,
                }
            vals["lines"].append(("create", line_vals))
            pmt_id = get_model("account.payment").create(vals, context={"type": vals["type"]})
            get_model("account.payment").post([pmt_id])
            line.write({"payment_id": pmt_id})
        obj.write({"state": "posted"})

BatchImport.register()
