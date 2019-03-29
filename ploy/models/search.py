from netforce.model import Model,fields,get_model 
from netforce.utils import get_data_path
from netforce.access import get_active_company, get_active_user, set_active_user
class search(Model):
    _name="testsearch"
    _fields= {
        "product_id": fields.Many2One("product", "Product", search=True),
        "contact_id": fields.Many2One("contact", "Customer", required=True, search=True),
        "sale_id": fields.Many2One("sale.order", "Sale"),
        "qty_total": fields.Decimal("Total Qty"),
        "line":fields.One2Many("testhi","mixnum","Number"),
        "mnum1":fields.Decimal("Number1"),
        "mnum2":fields.Decimal("Number2"),
        "mnum3":fields.Decimal("Result"),
        "namcod":fields.Char("Name && Code"),
        "state":fields.Selection([("draft","Draft"), ("confirmed","Confirmed"), ("done","Completed"), ("voided", "Voided")], "Status", required=True,search=True),
        }
    _defaults = {
        "state": "draft",
    }

    def approve(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state != "draft":
            raise Exception("No Confirm data")
        obj.write({"state": "confirmed"})

    def confirmed(self, ids, context={}):
        obj = self.browse(ids)[0]
        if obj.state != "confirmed":
            raise Exception("No Completed")
        obj.write({"state":"done"})

    def to_draft(self, ids, context={}):
        obj = self.browse(ids)[0]
        obj.write({"state":"draft"})

    def copy(self, ids, context={}):
        obj = self.browse(ids)[0]
        vals = {
            "contact_id": obj.contact_id.id,
            "namcod": obj.namcod,
            "mnum1":obj.mnum1,
            "mnum2":obj.mnum2,
            "mnum3":obj.mnum3,
            "line": [],
        }
        for line in obj.line:
            line_vals = {
                "num1": line.num1,
                "num2": line.num2,
                "num3": line.num3,
                "onnmcd": obj.onnmcd,
            }
            vals["line"].append(("create", line_vals))
        new_id = self.create(vals) #createI
        #new_obj = self.browse(new_id)

        return {
            "next": {
                "name": "tsearch",  #action
                "mode": "form", #type
                "active_id": new_id #id
            },
            "flash": "Copy Complete"
        }

    def copytest(self, ids, context={}):
        obj = self.browse(ids)[0]
        cptest_vals = {}
        aa = obj.contact_id
        #res = get_model("test").create(cptest_vals)
        cptest_vals = {
            "name":obj.contact_id.name,
            "description":obj.contact_id.country_id.name,
            "code": aa.code,
            "name": aa.name,
            "qty": obj.qty_total,
            "test": obj.qty_total,
            "line":[],
        }     

        for line in obj.line:
            line_vals = {
                "num1":line.num1,
                "num2":line.num2,
                "num3":line.num3,
            }
            cptest_vals["line"].append(("create",line_vals)) 
        new_cpt = get_model("test").create(cptest_vals)
        return {
            "next": {
                "name": "test", #actionnewpage
                "mode": "form",
                "active_id": new_cpt
            },
            "flash": "Copy to testmodel"
        }

    def onchange_product(self, context={}):
        data = context["data"]
        id = data["sale_id"]
        print(id)
        sale_id = get_model("sale.order").browse(id)
        result = 0
        for x in sale_id.lines: #ไปหาข้อมูลในไลน์มาใช้ ไล่ทีละตัว
            print(x.qty)
            result += x.qty
        data['qty_total'] = result
        #data['qty_total'] = sale_id.qty_total
        return data 

    def onchange_namcod(self,context={}):
        data = context["data"]
        id = data["contact_id"]
        print(id)
        contact_id = get_model("contact").browse(id)
        #data['namcod'] = contact_id.name +  contact_id.code 
        namcod = "%s [%s]"%(contact_id.name,contact_id.code)
        data['namcod'] = namcod
        #data['namcod'] = "{}, ({})".format(contact_id.name, contact_id.code)     
        for line in data["line"]: #เอาข้อมูลที่ได้มาใส่ในไลน์
            line['onnmcd'] = namcod
        return data
         
    def onchange_mnum1(self, context={}):
        data = context["data"]
        path = context["path"]
        mix = get_data_path(data, path, parent=True)  #ลอคแถว
        mix["num3"] = (mix.get("num1") or 0) + (mix.get("num2") or 0)
        print("path:" ,path)
        #remnum1 = 0
        #remnum2 = 0
        #remnum3 = 0
        remnum1, remnum2, remnum3 = 0, 0, 0
        for x in data["line"]:
            remnum1 += x.get('num1') or 0
            remnum2 += x.get('num2') or 0
            remnum3 += x.get('num3') or 0
        data['mnum1'] = remnum1
        data['mnum2'] = remnum2
        data['mnum3'] = remnum3

        return data 

search.register()
