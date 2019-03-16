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
from datetime import *
from dateutil.relativedelta import *
import time
from netforce.access import get_active_company,set_active_user,set_active_company,get_active_user

class FixedAssetSell(Model):
    _name = "account.fixed.asset.sell"
    _string = "Sell Asset"
    _fields = {
        "asset_id": fields.Many2One("account.fixed.asset", "Asset", readonly=True),
        "date": fields.Date("Date", required=True),
        "sale_acc_id": fields.Many2One("account.account", "Account to Debit for Sale", required=True),
        "gain_loss_acc_id": fields.Many2One("account.account", "Gain / Loss Account", required=True),
        "journal_id" : fields.Many2One("account.journal", "Account Journal", required=True),
        "price": fields.Decimal("Sale price (Excluding Tax)", required=True),
        "accum_depr_amount": fields.Decimal("Accum. Depr. Amount"),
    }
    _defaults = {
        "date": lambda *a: time.strftime("%Y-%m-%d"),
    }

    def onchange_date(self,context):
        data=context["data"]
        asset_id = data.get("asset_id")
        date=data.get("date")
        if not asset_id or not date:
           return data
        days = None
        accum_depr_amount = 0
        obj_asset = get_model("account.fixed.asset").browse(asset_id)
        if not obj_asset.last_dep:
           raise Exception("No Last depreciation")
        if obj_asset.last_dep:
            d_from=datetime.strptime(obj_asset.last_dep,"%Y-%m-%d")+timedelta(days=1)
        else:
            d_from=datetime.strptime(obj_asset.date_purchase,"%Y-%m-%d")+timedelta(days=1)
        d_to=datetime.strptime(date,"%Y-%m-%d")
        days = (d_to - d_from).days+1
        rate=obj_asset.get_daily_rate(d_from.strftime("%Y-%m-%d"))
        accum_depr_amount=get_model("currency").round(None,days*rate)
        data['accum_depr_amount'] = accum_depr_amount
        return data

    def sell_depreciation(self,ids,context):
        obj=self.browse(ids)[0]
        if obj.asset_id.last_dep:
            d_from=datetime.strptime(obj.asset_id.last_dep,"%Y-%m-%d")+timedelta(days=1)
        else:
            d_from=datetime.strptime(obj.asset_id.date_purchase,"%Y-%m-%d")
        d_to=datetime.strptime(obj.date,"%Y-%m-%d")
        days = (d_to - d_from).days+1
        if days > 30:
           raise Exception(" (Last depreciation : %s ) - (Date : %s ) Over 30 Days, Please Check Date"%(obj.asset_id.last_dep,obj.date))
        elif days <= 0:
           raise Exception(" (Last depreciation : %s ) - (Date : %s ) less 0 Days, Please Check Date"%(obj.asset_id.last_dep,obj.date))
        narration = "Fixed asset depreciation [%s] %s"%((obj.asset_id.number or ""),(obj.asset_id.name or ""))
        get_model("account.fixed.asset").depreciate([obj.asset_id.id],obj.date,context={"narration":narration})

        if obj.asset_id.periods:
            obj.write({
                'accum_depr_amount': obj.asset_id.periods[0].amount,
            })
        return {
            "flash":"registered assets (%s) are depreciated to %s"%(obj.asset_id.number,obj.date),
        }

    def sell(self, ids, context={}):
        settings=get_model("settings").browse(1)
        obj = self.browse(ids)[0]
        if settings.lock_date:
            assert obj.date >= settings.lock_date, "Accounting transaction is before lock date"
        journal_id=obj.journal_id.id
        if not journal_id:
            raise Exception("Account Journal not found")
        asset = obj.asset_id
        # FIX ME cannot use asset.book_val
        if asset.book_val is not None and asset.book_val == 0:
            pass
        elif not asset.last_dep:
            raise Exception("No last depreciation")
        elif asset.last_dep and asset.last_dep > obj.date:
            raise Exception("Cannot sell before last depreciation date %s"%asset.last_dep)
        elif asset.book_val is None or asset.salvage_value is None or asset.book_val > asset.salvage_value:
            if asset.last_dep < obj.date and asset.dep_rate:
                raise Exception("Last depreciation : %s  <  Date : %s, Please Depreciation First"%(asset.last_dep,obj.date))
        desc = "Sell fixed asset [%s] %s" % (asset.number, asset.name)
        ## get number
        number_jv = get_model("account.move")._get_number(context={"journal_id":journal_id})
        move_vals = {
            "journal_id": journal_id,
            "date": obj.date,
            "narration": desc,
            "related_id": "account.fixed.asset,%s"%asset.id
        }
        if number_jv:
            move_vals["number"] = number_jv
        lines = []
        amt = -asset.price_purchase
        line_vals = {
            "description": desc,
            "account_id": asset.fixed_asset_account_id.id,
            "debit": amt > 0 and amt or 0,
            "credit": amt < 0 and -amt or 0,
        }
        if asset.fixed_asset_account_id.require_track and asset.track_id.id:
            line_vals['track_id']=asset.track_id.id
        lines.append(line_vals)

        amt = asset.price_purchase - asset.book_val
        line_vals = {
            "description": desc,
            "account_id": asset.accum_dep_account_id.id,
            "debit": amt > 0 and amt or 0,
            "credit": amt < 0 and -amt or 0,
        }
        if asset.accum_dep_account_id.require_track and asset.track_id.id:
            line_vals['track_id']=asset.track_id.id
        lines.append(line_vals)

        amt = obj.price
        line_vals = {
            "description": desc,
            "account_id": obj.sale_acc_id.id,
            "debit": amt > 0 and amt or 0,
            "credit": amt < 0 and -amt or 0,
        }
        if obj.sale_acc_id.require_track and asset.track_id.id:
            line_vals['track_id']=asset.track_id.id
        lines.append(line_vals)

        amt = asset.book_val - obj.price
        line_vals = {
            "description": desc,
            "account_id": obj.gain_loss_acc_id.id,
            "debit": amt > 0 and amt or 0,
            "credit": amt < 0 and -amt or 0,
        }
        if obj.gain_loss_acc_id.require_track and asset.track_id.id:
            line_vals['track_id']=asset.track_id.id
        lines.append(line_vals)

        move_vals["lines"] = [("create", v) for v in lines]
        move_id = get_model("account.move").create(move_vals)
        get_model("account.move").post([move_id])
        asset.write({"state": "sold", "date_dispose": obj.date})
        return {
            "next": {
                "name": "fixed_asset",
                "mode": "form",
                "active_id": asset.id,
            }
        }

FixedAssetSell.register()
