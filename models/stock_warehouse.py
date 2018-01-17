from odoo import api, fields, models, _

class Warehouse(models.Model):
    _inherit = "stock.warehouse"