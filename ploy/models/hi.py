from netforce.model import Model,fields,get_model 
from netforce.utils import get_data_path
import pprint

class hi(Model):
    _name = "testhi" #NAMETABLE
    _string = "Sheet"
    _fields = {
        "remix_id":fields.Many2One("test","Ploy"),
        "mixnum":fields.Many2One("testsearch","MResult"), #line  
        "num1":fields.Decimal("Num1"),
        "num2":fields.Decimal("Num2"),
        "num3":fields.Decimal("Result"),
        "onnmcd":fields.Char("Name & Code"),
    }


    #def confirm(self, ids, context={}):
        #obj = self.browse(ids)[0]
        #x = obj.num1
        #y = obj.num2
        #obj.write({"num3":(x+y)})    

   #def confirm(self, ids, context={}):
        #print(ids)
        #print(self.browse(ids)[0])

    def onchange_result(self, context={}):
        data = context["data"]
        #path = context["path"]
        print(data)
        #print(path)
        #xy = get_data_path(data, path, parent = True)
        #pprint.pprint(xy)
        x = data.get("num1") or 0
        y = data.get("num2") or 0
        data["num3"] = x+y
        #x1 = xy.get("num1")
        #xy["amt"] = x1+y1
        #for l in data["lines"]:
            

        return data

    def confirm(self, ids, context={}):
        obj = self.browse(ids)[0]
        x = obj.num1
        y = obj.num2
        obj.write({"num3":(x+y)})

hi.register()
