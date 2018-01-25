from odoo import fields, models, api
from pygments.lexer import _inherit

class Entree(models.Model):
    #_name = 'gestiondefuts.purchase.order'
    _inherit = 'purchase.order'
    
    total_entree = fields.Integer(compute='_get_total')
    vehicle_ids = fields.Many2many('fleet.vehicle')
    is_retour = fields.Boolean(default=False)
    
    @api.depends('order_line.product_qty')
    def _get_total(self):
        
        for order in self:
            total_temp = 0
            for line in order.order_line:
                total_temp += line.product_qty
                
            order.update({
            'total_entree': total_temp,
            })
            
