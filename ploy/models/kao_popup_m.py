from netforce.model import Model, fields, get_model
from netforce.utils import get_data_path

class kaopopup(Model):
    _name = "kao.popup"
    _transient = True
    _fields = {
        "kao_id": fields.Many2One("kaoteang", "Kaoteang", required=True, on_delete="cascade"),
        "number": fields.Char("number"),
        "delivery": fields.Boolean("Delivery"),
        "contact_id": fields.Many2One("contact", "Customer",required=True, search=True),
        
        "date": fields.Date("Date"),
        "line": fields.One2Many("kao.popup.line", "pop_id", "Lines"),
    }

    def _get_picking(self, context={}):  
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        return int(pick_id)
    def _get_date(self, context={}):  
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        pick = get_model("kaoteang").browse(pick_id)
        return pick.date
    def _get_delivery(self, context={}):  
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        pick = get_model("kaoteang").browse(pick_id)
        return pick.delivery
        
    def _get_contact(self, context={}):
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        pick = get_model("kaoteang").browse(pick_id)
        return pick.contact_id.id 
    def _get_number(self, context={}):
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        pick = get_model("kaoteang").browse(pick_id)
        return pick.number
        
    def _get_lines(self, context={}): 
        pick_id = context.get("refer_id")
        if not pick_id:
            return None
        pick_id = int(pick_id)
        pick = get_model("kaoteang").browse(pick_id)
        lines = []
        for line in pick.line:
            lines.append({
                "product_id": line.product_id.id,
                "amount": line.amount,
                "price": line.price,
                "total": line.total,
            })
        print(" ----> ",lines)
        return lines

    _defaults = {
        "kao_id": _get_picking,
        "date": _get_date,
        "line": _get_lines,
        "contact_id": _get_contact,
        "number": _get_number,
    }

    def approve(self, ids, context={}):
        obj = self.browse(ids)[0]
        pick = obj.kao_id
        remain_lines = []
        alltotal = 0
        mixamount = 0
        old_total = 0
        old_amount = 0
        for i, line in enumerate(obj.line):
            move = pick.line[i]
            remain_amount = move.amount - line.amount
            print("=======> ",remain_amount)
            if remain_amount: #inline
                if remain_amount > 0:
                    remain_lines.append({
                        "product_id": move.product_id.id,
                        "amount": remain_amount,
                        "price": move.price,
                        "total": remain_amount * move.price,
                    })
                    mixamount = remain_amount + mixamount 
                    alltotal = (remain_amount * move.price) + alltotal

                    if line.amount:
                        move.write({"amount": line.amount, "price": line.price, "total":line.amount * line.price,"product_id":line.product_id.id, })
                        old_total = old_total + (line.amount * line.price)
                        old_amount = old_amount + line.amount
                    else:
                        move.delete()
                else:
                    move.write({"amount": line.amount, "price": line.price, "total":line.amount * line.price,"product_id":line.product_id.id})
                    old_total = old_total + (line.amount * line.price)
                    old_amount = old_amount + line.amount
            else:
                old_total = old_total + (line.amount * line.price)
                old_amount = old_amount + line.amount
                print("+++++++++")
        pick.write({"alltotal":old_total,"mixamount":old_amount})
        message = ""
        if remain_lines:  #outline 
            vals = {
                "date": pick.date,
                "state": "draft",#kaoteang
                "alltotal": alltotal,
                "mixamount": mixamount,
                "contact_id": pick.contact_id.id,
                "line": [("create", x) for x in remain_lines],
            }
            rpick_id = get_model("kaoteang").create(vals)
            rpick = get_model("kaoteang").browse(rpick_id)
            message = "Picking %s validated and back order %s created" % (pick.number, rpick.number)
        if pick.delivery:
            print("====>delivery")
            cpdelivery_vals = {}
            aa = obj.contact_id
            #res = get_model("test").create(cptest_vals)
            cpdelivery_vals = {
                "contact_id":obj.contact_id.id,
                "date": obj.date,
                "state": "draft", #kaodelivery
                "phone": aa.phone,
                "related_id": "kaoteang,%s"%(pick.id),
                "line":[],
            }

            for line in obj.line:
                line_vals = {
                    "product_id":line.product_id.id,
                    "amount":line.amount,
                    "price":line.price,
                    "total":line.total,
                    }
                cpdelivery_vals["line"].append(("create",line_vals))
            new_cpt = get_model("kao.delivery").create(cpdelivery_vals)
            return {
                "next": {
                    
                    "name": "kao_delivery", #actionnewpage
                    "mode": "form",
                    "active_id": new_cpt
                },
                "flash": "Copy to orderdelivery"
            }
        else:
            return {
                "next": {
                    "name": "kaoteang",
                    "mode": "form",
                    "active_id": pick.id,
                },
                "flash": message,
            }

kaopopup.register()
