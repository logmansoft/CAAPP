# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _

class SaleOrderLineCWUOM(models.Model):
    _inherit  = 'sale.order.line'
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'product_cw_uom_qty')
    def _compute_amount(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrderLineCWUOM, self)._compute_amount()
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.product_id.sale_price_base == 'cwuom':
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_cw_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            else:
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
             
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res  = super(SaleOrderLineCWUOM,self).product_id_change()
        self.product_cw_uom = self.product_id.cw_uom_id
        return res
    
    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLineCWUOM, self)._prepare_invoice_line(qty)
        res.update({
            'product_cw_uom': self.product_cw_uom.id,
            'product_cw_uom_qty': self.product_cw_uom_qty,
        })
        return res
    
    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLineCWUOM, self)._prepare_procurement_values(group_id)
        res.update({
                'product_cw_uom': self.product_cw_uom.id,
                'product_cw_uom_qty': self.product_cw_uom_qty,
        })
        return res
        