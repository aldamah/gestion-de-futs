from odoo import fields, models, api

class SaleOrder(models.Model):
    #_name = 'gestiondefuts.sale.order'
    _inherit = 'sale.order'
    total_sortie = fields.Integer(compute='_get_total')
    vehicle_ids = fields.Many2many('fleet.vehicle')
    
    
   
    @api.depends('order_line.product_uom_qty')
    def _get_total(self):
        
        for order in self:
            total_temp = 0
            for line in order.order_line:
                total_temp += line.product_uom_qty
                
            order.update({
            'total_sortie': total_temp,
            })
    
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    avec_futs = fields.Boolean("Facturer les futs", default=False)