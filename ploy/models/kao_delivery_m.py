from netforce.model import Model, fields, get_model
from netforce.utils import get_data_path
from netforce.access import get_active_company, get_active_user, set_active_user


class Kaodelivery(Model):
    _name = "kao.delivery"
    _transient = True
    _fields = {
        #"kao_id": fields.Many2One("kaoteang", "Kaoteang", required=True, on_delete="cascade"),
        "numberdv": fields.Char("Numberdelivery", search=True),
        "address": fields.Char("address"),
        "phone": fields.Char("phone"),
        "contact_id": fields.Many2One("contact", "Customer",required=True, search=True),
        "date": fields.Date("Date"),
        "line": fields.One2Many("kao.delivery.line", "pop_id", "Lines"),
        "state": fields.Selection([("draft","Draft"), ("confirm","Confirmed"), ("complete","Complete")], "Status" ,required=True, search=True),
        #"deliveryorder": fields.One2Many("kaoteang", "related_id", "Delivery Orders"),
        "related_id": fields.Reference([["kaoteang","KaoDelivery"]], "Related To"),
    }

    def _get_number(self, context={}):
        seq_id = get_model("sequence").find_sequence(type="kaodelivery",context=context)
        if not seq_id:
            return None
        while 1: 
            num = get_model("sequence").get_next_number(seq_id, context=context)
            if not num:
                return None
            user_id = get_active_user()
            set_active_user(1)
            res = self.search([["numberdv", "=", num]])
            set_active_user(user_id)
            if not res:
                return num
            get_model("sequence").increment_number(seq_id, context=context)

    _defaults = {
         "numberdv" : _get_number,
         "state" : "draft",
    }

    def confirmed(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state != "confirmed":
            raise Exception("No Completed")
        obj.write({"state":"confirm"})



Kaodelivery.register()
