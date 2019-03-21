from netforce.model import Model, fields, get_model
from datetime import *
from dateutil.relativedelta import *
from netforce.access import get_active_company
from . import num2word

def fmt_thai_tax_no(tax_no):
    s = tax_no or ""
    s.replace("-", "")
    if len(s) < 13:
        s += " " * (13 - len(s))
    return s

class ReportThaiWHTCertif(Model):
    _inherit = "report.thai.wht.certif"
    _fields = {
        "petty_cash_id": fields.Many2One("petty.cash", "Petty Cash", condition=[["state", "=", "posted"],["type","=","out"],["wht_taxes.tax_type","=","wht"]], on_delete="cascade"),
    }

    def get_report_data(self, ids, context={}):
        if not ids:
            return
        obj = self.browse(ids)[0]
        company_id = get_active_company()
        company = get_model("company").browse(company_id)
        settings = get_model("settings").browse(1)
        criteria = [["state","=","posted"],["move_id.lines.tax_comp_id.type", "=", "wht"]]
        if obj.date_from:
            criteria += [["date",">=",obj.date_from]]
        if obj.date_to:
            criteria += [["date","<=",obj.date_to]]
        payments = []
        clearings = []
        petty = []
        if obj.advance_clearing_id:
            criteria_cle = criteria + [["id","=",obj.advance_clearing_id.id]]
            clearings = get_model("account.advance.clear").search_browse(criteria_cle)
        if obj.payment_id:
            criteria_pay = criteria + [["id","=",obj.payment_id.id]]
            criteria_pay += [["type","=","out"]]
            payments = get_model("account.payment").search_browse(criteria_pay)
        if obj.petty_cash_id:
            criteria_petty = criteria + [["id","=",obj.petty_cash_id.id]]
            criteria_petty += [["type","=","out"]]
            petty = get_model("petty.cash").search_browse(criteria_petty)
        lines = []
        data_moves = []
        for cle in clearings:
            data_moves.append({
                "date": cle.date,
                "contact_id": cle.contact_id,
                "move_id": cle.move_id,
            })
        for pmt in payments:
            data_moves.append({
                "date": pmt.date,
                "contact_id": pmt.contact_id,
                "move_id": pmt.move_id,
            })
        for pet in petty:
            data_moves.append({
                "date": pet.date,
                "contact_id": pet.contact_id,
                "move_id": pet.move_id,
            })
        for data_move in data_moves:
            move=data_move.get('move_id')
            if not move:
                raise Exception("Journal entry not found")
            data={
                "company_tax_no": fmt_thai_tax_no(settings.tax_no),
                "company_name": company.name,
                "dept_addr": settings.default_address_id.address_text.replace("\n"," ") if settings.default_address_id else None, # XXX
                #"tax_no": fmt_thai_tax_no(contact.tax_no),
                #"partner_name": contact.name,
                "date": datetime.strptime(data_move.get('date'),"%Y-%m-%d").strftime("%d/%m/%Y"),
                "lines": [{}], # XXX
            }
                
            base={}
            tax={}
            contact_type=None
            wht_no=None
            for line in move.lines:
                contact=line.contact_id
                if contact.default_address_id:
                    data["tax_no"] = fmt_thai_tax_no(contact.tax_no)
                    data["partner_name"] = contact.name
                    data["partner_addr"]=contact.default_address_id.address_text.replace("\n"," ") if contact.default_address_id else None
                comp=line.tax_comp_id
                if not comp:
                    continue
                if comp.type!="wht" or comp.trans_type!="in":
                    continue
                if not wht_no:
                    wht_no=line.tax_no
                else:
                    if wht_no!=line.tax_no:
                        raise Exception("Multiple WHT numbers for same payment")
                if not contact_type:
                    contact_type=comp.contact_type
                else:
                    if contact_type!=comp.contact_type:
                        raise Exception("Different WHT contact types for same payment")
                if line.contact_id:
                    contact=line.contact_id
                    data["partner_name"]=contact.name or ""
                    if contact.addresses:
                        data["partner_addr"]=(contact.default_address_id.address_text.replace("\n"," ")).replace(",","") if contact.default_address_id else None
                    data["tax_no"]=fmt_thai_tax_no(line.contact_id.tax_no) or " "
                if comp.exp_type=="salary":
                    exp_code="1"
                elif comp.exp_type=="commission":
                    exp_code="2"
                elif comp.exp_type=="royalty":
                    exp_code="3"
                elif comp.exp_type=="interest":
                    exp_code="4"
                elif comp.exp_type in ("rental","service","transport","advert"):
                    #exp_code="5"
                    exp_code="5_%s"%(int(comp.rate))
                else:
                    exp_code="6"
                    data["desc"]=comp.description
                if line.tax_date:
                    data["date"] = datetime.strptime(line.tax_date,"%Y-%m-%d").strftime("%d/%m/%Y")
                base.setdefault(exp_code,0)
                tax.setdefault(exp_code,0)
                base[exp_code]+=line.tax_base
                tax[exp_code]+=line.credit-line.debit
            #if not wht_no:
                #raise Exception("WHT number not found")
            data["number"]=wht_no
            if contact_type=="individual":
                data["num_user1"]="x"
                data["num_user2"]=""
            elif contact_type=="company":
                data["num_user1"]=""
                data["num_user2"]="x"

            ##################################
            amt_code5=[]
            tax_code5=[]
            for exp_code,amt in base.items():
                if '5_' in exp_code:
                    amt_code5.append(amt)
                    base[exp_code]=0
            for exp_code,amt in tax.items():
                if '5_' in exp_code:
                    tax_code5.append(amt)
                    tax[exp_code]=0
            rate_min=1
            rate_max=6
            amt_code5.reverse()
            tax_code5.reverse()
            for i in range(rate_min,rate_max):
                try:
                    base['5_%s'%(i)]=amt_code5[i-1]
                except:
                    base['5_%s'%(i)]=0
            for i in range(rate_min,rate_max):
                try:
                    tax['5_%s'%(i)]=tax_code5[i-1]
                except:
                    tax['5_%s'%(i)]=0
            ##################################

            data["sum_amt"]=sum(base.values())
            data["sum_tax"]=sum(tax.values())
            for exp_code,amt in base.items():
                data["amt_"+exp_code]=amt
                if "5_" in exp_code and not amt:
                    data["amt_"+exp_code]=None
            for exp_code,amt in tax.items():
                data["tax_"+exp_code]=amt
                if "5_" in exp_code and not amt:
                    data["tax_"+exp_code]=None
            data["total_word"]=num2word.num2word_th(data["sum_tax"],l='th')
            lines.append(data)
        return {"obj": {"lines": lines}}

ReportThaiWHTCertif.register()

