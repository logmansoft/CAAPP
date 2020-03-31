# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _

class PurchaseOrderLineCWUOM(models.Model):
    _inherit  = 'purchase.order.line'
    
    @api.depends('product_qty', 'price_unit', 'taxes_id', 'product_cw_uom_qty')
    def _compute_amount(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(PurchaseOrderLineCWUOM, self)._compute_amount()
        for line in self:
            if line.product_id.purchase_price_base == 'cwuom':
                taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_cw_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            else:
                taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res  = super(PurchaseOrderLineCWUOM,self).onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id
        return res
    
    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLineCWUOM, self)._prepare_stock_moves(picking)
        res[0]['product_cw_uom'] = self.product_cw_uom.id
        res[0]['product_cw_uom_qty'] = self.product_cw_uom_qty
                  
        return res
     