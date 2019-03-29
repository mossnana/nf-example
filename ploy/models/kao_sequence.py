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
import time
from netforce.access import get_active_company
from netforce.utils import print_color


class Kaosequence(Model):
    _inherit = "sequence"
    _fields = {
        "type": fields.Selection([
            ["cust_invoice", "Customer Invoice"],
            ["supp_invoice", "Supplier Invoice"],
            ["cust_credit", "Customer Credit Note"],
            ["supp_credit", "Supplier Credit Note"],
            ["cust_debit", "Customer Debit Note"],
            ["supp_debit", "Supplier Debit Note"],
            ["pay_in", "Incoming Payment"],
            ["pay_out", "Outgoing Payment"],
            ["transfer", "Transfer"],
            ["tax_no", "Tax No"],
            ["debit_tax_no", "Tax No - Debit Note"],
            ["credit_tax_no", "Tax No - Credit Note"],
            ["wht_no", "WHT No"],
            ["account_move", "Journal Entry"],
            ["pick_in", "Goods Receipt"],
            ["pick_internal", "Goods Transfer"],
            ["pick_out", "Goods Issue"],
            ["stock_count", "Stock Count"],
            ["stock_move", "Stock Movement"],
            ["stock_lot", "Lot / Serial Number"],
            ["stock_container", "Container"],
            ["stock_transform", "Product Transforms"],
            ["landed_cost", "Landed Costs"],
            ["shipping_rates", "Shipping Rates"],
            ["delivery_route","Delivery Routes"],
            ["sale_quot", "Sales Quotations"],
            ["sale_order", "Sales Order"],
            ["sale_return","Sales Return"],
            ["ecom_sale_order", "Ecommerce Sales Order"],
            ["purchase_order", "Purchase Order"],
            ["purchase_return","Purchase Return"],
            ["purchase_request", "Purchase Request"],
            ["pos_closure", "POS Register Closure"],
            ["production", "Production Order"],
            ["bom", "Bill of Material"],
            ["service_item", "Service Item"],
            ["job", "Service Order"],
            ["task", "Task"],
            ["project", "Project"],
            ["service_contract", "Service Contract"],
            ["issue", "Issue"],
            ["employee", "Employee"],
            ["payrun", "Payrun"],
            ["leave_request", "Leave Request"],
            ["expense", "Expense Claim"],
            ["fixed_asset", "Fixed Asset"],
            ["claim", "Product Claims"],
            ["borrow", "Product Borrowings"],
            ["contact", "Contact Number"],
            ["ecom_cart","Cart Number"],
            ["rec_vat","Reconcile Vat"],
            ["production_period", "Production Period"],
            ["account_bill_in","Customer Bill Issue"],
            ["account_bill_out","Supplier Bill Issue"],
            ["account_cheque_in","Cheque Receipt"],
            ["account_cheque_out","Cheque Payment"],
            ["account_cheque_move_rb","Cheque Receipt Pay-In"],
            ["account_cheque_move_rp","Cheque Receipt Honor"],
            ["account_cheque_move_rr","Cheque Receipt Return"],
            ["account_cheque_move_rc","Cheque Receipt Cancel"],
            ["account_cheque_move_rs","Cheque Receipt Sale"],
            ["account_cheque_move_pp","Cheque Payment Honor"],
            ["account_cheque_move_pr","Cheque Payment Return"],
            ["account_cheque_move_pc","Cheque Payment Cancel"],
            ["account_advance","Advance Payment"],
            ["account_advance_clear","Advance Clearing"],
            ["allocate_group","Allocate Group"],
            ["allocate_prepaid_expense","Allocate Prepaid Expense"],
            ["petty_cash_received","Petty Cash Received"],
            ["petty_cash_payments","Petty Cash Payments"],
            ["rm_inspect","RM inspection"],
            ["qc_inspect","QC inspection"],
            ["production_plan","Production Plan"],
            ["kaoteang","Kaoteang"],
            ["kaoproduct","KaoProduct"],
            ["kaodelivery","Kaodelivery"],
            ["other", "Other"],
            

            ], "Type", required=True, search=True),
    }




Kaosequence.register()
