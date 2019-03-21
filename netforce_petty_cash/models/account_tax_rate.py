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

from netforce.model import Model, fields, get_model, BrowseRecord
import uuid
from decimal import *

class TaxRate(Model):
    _inherit = "account.tax.rate"

    def compute_base_wht(self, tax_id, amt=0, tax_type="tax_ex"):
        if isinstance(tax_id, BrowseRecord):  # XXX: for speed (use browse cache)
            obj = tax_id
        else:
            obj = self.browse(tax_id)
        tax = []
        amt=Decimal(amt)
        base_amt = amt # default
        rate = 0
        for comp in obj.components:
            if tax_type == "tax_in":
                base_amt = amt / (1 + comp.rate / 100)
            elif tax_type == "tax_ex":
                base_amt = amt
            tax.append((base_amt,comp.type))
        return tax

    def compute_taxes_wht(self, tax_id, base, when="invoice",wht=False):
        if isinstance(tax_id, BrowseRecord):  # XXX: for speed (use browse cache)
            obj = tax_id
        else:
            obj = self.browse(tax_id)
        has_defer = False
        for comp in obj.components:
            if comp.type == "vat_defer":
                has_defer = True
        comps = {}
        for comp in obj.components:
            if when == "petty_cash":
                pass
                #if comp.type in ("vat", "vat_exempt") and has_defer:
                    #continue
            else:
                raise Exception("Can't compute taxes: invalid 'when'")
            if when == "invoice" and comp.type not in ("vat", "vat_exempt", "vat_defer"):
                continue
            if when == "payment" and comp.type != "wht":
                continue
            tax = base * (comp.rate / 100)
            if comp.type == "wht":
                tax = -tax
            elif comp.type == "vat_defer" and when in ("invoice_payment", "invoice_payment_inv"):
                tax = -tax
            if wht and comp.type == "wht":
                comps[comp.id] = tax
            elif not wht and comp.type == "vat":
                comps[comp.id] = tax
        return comps

TaxRate.register()
