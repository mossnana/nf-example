from netforce.model import Model,fields,get_model
from netforce.utils import get_data_path
from datetime import datetime, timedelta
from netforce.access import get_active_company, get_active_user, set_active_user
import time
import random

class kaohome(Model):
    _name="kaoteang"
    _name_field="number"
    _fields= {
        "product_id": fields.Many2One("product", "Product", search=True),
        "contact_id": fields.Many2One("contact", "Customer",required=True, search=True),
        "date": fields.Date("Date", required=True),
        "amount": fields.Integer("Qty"),
        "devqty": fields.Integer("DeliveryQty"),
        "number": fields.Char("Number", search=True),
        "price": fields.Decimal("Price"),
        "total": fields.Decimal("Total", function="get_summary",function_multi=True),
        "description": fields.Char("Description"),
        "alltotal": fields.Decimal("Total Price", function="get_summary",function_multi=True),
        "mixamount": fields.Integer("All Amount", function="get_summary",function_multi=True),
        "eathere": fields.Boolean("Eat here"),
        "orderhome": fields.Boolean("Order food to go home"),
        "delivery": fields.Boolean("Delivery"),
        "send": fields.Char("เพิ่มค่าส่ง 50 บาท "),
        "line":fields.One2Many("kao.order.line","orderline","Menu Order"), #3nametable
        "state": fields.Selection([("draft","Draft"), ("confirmed","Confirmed"), ("approve","Approve"),("voided","Voided")], "Status" ,required=True, search=True),
        "cate": fields.Selection([("here","Here"), ("orderhome","Orderhome"), ("delivery","Delivery")], "Status" ,search=True),
        #"related_id": fields.Reference([["kao.delivery", "KaoDelivery"]], "Related To"),
        "deliveryorder": fields.One2Many("kao.delivery", "related_id", "Delivery Orders"),    
        "pickingout": fields.One2Many("stock.picking", "related_id", "pickingOut"),    
        "discount":fields.Char("Discount code"),
    }

    def _get_number(self, context={}):
        seq_id = get_model("sequence").find_sequence(type="kaoteang",context=context)
        if not seq_id:
            return None
        while 1:
            num = get_model("sequence").get_next_number(seq_id, context=context)
            if not num:
                return None
            user_id = get_active_user()
            set_active_user(1)
            res = self.search([["number", "=", num]])
            set_active_user(user_id)
            if not res:
                return num
            get_model("sequence").increment_number(seq_id, context=context)

    _defaults = {
        "state" : "draft",
        "amount" : "1",
        "date": lambda *a: time.strftime("%Y-%m-%d"), 
        "number" : _get_number,
    }

    def confirmed(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.eathere:
            obj.write({"cate":"here"})
            obj.write({"state":"confirmed"})
        elif obj.orderhome:
            obj.write({"cate":"orderhome"})
            obj.write({"state":"confirmed"})
        elif obj.delivery:
            obj.write({"cate":"delivery"})
            obj.write({"state":"confirmed"})
        else :
            raise Exception("Select Category")
        #if obj.eathere or obj.orderhome:
            #for aa in obj.line:
                #print(aa.amount,aa.devqty)
                #aa.write({"devqty":aa.amount})
            
            

    def to_edit(self, ids, context={}):
        obj = self.browse(ids)[0]
        obj.write({"state":"draft"})

    def copy_to_picking(self, ids, context={}):
        id = ids[0]
        obj = self.browse(id)
        pick_vals = {}
        contact = obj.contact_id
        res = get_model("stock.location").search([["type", "=", "customer"]])
        samount = 0
        sdevqty = 0 
        for aa in obj.line:
            samount += aa.amount
            sdevqty += aa.devqty
            print("amount :", samount)
            print("devqty :", sdevqty)
        if samount < sdevqty:
            raise Exception("ส่งเกินไปละ ส่งไรเยอะแยะ")
        elif samount > sdevqty:
            if not res:
                raise Exception("Customer location not found")
            cust_loc_id = res[0]
            wh_loc_id = 70 #จะแดกก็แดก

            pick_vals = {
                "contact_id":contact.id,
                "type" : "out",
                "related_id": "kaoteang,%s" % obj.id,
                "lines":[],
            }
            xamount = 0
            for line in obj.line:
                prod = line.product_id
                xamount = line.amount - line.devqty
                if xamount > 0:
                    line_vals = {
                        "product_id":prod.id,
                        "qty":xamount,
                        "uom_id": prod.uom_id.id,
                        "location_from_id": wh_loc_id,
                        "location_to_id": cust_loc_id,
                    }
                if xamount > 0: #สร้างไลน์เมื่อมีข้อมูล ถ้าไม่มีข้อมูลมาสร้างแล้วจะเออเร่อ
                    pick_vals["lines"].append(("create",line_vals))
            new_cpt = get_model("stock.picking").create(pick_vals, context={"pick_type": "out"}) #สั่งเขียนทีเดียว
        else:
            raise Exception("ส่งครบแล้วจ่ะ")
        return {
            "next": {
                "name": "pick_out", #actionnewpage
                "mode": "form",
                "active_id": new_cpt
            },
            "flash": "Copy to picking"
        }

    def onchange_amount(self, context={}):
        data = context["data"]
        path = context["path"]
        mix = get_data_path(data, path, parent=True)
        mix["total"] = (mix.get("amount") or 1) * (mix.get("price") or 1)
        x = 0
        y = 0
        for xy in data["line"]:
            x += xy.get("amount") or 0
            y += xy.get("total") or 0
        if data.get("delivery"):
            y = (y-(0.1*y)) + 50 if data.get('discount')=="sleepwithmefreebreakfast" else y+50
            print("Hello")
        data["mixamount"] = x
        data["alltotal"] = (y-(0.1*y)) if data.get("delivery")==None and data.get('discount')=="sleepwithmefreebreakfast" else y
        return data

    def onchange_delivery(self, context={}):
        data = context["data"]
        if data.get("delivery"):
            data["orderhome"] = False
            data["eathere"] = False
        
        x = 0
        y = 0

        for xy in data["line"]:
            x += xy.get("amount") or 0
            y += xy.get("total") or 0
        if data.get("delivery"):
            y = y + 50
        
        data["mixamount"] = x
        data["alltotal"] = y
        return data
        

    def onchange_orderhome(self, context={}):
        data = context["data"]
        if data.get("orderhome"):
            if data.get("delivery"):
                data["alltotal"] = data.get("alltotal") - 50
            data["delivery"] = False
            data["eathere"] = False
        return data

    def onchange_eathere(self, context={}):
        data = context["data"]
        if data.get("eathere"):
            if data.get("delivery"):
                data["alltotal"] = data.get("alltotal") - 50
            data["orderhome"] = False
            data["delivery"] = False

        return data

    def onchange_product(self, context={}):
        data = context["data"]
        path = context["path"]
        line = get_data_path(data, path, parent=True)
        prod = line.get("product_id")
        cont = data.get("contact_id")
        if not prod:
            return {}
        pd = get_model("product").browse(prod)
        ct = None
        if cont:
            ct = get_model("contact").browse(cont).name
        line["price"] = pd.price
        line["description"] = pd.description or ct

        line["total"] = (line.get("amount") or 1) * (line.get("price") or 1)
        x = 0
        y = 0
        for xy in data["line"]:
            x += xy.get("amount") or 0
            y += xy.get("total") or 0
        if data.get("delivery"):
            y = y-(data.get("discount")*0.1) + 50 if data.get('discount')=="sleepwithmefreebreakfast" else y + 50

        data["mixamount"] = x
        data["alltotal"] = y
        return data

    def get_summary(self,ids,context={}): 
        res = {}
        for obj in self.browse(ids):
            alltotal = 0
            mixamount = 0
            #total = 0
            for att in obj.line:
                    print("innnnnnnnnnnn") 
                    print(att.total)
                    att.total = float(att.price or 0) * float(att.amount or 0)
                    mixamount += float(att.amount or 0)
                    alltotal += att.total
            if obj.delivery:
                alltotal = (alltotal-(0.1*alltotal)) + 50 if obj.discount=="sleepwithmefreebreakfast" else alltotal+50
            print("====> ",obj.contact_id.id)
            res[obj.id] = {
                "total": att.total,
                "alltotal": alltotal,
                "mixamount": mixamount,
                    }
        return res

    def deliveryre(self, ids, context={}):
        obj = self.browse(ids[0])
        action = "kao_delivery_re"
        layout = "kao_deliveryorder_form"
        return {
            "next": {
                "name": action,
                "mode": "form",
                "form_view_xml": layout,
                "active_id": obj.id,
                }
            }

    def eatrandom(self, ids, context={}):
        # self callled
        obj = self.browse(ids[0])
        product_ids = get_model("product").search([["foodtype", "=", True]])
        import pdb; pdb.set_trace()
        random_food = random.choice(product_ids)
        vals = {
        "orderline": obj.id,
        "product_id": random_food,
        "price": random_food.get_model("product").browse().price,
        }
        get_model("kao.order.line").create(vals)
        return {
        "next": {
            "type": "reload",
            },
        "flash": "Random Successful",
        }

    def onchange_discount(self, context={}):
        obj=context['data']
        if obj['discount'] == "sleepwithmefreebreakfast":
            obj['alltotal'] = obj.get('alltotal') - (0.1*obj.get('alltotal'))
        else:
            return
        return obj

kaohome.register()
