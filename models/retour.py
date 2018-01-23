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
    
    name = fields.Char('Retour Reference', required=True, index=True, copy=False, default='Nouveau')
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
    qty_received = fields.Float(compute='_compute_qty_received', string="Received Qty", store=True)
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    READONLY_STATES = {
        'retour': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    product_uom = fields.Many2one('product.uom', string='Product Unit of Measure', required=True, default=1)
    dest_address_id = fields.Many2one('res.partner', string='Drop Ship Address', states=READONLY_STATES,\
        help="Put an address if you want to deliver directly from the vendor to the customer. "\
             "Otherwise, keep empty to deliver to your own company.")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES, default=lambda self: self.env.user.company_id.id)
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    @api.depends('move_ids.state')
    def _compute_qty_received(self):
        for line in self:
            if line.state not in ['purchase', 'done']:
                line.qty_received = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.qty_received = line.product_qty
                continue
            total = 0.0
            for move in line.move_ids:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total += move.product_uom_qty
            line.qty_received = total

    
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
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'date': line.date_order,
                'date_expected': line.date_planned,
                'location_id': line.partner_id.property_stock_supplier.id,
                'location_dest_id': line._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.dest_address_id.id,
                'move_dest_id': False,
                'state': 'done',
                'purchase_line_id': line.id,
                'company_id': line.company_id.id,
                'picking_type_id': line.picking_type_id.id,
                'group_id': line.group_id.id,
                'procurement_id': False,
                'origin': line.name,
                'route_ids': line.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id':line.picking_type_id.warehouse_id.id,
            }
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty - qty
            for procurement in line.procurement_ids:
                # If the procurement has some moves already, we should deduct their quantity
                sum_existing_moves = sum(x.product_qty for x in procurement.move_ids)
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
    
    @api.multi
    def _get_destination_location(self):
        self.ensure_one()
        if self.dest_address_id:
            return self.dest_address_id.property_stock_customer.id
        return self.picking_type_id.default_location_dest_id.id
    
    @api.model
    def _prepare_picking(self):
        self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }
    
    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.mapped('product_id.type')]):
                pickings = order.picking_ids
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order._create_stock_moves(picking)
                moves = moves.action_confirm()
                moves.force_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True 
    
    @api.model
    def create(self, values):
        line = super(Retour, self).create(values)
        line._create_picking()
        return line
    
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    retour_id = fields.Many2one('gestiondefuts.retour', string='Retour')