# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockScrap(models.Model):
    _inherit = 'stock.scrap'
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM', states={'done': [('readonly', True)]})
    scrap_cw_qty = fields.Float(string='CW-Qty', default=1.0, states={'done': [('readonly', True)]})
    
    def _prepare_move_values(self):
        res = super(StockScrap, self)._prepare_move_values()
        res.update({
            'product_cw_uom': self.product_cw_uom.id,
            'product_cw_qty_done': self.scrap_cw_qty,
            'move_line_ids': [(0, 0, {
                                    'product_cw_uom': self.product_cw_uom.id,
                                    'cw_qty_done': self.scrap_cw_qty,
                                    'product_id': self.product_id.id,
                                    'product_uom_id': self.product_uom_id.id, 
                                    'qty_done': self.scrap_qty,
                                    'location_id': self.location_id.id, 
                                    'location_dest_id': self.scrap_location_id.id,
                                    'package_id': self.package_id.id, 
                                    'owner_id': self.owner_id.id,
                                    'lot_id': self.lot_id.id,  })],
            })
        return res
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockScrap, self).onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id.id
        return res