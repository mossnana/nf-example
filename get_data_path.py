def onchange_product(self, context={}):
        
        # data เก็บข้อมูลของ fields ทั่วไป
        data=context['data']
        
        # path ตัวช่วยเข้าถึงข้อมูลใน line 1 บรรทัด
        path=context['path']
        
        # get_data_path ทำการจับคู่ข้อมูลของ line นั้นๆ กับแต่ละบรรทัด โดยไม่ต้อง for ... in ...
        line = get_data_path(data, path, parent=True)
        
        # เอาข้อมูล Product มาจาก model ของ Product ใน line นั้นๆ
        # line.get("product_id") -> id ของ Product ใน line นั้นๆ 1 บรรทัด
        product_model=get_model("product").browse(line.get("product_id"))
        
        # กำหนดให้ช่อง description ของ line นั้น ให้ตาม Product
        line["description"] = product_model.description
        
        # กำหนดให้ช่อง account_id ของ line นั้น ให้ตาม Product
        line["account_id"] = product_model.purchase_account_id.id
        
        # ถ้าตัว Product ใน line นั้นๆ มี Purchase Tax ที่ถูกกำหนดในตัว Product
        if product_model.purchase_tax_id is not None and product_model.purchase_tax_id.id:
            line["tax_id"] = product_model.purchase_tax_id.id
        # แต่ถ้าไม่เจอ Purchase Tax ใน Product Tax .....
        else: # ให้ไปหาต่อใน ....
            # ใน Product Category ไปดึง Purchase Tax มา
            if product_model.categ_id.purchase_tax_id is not None and product_model.categ_id.purchase_tax_id.id:
                line["tax_id"] = product_model.categ_id.purchase_tax_id.id
            else:
                # แต่ถ้าไม่เจอทั้ง 2 ที่ให้เป็น None
                line["tax_id"] = None
        
        # ถ้ามี Purchase Tax ให้ตั้ง Tax Type เป็น Tax Exclusive
        if line['tax_id']:
            line['tax_type'] = "Tax Exclusive"
        else: # ถ้ามีให้ใส่ None
            line['tax_type'] = None
        
        # ถ้ามี Petty Cash Fund ให้ไปดึง Track มา
        if data.get("fund_id"):
            fund_id = get_model("petty.cash.fund").browse(int(data.get("fund_id")))
            if fund_id:
                data["number_receive"] = fund_id.number_receive.id if fund_id.number_receive else None
                data["amount_bal"] = fund_id.acc_bal
                if data.get("type") == "out":
                    line['track_id'] = fund_id.track_id.id if fund_id.track_id else None
                    line['track2_id'] = fund_id.track2_id.id if fund_id.track2_id else None
        return data
