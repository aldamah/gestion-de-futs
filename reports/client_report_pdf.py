from odoo import fields, models, api

class client_report_pdf(models.Model):
    _name = 'res.partner.report'
    _sql = """
                CREATE OR REPLACE VIEW client_report_pdf as 
                SELECT * from sale_order so, purchase_order po, gestiondefuts_retour re
                WHERE so.partner_id = partner_id OR po.partner_id = partner_id OR re.partner_id = partner_id
                ORDER BY date_order ASC
    
    """
    name = fields.Char(index=True)
    solde = fields.Integer(default=0,compute='_get_solde')
    sale_order_ids = fields.One2many('sale.order', 'partner_id', 'Sale Order')
    purchase_order_ids = fields.One2many('purchase.order', 'partner_id', 'Purchase Order')
    retour = fields.One2many('gestiondefuts.retour', 'partner_id', 'Retour')
    @api.depends('sale_order_ids','retour')
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
           
            for pOrder in client.retour:
                solde_retour += pOrder.product_qty
            solde_final = solde_sale - solde_retour 
            client.update({
            'solde': solde_final,
            })
        
    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        report = report_obj.get_report_from_name(
            cr, uid, 'gestion_de_futs.client_report_pdf'
            )
        
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': self.pool[report.model].browse(cr, uid,ids, context=context)
            }
        
        return report_obj.render(cr, uid, ids, 'gestion_de_futs.client_report_pdf')