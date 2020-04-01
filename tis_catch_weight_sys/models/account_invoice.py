# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _

class AccountInvoiceLineCWUOM(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date', 'product_cw_uom_qty')
    def _compute_price(self):
        super(AccountInvoiceLineCWUOM, self)._compute_price()
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_id.type in ['in_invoice', 'in_refund']:
            if self.product_id.purchase_price_base == 'cwuom':
                quantity = self.product_cw_uom_qty
            else:
                quantity = self.quantity
        else:
            if self.product_id.sale_price_base == 'cwuom':
                quantity = self.product_cw_uom_qty
            else:
                quantity = self.quantity
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    
    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        res  = super(AccountInvoiceLineCWUOM,self)._onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id

class AccountInvoiceCWUOM(models.Model):
    _inherit = 'account.invoice'
        
    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoiceCWUOM, self). _prepare_invoice_line_from_po_line(line)
        res.update({
                    'product_cw_uom': line.product_cw_uom.id,
                    })
        return res

    @api.multi
    def get_taxes_values(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(AccountInvoiceCWUOM, self).get_taxes_values()
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if line.invoice_id.type in ['in_invoice', 'in_refund'] and line.product_id.purchase_price_base == 'cwuom':
                quantity = line.product_cw_uom_qty
            elif line.invoice_id.type in ['out_invoice', 'out_refund'] and line.product_id.sale_price_base == 'cwuom':
                quantity = line.product_cw_uom_qty
            else:
                quantity = line.quantity
            if not line.account_id:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, quantity, line.product_id,
                                                          self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped
