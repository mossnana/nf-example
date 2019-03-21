from netforce.model import Model,fields,get_model

class PriceType(Model):
    _name="price.type"
    _string="Price Type"
    _key = ["name"]
    _fields={
        "name": fields.Char("Name",required=True),
        "currency_id": fields.Many2One("currency","Currency",required=True),
        "uom_id": fields.Many2One("uom","UoM",required=True),
        "price_format": fields.Char("Price format"),
        "price_format_factor": fields.Decimal("Price format factor",scale=6),
    }

    def convert(self,price,from_id,to_id,context={}):
        pt_from=self.browse(from_id)
        pt_to=self.browse(to_id)
        price_qty=get_model("uom").convert(price,pt_to.uom_id.id,pt_from.uom_id.id,context=context)
        price_cur=get_model("currency").convert(price_qty,pt_from.currency_id.id,pt_to.currency_id.id,context=context)
        return price_cur

PriceType.register()
