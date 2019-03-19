def onchange_product(self, context={}):
        data=context['data']
        path=context['path']
        line = get_data_path(data, path, parent=True)
        product_model=get_model("product").browse(line.get("product_id"))
        line["description"] = product_model.description
        line["account_id"] = product_model.purchase_account_id.id
        #line["tax_id"] = product_model.purchase_tax_id.id or product_model.categ_id.purchase_tax_id.id
        if product_model.purchase_tax_id is not None and product_model.purchase_tax_id.id:
            print("{} use tax from product".format(product_model.name))
            line["tax_id"] = product_model.purchase_tax_id.id
        else:
            if product_model.categ_id.purchase_tax_id is not None and product_model.categ_id.purchase_tax_id.id:
                print("{} use tax from cate tax".format(product_model.name))
                line["tax_id"] = product_model.categ_id.purchase_tax_id.id
            else:
                print("{} use tax from default".format(product_model.name))
                line["tax_id"] = None
        if line['tax_id']:
            line['tax_type'] = "Tax Exclusive"
        else:
            line['tax_type'] = None
        if data.get("fund_id"):
            fund_id = get_model("petty.cash.fund").browse(int(data.get("fund_id")))
            if fund_id:
                data["number_receive"] = fund_id.number_receive.id if fund_id.number_receive else None
                data["amount_bal"] = fund_id.acc_bal
                if data.get("type") == "out":
                    line['track_id'] = fund_id.track_id.id if fund_id.track_id else None
                    line['track2_id'] = fund_id.track2_id.id if fund_id.track2_id else None
        return data
