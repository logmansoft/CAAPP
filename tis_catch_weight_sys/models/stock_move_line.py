# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _
    
class StockMoveLine(models.Model):    
    _inherit = 'stock.move.line'
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW Demand')
    cw_qty_done = fields.Float(string='CW Done')
    
    @api.onchange('product_id', 'product_uom_id', ' product_cw_uom', 'move_id.product_cw_uom')
    def onchange_product_id(self):
        res = super(StockMoveLine, self).onchange_product_id()
        if self.product_id:
            self.product_cw_uom = self.product_id.cw_uom_id.id
        else:
            self.product_cw_uom = self.move_id.product_cw_uom.id
        return res

#     @api.onchange('move_id')
#     def onchange_move_id(self):
#         move_lines = self.env['stock.move'].search([('id', '=', self.move_id.id)])
#         move_lines[0].