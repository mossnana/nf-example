# Copyright (c) 2012-2015 Netforce Co. Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from netforce.model import Model, fields, get_model
from netforce.utils import get_data_path

class KaoPickValidate(Model):
    _inherit = "pick.validate"


    def do_validate(self, ids, context={}):
        st=get_model("settings").browse(1) 
        obj = self.browse(ids)[0]
        remain_lines = []
        if not obj.date:
            raise Exception("Missing Validation Date")
        pick = obj.picking_id
        
        print("==============================")
        print("related to :",pick.related_id.contact_id.id)
        remain_lines = []
        for checkqty in obj.lines:
            for checkamount in pick.related_id.line:
                if checkqty.product_id.id == checkamount.product_id.id:
                    print("checkqtyp",checkqty.product_id.id)
                    print("checkamountp",checkamount.product_id.id)
                    checkdev = checkamount.amount - (checkamount.devqty or 0 )
                    if checkqty.qty <= checkdev:
                        print("checkqty",checkqty.qty)
                        print("checkamount",checkamount.amount,checkamount.devqty)
     #ploy###########################################################ploy 
                        for i, line in enumerate(obj.lines):
                            if checkqty.id != line.id:continue
                            move = pick.lines[i]
                            ########################################
                            print("##################read new line################################")
                            # check related product
                            have_prod = False
                            right_location = False
                            if pick.related_id.id and (pick.related_id._model == 'sale.order' or pick.related_id._model == 'purchase.order'):
                                for prod in pick.related_id.lines:
                                    if (move.product_id.id == prod.product_id.id):
                                        have_prod = True
                                    if (prod.location_id.id == move.location_from_id.id) and pick.related_id._model == 'sale.order':
                                        right_location = True
                                    elif (prod.location_id.id == move.location_to_id.id) and pick.related_id._model == 'purchase.order':
                                        right_location = True
                                if not have_prod:
                                    raise Exception("Product %s in line %s not in %s number %s"%(move.product_id.code,i+1,pick.related_id._model,pick.related_id.number))
                                if not right_location:
                                    raise Exception("Product %s in line %s select difference location then %s[%s]"%(move.product_id.code,i+1,pick.related_id._model,pick.related_id.number))
                            ########################################
                            # prevent to validate stock if it's not enough
                            if st.prevent_validate_neg_stock and pick.type in ('out','internal') and move.location_from_id.type!='production': #and move.product_id.type != "consumable":
                                lot_id=line.lot_id and line.lot_id.id or None
                                key=(move.product_id.id, lot_id, move.location_from_id.id, None)
                                keys=[key]
                                bals = get_model("stock.balance").compute_key_balances_qty(keys,context={"virt_stock":False, "date_to": obj.date or pick.date, "move_id": move.id})

                                bal_qty=min(bals[key][3],bals[key][0])
                                line_qty = get_model("uom").convert(line.qty, line.uom_id.id, line.product_id.uom_id.id)
                                if line_qty>bal_qty and line_qty>0:
                                    prod=move.product_id
                                    lot=lot_id and "Lot %s"%line.lot_id.number or ""
                                    raise Exception("Stock is not enough :Line %s [%s] %s, %s (%s of %s) on %s"%(i+1,prod.code,prod.name,lot,line.qty,bal_qty,obj.date or pick.date))
                            ########################################
                            remain_qty = move.qty - get_model("uom").convert(line.qty, line.uom_id.id, move.uom_id.id)
                            if remain_qty:
                                remain_lines.append({
                                    "date": move.date,
                                    "product_id": move.product_id.id,
                                    "location_from_id": move.location_from_id.id,
                                    "location_to_id": move.location_to_id.id,
                                    "qty": remain_qty,
                                    "uom_id": move.uom_id.id,
                                    "cost_price": move.cost_price,
                                    'cost_price_cur': move.cost_price_cur,
                                    "cost_amount": move.cost_price*remain_qty,
                                    "state": move.state,
                                    "related_id": "%s,%s"%(move.related_id._model,move.related_id.id) if move.related_id else None,
                                })
                            if line.qty:
                                move.write({"qty": line.qty, "uom_id": line.uom_id.id, "cost_amount":line.qty*(move.cost_price or 0),"cost_amount_cur":line.qty*(move.cost_price_cur or 0) if move.cost_price != move.cost_price_cur else 0, "lot_id": line.lot_id and line.lot_id.id or None})
                            else:
                                move.delete()

                    else:
                        raise Exception("ส่งของเกินที่สั่ง")

        if remain_lines:
            vals = {
                "type": pick.type,
                "contact_id": pick.contact_id.id,
                "journal_id": pick.journal_id.id,
                "date": pick.date,
                "ref": pick.number,
                "lines": [("create", x) for x in remain_lines],
                "state": pick.state,
            }
            if pick.related_id:
                vals["related_id"]="%s,%d"%(pick.related_id._model,pick.related_id.id)
            rpick_id = get_model("stock.picking").create(vals, context={"pick_type": pick.type})
            rpick = get_model("stock.picking").browse(rpick_id)
            message = "Picking %s validated and back order %s created" % (pick.number, rpick.number)
        else:
            message = "Picking %s validated" % pick.number
        pick.write({ "date": obj.date })
        pick.set_done()
        if pick.type == "in":
            action = "pick_in"
        elif pick.type == "out":
            action = "pick_out"
        elif pick.type == "internal":
            action = "pick_internal"

        return {
            "next": {
                "name": action,
                "mode": "form",
                "active_id": pick.id,
            },
            "flash": message,
        }


                

KaoPickValidate.register()
