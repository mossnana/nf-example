from netforce.model import Model,fields,get_model
from netforce.access import get_active_company
from netforce.utils import get_data_path
from datetime import *

class PettyCash(Model):
    _name = "petty.cash"
    _multi_company = True
    _key = ["number","company_id"]
    _name_field = "number"
    _string = "Petty Cash"
    _fields = {
        "company_id":fields.Many2One("company","Company",readonly=True,required=True),
        "number": fields.Char("Number", search=True),
        "date":fields.Date("Date",search=True),
        "state":fields.Selection([["draft","Draft"],["posted","Posted"],["voided","Voided"]],"Status",search=True),
        "fund_id":fields.Many2One("petty.cash.fund","Petty Cash Fund", condition=[["state", "=", "approved"]], search=True),
        "type":fields.Selection([["in","Receive"],["out","Payment"]],"Type"),
        "receive_type":fields.Selection([["in","IN"],["out","OUT"]],"Type"),
        "amount":fields.Decimal("Amount"),
        "amount_bal":fields.Decimal("Current Balance",readonly=True), ##pull Current Balance from petty cash fund
        "note":fields.Text("Memo", search=True),
        "analytic_account_id":fields.Many2One("account.account","Analytic Account"),
        "account_id":fields.Many2One("account.account","Petty Cash Account",search=True, readonly=True),
        "cash_account_id":fields.Many2One("account.account","From Account"),
        "journal_id": fields.Many2One("account.journal", "Journal",readonly=True),
        "move_id": fields.Many2One("account.move", "Journal Entry"),
        "sequence_id": fields.Many2One("sequence", "Number Sequence"),
        "track_id": fields.Many2One("account.track.categ", "Track-1", condition=[["type", "=", "1"]], readonly=True),
        "track2_id": fields.Many2One("account.track.categ", "Track-2", condition=[["type", "=", "2"]], readonly=True),
        "number_receive":fields.Many2One("petty.cash","Petty Cash Receive",readonly=True, search=True), ##check petty cash receive remain
        "number_payment":fields.Many2One("petty.cash","Petty Cash peyment waiting",readonly=True), ##check petty cash payment waiting
        "sequence_id": fields.Many2One("sequence", "Number Sequence"),
        "employee_id":fields.Many2One("hr.employee","Employee"),
        #"tax_type": fields.Selection([["tax_ex", "Tax Exclusive"], ["tax_in", "Tax Inclusive"], ["no_tax", "No Tax"]],"Tax Type"),
        "lines":fields.One2Many("petty.cash.line","petty_cash_id","Payment"),
        "taxes":fields.One2Many("petty.cash.tax","petty_cash_id","Vat Line",condition=[["tax_type", "=", "vat"]]),
        "wht_taxes":fields.One2Many("petty.cash.tax","petty_cash_id","WHT Line",condition=[["tax_type", "=", "wht"]]),
        "amount_subtotal":fields.Decimal("Subtotal",function="get_amounts",function_multi=True),
        "amount_tax":fields.Decimal("Tax Amount",function="get_amounts",function_multi=True),
        "amount_wht":fields.Decimal("Withholding Tax Amount",function="get_amounts",function_multi=True),
        "amount_total":fields.Decimal("Total Amount",function="get_amounts",function_multi=True),
        "product_id": fields.Many2One("product", "Product", search=True),
        "currency_id": fields.Many2One("currency", "Currency"),
        "cash_account_currency_id": fields.Many2One("currency", "Currency"),
        "number_receive_total": fields.Json("Number of Payment Receive", function="get_number_receive"),
        }
    
    def _get_number(self, context={}):
        type = context.get("type")
        seq_id = context.get("sequence_id")
        if not seq_id:
            if type == "in":
                seq_type = "petty_cash_receive"
            elif type == "out":
                seq_type = "petty_cash_payment"
            else:
                return
            #seq_type = "petty_cash_receive"
            seq_id = get_model("sequence").find_sequence(name=seq_type,context=context)
            if not seq_id:
                return None
        while 1:
            num = get_model("sequence").get_next_number(seq_id, context=context)
            res = self.search([["number", "=", num]])
            if not res:
                return num
            get_model("sequence").increment_number(seq_id, context=context)

    def _get_type(self, context={}):
        return context.get("type")

    def _get_journal_id(self,context={}):
        settings = get_model("settings").browse(1)
        return settings.petty_cash_journal_id.id

    def _get_num_receive(self,context={}):
        receive_ptc = get_model("petty.cash.fund").search([['number_receive', '!=', None]])
        return receive_ptc

    _defaults = {
        "number":_get_number,
        "company_id":lambda *a: get_active_company(),
        "date":lambda *a: datetime.strftime(datetime.today(),"%Y-%m-%d"),
        "state":"draft",
        "type":_get_type,
        "tax_type":"tax_in",
        "journal_id":_get_journal_id,
        "note": "",
        "number_receive_total": _get_num_receive,
        }

    def get_number_receive(self, ids, context={}):
        print("Hello ===========================>")
        res = {}
        for obj in self.browse(ids):
            receive_ptc = get_model("petty.cash.fund").search([['number_receive', '!=', None]])
            res[obj.id] = receive_ptc
        return res

    def write(self, ids, vals, **kw):
        super().write(ids, vals, **kw)
        self.function_store(ids)
        return ids

    def create(self, vals, **kw): 
        context=kw.get('context')
        print("create function")
        new_id = super().create(vals, **kw)
        return new_id

    def onchange_fund(self,context={}):
        data = context["data"]
        fund_id = get_model("petty.cash.fund").browse(data["fund_id"])
        if fund_id.number_receive.number_payment:
            if fund_id.number_receive.number_payment.state=="draft":
                amount = fund_id.number_receive.number_payment.amount_total
                amount_bal = fund_id.acc_bal - fund_id.number_receive.number_payment.amount_total
            else:
                amount = fund_id.max_amt - fund_id.acc_bal
                amount_bal = fund_id.acc_bal 
        else :
            amount = fund_id.max_amt - fund_id.acc_bal
            amount_bal = fund_id.acc_bal 
        data["account_id"] = fund_id.account_id.id
        data["track_id"] = fund_id.track_id.id
        data["track2_id"] = fund_id.track2_id.id
        data["currency_id"] = fund_id.currency_id.id
        data["amount"] = amount 
        data["amount_bal"] = amount_bal
        return data

    def onchange_fund_pay(self,context={}):
        data = context["data"]
        fund_id = get_model("petty.cash.fund").browse(int(data.get("fund_id")))
        data["number_receive"] = fund_id.number_receive.id
        data["amount_bal"] = fund_id.acc_bal
        if data.get("type") == "out":
            for line in data["lines"]:
                line['track_id'] = fund_id.track_id.id if fund_id.track_id else None
                line['track2_id'] = fund_id.track2_id.id if fund_id.track2_id else None
        print("data from onchange product")
        print(data)
        return data

    def update_line(self,context={}):
        data=context["data"]
        path=context['path']
        line = get_data_path(data,path,parent=True)
        try:
            fund_id = get_model("petty.cash.fund").browse(data.get("fund_id"))
        except:
            raise Exception("Not found Petty Cash Fund")
        amount_bal = fund_id.acc_bal or 0
        if not line.get("qty",None):
            line["qty"] = 1
            data["amount_bal"] = amount_bal
        line["amount"] = (line.get("unit_price") or 0) * (line.get("qty") or 0)
        data = self.update_amounts(data)
        data["amount_bal"] = amount_bal - (data["amount_total"] or 0) if amount_bal else 0
        return data
        

    def post(self,ids,context={}):
        obj = self.browse(ids)[0]
        obj.calc_taxes()
        fund = get_model("petty.cash.fund")
        fund_id = obj.fund_id
        if fund_id:
            if obj.type=="out" and fund_id.acc_bal < fund_id.min_amt:
                raise Exception ("Information Current Balance less than Minimum Amount in Petty Cash Fund your select!! Please make Petty Cash Receive")
        if obj.type == "in":
            if obj.amount > (obj.fund_id.max_amt - obj.fund_id.acc_bal) or obj.amount <= 0:
                raise Exception("Invalid amount")
            cond = [["id","=",obj.fund_id.id],]
            for s in fund.search_browse(cond):
                s.write({"number_receive" : obj.id,})
            move_vals = {
                "journal_id": obj.journal_id.id,
                "number": obj.number,
                "date": obj.date,
                "narration": "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash received ; {}".format(obj.fund_id.name),
                "related_id": "petty.cash,%s" % obj.id,
                "company_id": obj.company_id.id,
                'lines': [],
            }

            ## petty cash account
            line_vals={
                'description': "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash received ; {}".format(obj.fund_id.name),
                'account_id': obj.account_id.id,
                'track_id':obj.track_id.id,
                'track2_id':obj.track2_id.id,
                'debit': obj.amount,
                'credit': 0,
                'due_date': obj.date,
            }
            move_vals['lines'].append(('create',line_vals))

            ## cash account
            line_vals={
                'description': "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash received ; {}".format(obj.fund_id.name),
               # 'description': "{} ; {}".format(obj.note, obj.fund_id.name),
              'account_id': obj.cash_account_id.id,
              'debit': 0,
              'credit': obj.amount,
              'due_date': obj.date,
            }
            move_vals['lines'].append(('create',line_vals))

        else:
            if obj.amount_total > obj.fund_id.max_amt:
                raise Exception("Total amount is over limit.")
            if obj.amount_total > obj.fund_id.acc_bal:
                raise Exception("Account Balance is not enough.")
            if obj.amount_bal <0:
                raise Exception("Petty Cash Payment Over Petty Cash Receive")
            if fund_id.number_receive : 
                fund_id.number_receive.write({"amount_bal" : obj.amount_bal,})
            if obj.number_receive:
                obj.number_receive.write({"number_payment" : obj.id})
            move_vals = {
                "journal_id": obj.journal_id.id,
                "number": obj.number,
                "date": obj.date,
                "narration": "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash payment ; {}".format(obj.fund_id.name),
                "related_id": "petty.cash,%s" % obj.id,
                "company_id": obj.company_id.id,
                'lines': [],
            }

            # lines
            for line in obj.lines:
                line_vals={
                    'description': "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash payment ; {}".format(obj.fund_id.name),
                    'account_id': line.account_id.id,
                    'debit': line.base_amt,
                    'track_id':line.track_id.id,
                    'track2_id':line.track2_id.id,
                    'credit': 0,
                    'due_date': obj.date,
                }
                move_vals['lines'].append(('create',line_vals))

            # vat
            for tax in obj.taxes:
                line_vals={
                'description': "{} ; {} ; {}".format(obj.note, obj.fund_id.name, tax.tax_comp_id.name) if obj.note or obj.note != "" else "Petty Cash payment ; {} ; {}".format(obj.fund_id.name, tax.tax_comp_id.name),
                    'account_id': tax.tax_comp_id.account_id.id,
                    'debit': tax.tax_amount,
                    'contact_id': tax.contact_id.id,
                    'tax_comp_id':tax.tax_comp_id.id,
                    'tax_base':tax.base_amount,
                    'tax_no': tax.tax_no,
                    'track_id':line.track_id.id,
                    'track2_id':line.track2_id.id,
                    'credit': 0,
                    'due_date': obj.date,
                }
                move_vals['lines'].append(('create',line_vals))

            # wht
            for wht in obj.wht_taxes:
                line_vals={
                    'description': "{} ; {} ; {}".format(obj.note, obj.fund_id.name, wht.tax_comp_id.name) if obj.note or obj.note != "" else "Petty Cash payment ; {} ; {}".format(obj.fund_id.name, wht.tax_comp_id.name),
                    #'description': "{} ; {} ; {} ".format(obj.note, obj.fund_id.name, wht.tax_comp_id.name),
                    'account_id': wht.tax_comp_id.account_id.id,
                    'debit': 0,
                    'contact_id': wht.contact_id.id,
                    'tax_comp_id':wht.tax_comp_id.id,
                    'tax_base':wht.base_amount,
                    'tax_no': wht.tax_no,
                    'track_id':line.track_id.id,
                    'track2_id':line.track2_id.id,
                    'credit': wht.tax_amount,
                    'due_date': obj.date,
                }
                move_vals['lines'].append(('create',line_vals))

            # fund
            line_vals={
                'description': "{} ; {}".format(obj.note, obj.fund_id.name) if obj.note or obj.note != "" else "Petty Cash payment ; {}".format(obj.fund_id.name),
                'account_id': obj.fund_id.account_id.id,
                'debit': 0,
                'track_id':obj.fund_id.track_id.id,
                'track2_id':obj.fund_id.track2_id.id,
                'credit': obj.amount_total,
                'due_date': obj.date,
            }
            move_vals['lines'].append(('create',line_vals))

        move_id=get_model('account.move').create(move_vals)
        move=get_model('account.move').browse(move_id)
        move.post()
        obj.write({
            'move_id': move_id,
            'state': 'posted',
        })

    def view_journal_entry(self,ids,context={}):
        obj=self.browse(ids)[0]
        return {
            'next': {
                'name': 'journal_entry',
                'active_id': obj.move_id.id,
                'mode': 'form',
            },
        }

    def onchange_sequence(self, context={}):
        data = context["data"]
        num = self._get_number(context={"type": data["type"], "date": data["date"], "sequence_id": data["sequence_id"]})
        data["number"] = num
        return data

    def get_amounts(self,ids, context={}):
        res = {}
        obj = self.browse(ids)[0]
        settings = get_model("settings").browse(1)
        subtotal = tax_amount = wht_amount = total = 0
        for line in obj.lines:
            tax_id = line.tax_id
            tax = 0
            wht = 0
            if tax_id and line.tax_type != "no_tax":
                base_amts = get_model("account.tax.rate").compute_base_wht(tax_id, line.amount, tax_type=line.tax_type)
                for amt,comp_type in base_amts:
                    if comp_type == "vat":
                        base_amt = amt
                        tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, amt,when="petty_cash")
                        for comp_id, tax_amt in tax_comps.items():
                            tax += tax_amt
                    elif comp_type == "wht":
                        tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, amt,when="petty_cash",wht=True)
                        for comp_id, tax_amt in tax_comps.items():
                            wht += tax_amt
            else:
                base_amt = line.amount
            subtotal += base_amt
            tax_amount += tax
            wht_amount += wht
            total += base_amt + tax
        vals = {
            "amount_subtotal":get_model("currency").round(settings.currency_id.id,subtotal),
            "amount_tax":get_model("currency").round(settings.currency_id.id,tax_amount),
            "amount_wht": abs(wht_amount),
            "amount_total":total + wht_amount,
            }
        res[obj.id] = vals
        return res

    def update_amounts(self,data,context={}):
        res = {}
        settings = get_model("settings").browse(1)
        subtotal = tax_amount = wht_amount = total = 0
        for line in data["lines"]:
            if line.get("tax_id"):
                tax_id = get_model("account.tax.rate").browse(line.get("tax_id"))
                tax = 0
                wht = 0
                if tax_id and line.get("tax_type") not in ["no_tax",None]:
                    base_amts = get_model("account.tax.rate").compute_base_wht(tax_id, line.get("amount"), tax_type=line.get("tax_type"))
                    for amt,comp_type in base_amts:
                        if comp_type == "vat":
                            base_amt = amt
                            tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, amt,when="petty_cash")
                            for comp_id, tax_amt in tax_comps.items():
                                tax += tax_amt
                        elif comp_type == "wht":
                            tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, amt,when="petty_cash",wht=True)
                            for comp_id, tax_amt in tax_comps.items():
                                wht += tax_amt
                            base_amt = line["amount"] if base_amt == 0 else base_amt
                else:
                    base_amt = line["amount"]

                line["base_amt"] = base_amt
                subtotal += base_amt
                tax_amount += tax
                wht_amount += wht
                total += base_amt + tax
            else:
                line["base_amt"] = line.get("amount")
                subtotal += line.get("amount") or 0
                total += line.get("amount") or 0
        data["amount_subtotal"] = get_model("currency").round(settings.currency_id.id,subtotal),
        data["amount_tax"] = get_model("currency").round(settings.currency_id.id,tax_amount),
        data["amount_wht"] =  abs(wht_amount),
        data["amount_total"] = total + wht_amount
        return data

    def to_draft(self,ids,context={}):
        obj=self.browse(ids)[0]
        if obj.move_id:
            obj.move_id.to_draft()
            obj.move_id.delete()
        obj.write({'state': 'draft',},context=context)
        obj.taxes.delete()
        obj.wht_taxes.delete()
        
        if obj.type == "in":
            obj.fund_id.write({"number_receive" : None})
        
        return

    def void(self,ids,context={}):
        obj=self.browse(ids)[0]
        obj.move_id.void()
        obj.write({'state': 'voided',},context=context)
        for tax in obj.taxes:
            tax.write({
                'base_amount': 0,
                'tax_amount': 0,
            })
        for tax in obj.wht_taxes:
            tax.write({
                'base_amount': 0,
                'tax_amount': 0,
            })
        if obj.type == "in":
            obj.fund_id.write({"number_receive" : None})

    def copy(self, ids, context={}):
        obj = self.browse(ids)[0]
        vals = {
            "date": obj.date,
            "type": obj.type,
            "fund_id": obj.fund_id.id,
            "number_receive": obj.number_receive.id,
            "amount_bal": obj.amount_bal,
            "company_id": obj.company_id.id,
            "journal_id": obj.journal_id.id,
            "amount_subtotal": obj.amount_subtotal,
            "amount_tax": obj.amount_tax,
            "amount_wht": obj.amount_wht,
            "amount_total": obj.amount_total,
            "track_id": obj.track_id.id,
            "track2_id": obj.track2_id.id,
            "amount": obj.amount,
            "cash_account_id" : obj.cash_account_id.id,
            "account_id" : obj.account_id.id,
        }
        lines = []
        for line in obj.lines:
            line_vals = {
                "product_id": line.product_id.id,
                "description": line.description,
                "account_id": line.account_id.id,
                "unit_price": line.unit_price,
                "qty": line.qty,
                "amount": line.amount,
                "tax_id": line.tax_id.id,
                "tax_type": line.tax_type,
                "tax_date": line.tax_date,
                "tax_invoice": line.tax_invoice,
                "contact_id": line.contact_id.id,
                "track_id": line.track_id.id,
                "track2_id": line.track2_id.id,
            }
            lines.append(line_vals)
        vals["lines"] = [("create", v) for v in lines]
        pmt_id = self.create(vals, context={"type": vals["type"]})
        return {
            "next": {
                "name": "view_petty_cash",
                "active_id": pmt_id,
            },
            "flash": "New payment %d copied from %d" % (pmt_id, obj.id),
        }

    def calc_taxes(self,ids,context={}):
        obj=self.browse(ids[0])
        obj.taxes.delete()
        obj.wht_taxes.delete()
        settings = get_model("settings").browse(1)
        taxes = {}
        tax_nos = []
        total_amt = total_base = total_tax = 0
        for line in obj.lines:
            tax_id = line.tax_id
            if tax_id and line.tax_type not in ["no_tax",None]:
                base_amts = get_model("account.tax.rate").compute_base_wht(tax_id, line.amount, tax_type=line.tax_type)
                for amt,comp_type in base_amts:
                    if settings.rounding_account_id:
                        base_amt=get_model("currency").round(settings.currency_id.id,amt)
                    if comp_type == "vat":
                        base_amt = amt
                        tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, base_amt,when="petty_cash")
                        for comp_id, tax_amt in tax_comps.items():
                            key = (comp_id,line.contact_id.id,line.tax_invoice)
                            tax_vals = taxes.setdefault(key, {"tax_amt": 0, "base_amt": 0})
                            tax_vals["tax_amt"] += tax_amt
                            tax_vals["base_amt"] += base_amt
                    elif comp_type == "wht":
                        tax_comps = get_model("account.tax.rate").compute_taxes_wht(tax_id, base_amt,when="petty_cash",wht=True)
                        for comp_id, tax_amt in tax_comps.items():
                            key = (comp_id,line.contact_id.id,line.tax_invoice)
                            tax_vals = taxes.setdefault(key, {"tax_amt": 0, "base_amt": 0})
                            tax_vals["tax_amt"] += tax_amt
                            tax_vals["base_amt"] += base_amt
            else:
                base_amt = line.amount
        for (comp_id,contact_id,tax_invoice),tax_vals in taxes.items():
            comp = get_model("account.tax.component").browse(comp_id)
            acc_id = comp.account_id.id
            if not acc_id:
                raise Exception("Missing account for tax component %s" % comp.name)
            ctx = {"date":obj.date}
            vals = {
                "petty_cash_id": obj.id,
                "tax_comp_id": comp_id,
                "base_amount": get_model("currency").round(settings.currency_id.id,tax_vals["base_amt"]),
                "tax_amount": get_model("currency").round(settings.currency_id.id,abs(tax_vals["tax_amt"])),
                'tax_date': obj.date,
                'tax_type':comp.type,
                'tax_no':get_model("petty.cash.line").gen_tax_no(context=ctx) if comp.type =="wht" else tax_invoice,
                'contact_id':contact_id,
            }
            get_model("petty.cash.tax").create(vals)

    def view_petty_cash(self, ids, context={}):
        obj = self.browse(ids[0])
        if obj.type == "out":
            action = "petty_cash_payment"
            layout = "petty_cash_payment_form"
        elif obj.type == "in":
            action = "petty_cash_receive"
            layout = "petty_cash_receive_form"
        return {
            "next": {
                "name": action,
                "mode": "form",
                "form_view_xml": layout,
                "active_id": obj.id,
            }
        }

    def onchange_date(self, context={}):
        data = context["data"]
        ctx = {
            "type": data["type"],
            "date": data["date"],
        }
        number = self._get_number(context=ctx)
        data["number"] = number
        return data

    def delete(self, ids, **kw):
        for obj in self.browse(ids):
            if obj.state == "voided" or obj.state == "posted":
                raise Exception ("These items can not be Deleted")
        super().delete(ids, **kw)

    def onchange_product(self, context={}):
        data=context['data']
        path=context['path']
        line = get_data_path(data, path, parent=True)
        product_model=get_model("product").browse(line.get("product_id"))
        line["description"] = product_model.description
        if product_model.get("purchase_account_id"):
            line["account_id"] = product_model.purchase_account_id.id
        else:
            line["account_id"] = product_model.categ_id.purchase_account_id.id if product_model.categ_id.purchase_account_id else None

        if product_model.purchase_tax_id is not None and product_model.purchase_tax_id.id:
            line["tax_id"] = product_model.purchase_tax_id.id
        else:
            if product_model.categ_id.purchase_tax_id is not None and product_model.categ_id.purchase_tax_id.id:
                line["tax_id"] = product_model.categ_id.purchase_tax_id.id
            else:
                line["tax_id"] = None
        if line['tax_id']:
            line['tax_type'] = "tax_ex"
        else:
            line['tax_type'] = None
        if data.get("fund_id"):
            fund_id = get_model("petty.cash.fund").browse(int(data.get("fund_id")))
            if fund_id:
                data["number_receive"] = fund_id.number_receive.id if fund_id.number_receive else None
                data["amount_bal"] = fund_id.acc_bal
                if data.get("type") == "out":
                    line['track_id'] = fund_id.track_id.id if fund_id.track_id else None
                    line['track2_id'] = fund_id.track2_id.id if fund_id.track2_id else None
        return data

    def onchange_cash_account_id(self, context={}):
        obj=context['data']
        cash_account=get_model("account.account").browse(obj['cash_account_id'])
        if not cash_account:
            return
        else:
            obj['cash_account_currency_id']= cash_account.currency_id.id
        return obj

PettyCash.register()

