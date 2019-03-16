from netforce.model import Model, fields, get_model

class AccountFixedAssetConfirmToPedding(Model):
    _name="account.fixed.asset.confirm.to.pedding"
    _transient=True

    _fields={
        'fix_asset_id': fields.Many2One("account.fixed.asset","Fixed Asset", required=True),
    }

    def _get_fix_asset(self, context={}):
        refer_id=context.get('refer_id', None)
        return refer_id

    _defaults={
        'fix_asset_id': _get_fix_asset,
    }


    def confirm(self, ids, context={}):
        obj=self.browse(ids)[0]
        if obj.fix_asset_id:
            asset=obj.fix_asset_id
            jv_ids=[]
            for case in ["Dispose","Sell"]:
                desc="%s fixed asset [%s] %s" % (case, asset.number, asset.name)
                cond=[
                    ['narration','=',desc],
                    ['state','=','posted'],
                ]
                jv_ids+=get_model("account.move").search(cond)
            get_model("account.move").void(jv_ids)
            asset.to_pending()
            asset.write({"state":"registered"})
            return {
                'next': {
                    'name': 'fixed_asset',
                    'mode': 'form',
                    'active_id': asset.id,
                },
                #'flash': '',
            }

AccountFixedAssetConfirmToPedding.register()
