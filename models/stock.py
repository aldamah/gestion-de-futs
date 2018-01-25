from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
class StockMove(models.Model):
    _inherit = 'stock.move'
