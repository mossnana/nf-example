from netforce.model import Model, fields, get_model
from netforce.utils import get_data_path, roundup
import time
from netforce.access import get_active_user, set_active_user
from netforce.access import get_active_company, check_permission_other, set_active_company
from datetime import datetime, timedelta
from decimal import Decimal

class PloySaleOrder(Model):
    _inherit = "sale.order"
    _fields = {
        "description":fields.Text("Description"),
        "topic":fields.Char("Topic"),
    }
    
    
PloySaleOrder.register()
