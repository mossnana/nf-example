# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import os
import random
import requests
import uuid

from netforce.model import Model, fields, get_model
from netforce.database import get_connection, get_active_db

def get_rand():
    return int(random.random()*10000)

class ReportTemplate(Model):
    _inherit = "report.template"
    _fields = {
            "type": fields.Selection([
            ["cust_invoice", "Customer Invoice"],
            ["cust_debit_note", "Customer Debit Note"],
            ["cust_credit_note", "Customer Credit Note"],
            ["supp_invoice", "Supplier Invoice"],
            ["payment", "Payment (Base)"],
            ["account_move", "Journal Entry"],
            ["sale_quot", "Quotation"],
            ["sale_order", "Sales Order"],
            ["purch_order", "Purchase Order"],
            ["purchase_request", "Purchase Request"],
            ["prod_order", "Production Order"],
            ["goods_receipt", "Goods Receipt"],
            ["goods_transfer", "Goods Transfer"],
            ["goods_issue", "Goods Issue"],
            ["pay_slip", "Pay Slip"],
            ["tax_detail", "Tax Detail"],
            ["hr_expense", "HR Expense"],
            ["landed_cost","Landed Cost"],
            ["borrow_form", "Borrow Request"],
            ["claim_bill","Claim Bill"],

            # XXX: Better add by config
            ["cust_payment", "Receipt"],
            ["supp_payment", "Payment"],
            ["account_bill","Bill Issue"],
            ["account_cheque","Cheque"],
            ["account_advance","Advance Payment"],
            ["account_advance_clear","Advance Clearing"],

            # XXX: petty cash
            ["petty_cash", "Petty Cash"],

            ["other", "Other"]], "Template Type", required=True, search=True),
    }


ReportTemplate.register()

