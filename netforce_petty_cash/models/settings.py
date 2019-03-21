from netforce.model import Model, fields

class Settings(Model):
    _inherit="settings"
    _fields={
        'petty_cash_journal_id': fields.Many2One("account.journal","Petty Cash Journal"),
    }

Settings.register()
