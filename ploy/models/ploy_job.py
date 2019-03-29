from netforce.model import Model, fields, get_model
from netforce.access import get_active_user, set_active_user
from datetime import *
from dateutil.relativedelta import relativedelta
import time
from netforce.database import get_connection
from netforce.access import get_active_company, check_permission_other
from netforce.utils import get_data_path


class PloyJob(Model):
    _inherit = "job"
   # _string = "Service Order"
    _fields = {
        "description":fields.Char("Description")
    }

    def onchange_product(self, context={}):
        print("###########################1234")
        data = context["data"]
        path = context["path"]
        line = get_data_path(data, path, parent=True)
        prod_id = line["product_id"]
        prod = get_model("product").browse(prod_id)
        line["uom_id"] = prod.uom_id.id
        line["unit_price"] = prod.sale_price
        print(data.get("description"))
        line["description"] = data.get("description") or prod.description or prod.name 
        #if "description" == '':
            #line["description"] = prod.description 
            #print("in1")
        #else: 
            #line["description"] = data["description"]
            #print("in2")
        return data
    
    
    
    
    
PloyJob.register()
