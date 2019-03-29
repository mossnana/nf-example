from netforce.model import Model,fields,get_model 
from netforce.access import get_active_company, get_active_user, set_active_user
from netforce.utils import get_data_path


class test(Model):
    _name = "test" #NAMETABLE
    _string = "test123"
    _fields = {
        "code":fields.Char("Code", required=True),
        "description":fields.Text("Description"),
        "qty":fields.Decimal("Qty"),
        "name":fields.Char("Name"),
        "line":fields.One2Many("testhi","remix_id","ResultMix"),
        "invoice_id": fields.Many2One("account.invoice", "Invoice"),
        }

    def write(self, ids, vals, context={}):
        print(vals)
        super().write(ids, vals, context)

    def onchange_code(self, context={}):
        data = context["data"]
        path = context["path"]
        print(context)
        line = get_data_path(data, path, parent=True)
        print(data.get("code"))
        print(data)
        for line in data['line']:
            line['num1'] = data['code']    
        return data

    def onchange_qty(self, context={}):
        try:
            data = context["data"]
            path = context["path"]
            line = get_data_path(data, path, parent=True)
            data['name'] = data['code']
            res = 0
            for line in data['line']: 
                print(line.get('num2'))
                res += line.get('num2')
            data['qty'] = res
            return data
        except:
            raise Exception("NO!!!")

    def onchange_invoice(self, context={}):
        data = context["data"]
        id = data["invoice_id"]
        print(id)
        invoice_id = get_model("account.invoice").browse(id)
        data['description'] = invoice_id.contact_id.name
        return data

    #def _get_name(self, context={}):
        #name = "Ploy1234"
        #return name

    #_defaults = {
        #"name": _get_name,
 
    # "state"
test.register()
