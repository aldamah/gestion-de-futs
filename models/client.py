from odoo import fields, models, api
from odoo import fields, models, api
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP

class Client(models.Model):
    _inherit = 'res.partner'
    solde = fields.Integer(default=0,compute='_get_solde')
    entree = fields.One2many('purchase.order', 'partner_id', 'Retour')

    
    @api.depends('sale_order_ids','entree')
    def _get_solde(self):
        
        for client in self:
            solde_sale = 0
            solde_retour = 0
            solde_final = 0
            for order in client.sale_order_ids:
                for line in order.order_line:
                    if not line.avec_futs:
                        solde_sale += line.product_uom_qty
                    else:
                        continue
           
            for order in client.entree:
                if order.is_retour:
                    for line in order.order_line:
                        solde_retour += line.product_qty
            solde_final = solde_sale - solde_retour
            client.update({
            'solde': solde_final,
            })