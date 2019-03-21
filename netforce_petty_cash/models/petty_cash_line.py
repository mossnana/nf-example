from netforce.model import Model,fields,get_model
from netforce.access import get_active_user, set_active_user

class PettyCashLine(Model):
    _name="petty.cash.line"
    _fields={
        "petty_cash_id":fields.Many2One("petty.cash","Petty Cash",on_delete="cascade",required=True),
        "product_id":fields.Many2One("product","Product"),
        "description":fields.Char("Description"),
        "account_id":fields.Many2One("account.account","Account",required=True),
        "unit_price":fields.Decimal("Unit Price"),
        "tax_id": fields.Many2One("account.tax.rate", "Tax Rate", on_delete="restrict"),
        "tax_type": fields.Selection([["tax_ex", "Tax Exclusive"], ["tax_in", "Tax Inclusive"]],"Tax Type"),
        "tax_date": fields.Date("Tax Date"),
        "tax_invoice":fields.Char("Tax Invoice Number"),
        "contact_id":fields.Many2One("contact","Supplier"),
        "track_id": fields.Many2One("account.track.categ", "Track-1", condition=[["type", "=", "1"]]),
        "track2_id": fields.Many2One("account.track.categ", "Track-2", condition=[["type", "=", "2"]]),
        "qty":fields.Decimal("Qty"),
        "max_amt":fields.Decimal("Max Amount"),
        "amount":fields.Decimal("Subtotal",readonly=True),
        "base_amt":fields.Decimal("Base Amount"),
        }

    def _get_track_id(self,context={}):
        try:
            if "data" in context:
                data = context["data"]
                fund_id = get_model("petty.cash.fund").browse(data.get("fund_id"))
                return fund_id.track_id.id
            else:
                return
        except:
            raise Exception("Error to get data from Track 1")

    def _get_track2_id(self,context={}):
        try:
            if "data" in context:
                data = context.get("data")
                fund_id = get_model("petty.cash.fund").browse(data.get("fund_id"))
                return fund_id.track2_id.id
            else:
                return
        except:
            raise Exception("Error to get data from Track 2")

    def gen_tax_no(self,context={}):
        seq_id = get_model("sequence").find_sequence(type="wht_no",context=context)
        if not seq_id:
            return None
        while 1:
            num = get_model("sequence").get_next_number(seq_id, context=context)
            if not num:
                return None
            user_id = get_active_user()
            set_active_user(1)
            res = self.search([["tax_invoice", "=", num]])
            set_active_user(user_id)
            if not res:
                return num
            get_model("sequence").increment_number(seq_id, context=context)

    _defaults = {
        #"track_id":_get_track_id,
        #"track2_id":_get_track2_id,
    }

PettyCashLine.register()
