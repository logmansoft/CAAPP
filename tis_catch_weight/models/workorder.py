from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round

class MrpWorkorderCWUOM(models.Model):
    _inherit  = 'mrp.workorder'
    

    
    product_cw_uom = fields.Many2one(
        'uom.uom', 'CW-UOM',
        related='production_id.product_cw_uom', readonly=True,
        help='Technical: used in views only.')
    product_cw_uom_qty_produced = fields.Float(
        'CW-Qty Produced', default=0.0,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="The number of products already handled by this work order")
    product_cw_uom_qty_production = fields.Float('Original Production Quantity', readonly=True, related='production_id.product_cw_uom_qty')
    cw_qty_remaining = fields.Float('Quantity To Be Produced(CW)', compute='_compute_qty_remaining', digits=dp.get_precision('Product Unit of Measure'))# edit fuction to return cw qty remain
    production_availability_cw = fields.Selection(
        'Stock Availability', readonly=True,
        related='production_id.availability', store=True,
        help='Technical: used in views and domains only.')
    qty_producing_cw = fields.Float(
        'Currently CW Produced Quantity', default=1.0,
        digits=dp.get_precision('Product Unit of Measure'),
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    
   
    @api.multi
    def record_production(self):
        production = super(MrpWorkorderCWUOM, self).record_production()
        if production:
            self.qty_producing_cw = self.production_id.product_cw_uom_qty - self.product_cw_uom_qty_produced
            if self.qty_production == self.qty_produced:
                self.product_cw_uom_qty_produced = self.product_cw_uom_qty_production
                for move in self.move_raw_ids:
                    rounding = move.product_cw_uom.rounding
                    move.cw_qty_done += self.qty_producing_cw * move.cw_unit_factor
            elif self.qty_production > self.qty_produced:
                differ_amount = self.qty_production - self.qty_produced
                self.product_cw_uom_qty_produced = self.product_cw_uom_qty_production/differ_amount