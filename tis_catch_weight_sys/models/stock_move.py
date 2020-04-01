# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockMoveCWUOM(models.Model):
    _inherit = 'stock.move'
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW Demand')
    cw_qty_done = fields.Float(string='CW Done', compute='_cw_quantity_done_compute', inverse='_quantity_done_set')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMoveCWUOM, self).onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id.id
        return res
    
    @api.multi
    @api.depends('move_line_ids.product_cw_uom_qty', 'move_line_ids.product_cw_uom')
    def _cw_quantity_done_compute(self):

        for move in self:
            for move_line in move.move_line_ids:
                move.cw_qty_done += move_line.product_cw_uom._compute_quantity(move_line.cw_qty_done, move.product_cw_uom)
            
    def _quantity_done_set(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMoveCWUOM, self)._quantity_done_set()

        quantity_done = self[0].quantity_done
        cw_quantity_done = self[0].cw_qty_done
        for move in self:
            move_lines = move._get_move_lines()

            if not move_lines:
                if quantity_done and cw_quantity_done:
                    move_line = self.env['stock.move.line'].create(
                        dict(move._prepare_move_line_vals(), qty_done=quantity_done, cw_qty_done=cw_quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
                elif quantity_done and not cw_quantity_done:
                    move_line = self.env['stock.move.line'].create(
                        dict(move._prepare_move_line_vals(), qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
                elif cw_quantity_done:
                    move_line = self.env['stock.move.line'].create(
                        dict(move._prepare_move_line_vals(), cw_qty_done=cw_quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].qty_done = quantity_done
                move_lines[0].cw_qty_done = cw_quantity_done
            else:
                raise UserError("Cannot set the done quantity from this stock move, work directly with the move lines.")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super(StockMoveCWUOM, self)._prepare_move_line_vals()
        if self.product_id.tracking == 'serial':
            serial_qty = self.product_cw_uom_qty/self.product_uom_qty
            res.update({'product_cw_uom_qty': serial_qty,
                        'product_cw_uom': self.product_cw_uom and self.product_cw_uom.id})
        else:
            res.update({'product_cw_uom_qty': self.product_cw_uom_qty,
                        'product_cw_uom': self.product_cw_uom and self.product_cw_uom.id})
        if quantity:
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            res = dict(res, product_uom_qty=uom_quantity)
        if reserved_quant:
            res = dict(
                res,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        return res


class ProcurementRule(models.Model):
    _inherit = 'stock.rule'
 
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('product_cw_uom', False):
            result['product_cw_uom'] = values['product_cw_uom']
        if values.get('product_cw_uom_qty', False):
            result['product_cw_uom_qty'] = values['product_cw_uom_qty']
        return result
    