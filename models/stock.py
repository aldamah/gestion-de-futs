from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    retour_id = fields.Many2one('gestiondefuts.retour', string="Retour", readonly=True)
    @api.model
    def _prepare_values_extra_move(self, op, product, remaining_qty):
        res = super(StockPicking, self)._prepare_values_extra_move(op, product, remaining_qty)
        for m in op.linked_move_operation_ids:
            if m.move_id.purchase_line_id and m.move_id.product_id == product:
                res['retour_id'] = m.move_id.purchase_line_id.id
                break
        return res
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    retour_id = fields.Many2one('gestiondefuts.retour',
        'Retour', ondelete='set null', index=True, readonly=True)