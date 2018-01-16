from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    retour_id = fields.Many2one('gestiondefuts.retour', string="Retour", readonly=True)
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    retour_id = fields.Many2one('gestiondefuts.retour',
        'Retour', ondelete='set null', index=True, readonly=True)