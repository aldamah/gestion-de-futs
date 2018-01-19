from odoo import fields, models, api

class Vehicule(models.Model):
    _inherit='fleet.vehicle'
    sale_order_id = fields.Many2many('sale.order')
    purchase_order_id = fields.Many2many('purchase.order')
    