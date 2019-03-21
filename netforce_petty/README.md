## Petty Cash Module
Module แรกที่ทำ

### เทคนิคที่ใช้
#### 1. field JSON
  - ใน model
  ```python
  class PettyCash(Model):
    _name="petty.cash"
    
    _string = "Petty Cash"
  
    // field เรียก function get_number_receive
    _fields={
    "number_receive_total": fields.Json("Number of Payment Receive", function="get_number_receive"),
    }
    
""" ============================================================================== """

    // ในกรณี เอาค่าไปใช้ใน layout xml ให้ return ค่าเป็น ก้อน object ซึ่งสามารถทำออกมาได้หลาย function
    def get_number_receive(self, ids, context={}):
        res = {}
        for obj in self.browse(ids):
            receive_ptc = get_model("petty.cash.fund").search([['number_receive', '!=', None]])
            res[obj.id] = receive_ptc
        // return ออกไปเป็นก้อน object ของข้อมูล
        return res

""" ============================================================================== """

    // ในกรณีใช้เป็นค่า default โดยตรง ให้ return ค่าได้เลยโดยตรง
    def _get_num_receive(self,context={}):
        receive_ptc = get_model("petty.cash.fund").search([['number_receive', '!=', None]])
        return receive_ptc

""" ============================================================================== """
    
    _defaults= {
    "number_receive_total": _get_num_receive
    }
  ```
  
  - ในไฟล์ XML
  ```xml
  <!-- อ้างอิงถึงไฟล์ JSON -->
  <field name="number_receive_total" span="2" invisible="1" view="field_code"/>
  
  <!-- นำไปใช้ ให้อ้างอิง field name JSON ด้านบน -->
  <!-- condition='[["id","in",number_receive_total]]' หมายถึง ให้แสดงรายการ id ที่มี Receive Petty Cash อยู่ -->
  <field name="fund_id" span="2" required="1" onchange="onchange_fund_pay" condition='[["id","in",number_receive_total]]'/>
  ```
  <br/>
  
  #### 2. การให้แสดง read only mode ในสถานะเฉพาะนั้นๆ
  เพิ่ม:
  ` attrs='{"readonly":[["ชื่อ field","in",["approved","voided"]]]}' `
  เข้าไปที่ tag form ในตัวอย่างคือ 
  
  ```xml
  <form model="petty.cash.fund" attrs='{"readonly":[["state","in",["approved","voided"]]]}' show_company="1">
    ...
  </form>
  ```
  <br/>
  
  #### 3. การใช้ attibute condition และ states
  - ใช้ใน Model
      ```python
      _fields = { "fund_id":fields.Many2One("petty.cash.fund","Petty Cash Fund", condition=[["state", "=", "approved"]], search=True), }
      ```
  - ใช้ใน Layout
    - ในตัวอย่างหมายถึง กรองข้อมูลที่ field type เป็น pay_in หรือ pay_out
      ```xml
      <field name="sequence_id" span ="4" condition='[["type","in",["pay_in","pay_out"]]]' onchange="onchange_sequence"/>
      ```
    - attibute states คือ โชว์ field เมื่ออยู่ในสถานะนั้นๆ ในตัวอย่างหมายถึงว่า ปุ่ม Draft จะขึ้นมาก็ต่อเมื่อเอกสารอยู่ในสถานะ posted
      ```xml
      <item string="To Draft" method="to_draft" states="posted"/>
      ```
