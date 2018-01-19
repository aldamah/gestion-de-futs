from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp


class Retour(models.Model):
    _name = 'gestiondefuts.retour'
    
    product_qty = fields.Float(string='Quantity', required=True)
    date_planned = fields.Datetime(string='Scheduled Date', required=True, index=True)
    date_order = fields.Datetime(string='Order Date', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True, track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True)
    picking_count = fields.Integer(compute='_compute_picking', string='Receptions', default=0)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Receptions', copy=False)
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', default="1",required=True,
        help="This will determine picking type of incoming shipment")
    move_ids = fields.One2many('stock.move', 'retour_id', string='Retour', readonly=True, ondelete='set null', copy=False)
    procurement_ids = fields.One2many('procurement.order', 'retour_id', string='Procurements')
   

    @api.depends('move_ids')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
            moves = order.move_ids | order.move_ids.mapped('returned_move_ids')
            moves = moves.filtered(lambda r: r.state != 'cancel')
            pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)
            
            
    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            qty = 0.0
            price_unit = line._get_stock_move_price_unit()
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id':line.order_id.picking_type_id.warehouse_id.id,
            }
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty - qty
            for procurement in line.procurement_ids:
                # If the procurement has some moves already, we should deduct their quantity
                sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
                existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves, procurement.product_uom)
                procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, line.product_uom) - existing_proc_qty
                if float_compare(procurement_qty, 0.0, precision_rounding=procurement.product_uom.rounding) > 0 and float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                    tmp = template.copy()
                    tmp.update({
                        'product_uom_qty': min(procurement_qty, diff_quantity),
                        'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
                        'procurement_id': procurement.id,
                        'propagate': procurement.rule_id.propagate,
                    })
                    done += moves.create(tmp)
                    diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done        
    
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    retour_id = fields.Many2one('gestiondefuts.retour', string='Retour')