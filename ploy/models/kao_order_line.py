from netforce.model import Model,fields,get_model
from netforce.utils import get_data_path
from datetime import datetime, timedelta
from netforce.access import get_active_company, get_active_user, set_active_user



class kaoorderline(Model):
    _name="kao.order.line"
    _fields= {
        "product_id": fields.Many2One("product", "Product", search=True),
        "description": fields.Char("Description"),
        "amount": fields.Integer("Amount"),
        "devqty": fields.Integer("DeliveryQty", function="get_devqty"),
        #"devqty": fields.Integer("DeliveryQty"),
        "price": fields.Decimal("Price"),
        "total": fields.Decimal("Total"),
        "orderline": fields.Many2One("kaoteang","dd"),
    }

    def get_devqty(self,ids,context={}):
        res = {}
        for obj in self.browse(ids):
            print(" ==================================")
            print(" product : ",obj.product_id.name)
            print(" amount  : ",obj.amount)
            qtytotal = 0

            if obj.orderline.eathere or obj.orderline.orderhome:
                qtytotal = obj.amount
            else:
                #order = obj.orderline
                #for aa in order.pickingout:
                for aa in obj.orderline.pickingout:
                    print(" order number : ",aa.number)
                    if aa.state == "done":
                        for bb in aa.lines:
                            print("=product1" ,obj.product_id.id)
                            print("=product2" ,bb.product_id.id)
                            if obj.product_id.id == bb.product_id.id:
                                qtytotal += bb.qty
            print("qtytotal :", qtytotal)
            res[obj.id] = qtytotal
        return res
        
                    
kaoorderline.register()
