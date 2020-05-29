# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MrpUnbuildCW(models.Model):
    _inherit = 'mrp.unbuild'
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM', states={'done': [('readonly', True)]})
    unbuild_cw_qty = fields.Float(string='CW-Qty', default=1.0, states={'done': [('readonly', True)]})
    
    

    def _generate_consume_moves(self):
        consumed_moves = super(MrpUnbuildCW, self)._generate_consume_moves()
        for consumed_move in consumed_moves:
            consumed_move.product_cw_uom_qty = self.unbuild_cw_qty
            consumed_move.product_cw_uom = self.product_cw_uom
        return consumed_moves

    @api.onchange('mo_id')
    def onchange_mo_id(self):
        if self.mo_id:
            super(MrpUnbuildCW, self).onchange_mo_id()
            self.unbuild_cw_qty = self.mo_id.product_cw_uom_qty
            self.product_cw_uom = self.mo_id.product_cw_uom

    

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            super(MrpUnbuildCW, self).onchange_product_id()
            self.product_cw_uom = self.product_id.cw_uom_id.id
    
    def _generate_produce_moves(self):
        produced_moves = super(MrpUnbuildCW, self)._generate_produce_moves()
        for move in produced_moves:
            move.product_cw_uom_qty = self.bom_id.bom_line_ids.filtered(lambda x: x.product_id == move.product_id).product_cw_uom_qty
            move.product_cw_uom = self.bom_id.bom_line_ids.filtered(lambda x: x.product_id == move.product_id).product_cw_uom.id
        return produced_moves

