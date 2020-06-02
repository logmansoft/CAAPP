# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	@api.one
	@api.depends('invoice_line_ids.price_unit', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'global_discount_type', 'global_order_discount')
	def _compute_amount(self):
		super(AccountInvoice, self)._compute_amount()
		totalAmount, totalDiscount, lineTotalDiscount = 0, 0, 0
		amountUntaxed = sum((line.price_unit * line.quantity) for line in self.invoice_line_ids)
		amountTax = sum(line.amount for line in self.tax_line_ids)
		if self.type == 'in_invoice':
			lineTotalDiscount = sum(((line.quantity*line.price_unit) * (line.p_discount/100)) if line.discount_type == 'percent' else line.p_discount for line in self.invoice_line_ids)
		elif self.type == 'out_invoice':
			lineTotalDiscount = sum(((line.quantity*line.price_unit) * (line.s_discount/100)) if line.discount_type == 'percent' else line.s_discount for line in self.invoice_line_ids)
		totalDiscount = lineTotalDiscount
		totalAmount = amountUntaxed + amountTax
		IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
		orderObj = False
		discTax = 'untax'
		moduleObj = self.env['ir.module.module'].sudo().search(
			[("name","=","discount_sale_order"),("state","=","installed")])
		if self.type and self.type == 'in_invoice':
			orderObj = self.env['purchase.order'].sudo().search([('name', '=', self.origin)])
			discTax = IrConfigPrmtrSudo.get_param('purchase.global_discount_tax_po')
		if self.type and self.type == 'out_invoice' and moduleObj:
			orderObj = self.env['sale.order'].sudo().search([('name', '=', self.origin)])
			discTax = IrConfigPrmtrSudo.get_param('sale.global_discount_tax')
		totalAmount = totalAmount - lineTotalDiscount
		self.total_discount = totalDiscount
		self.amount_untaxed = amountUntaxed
		self.amount_tax = amountTax
		self.amount_total = totalAmount
		amount_total_company_signed = self.amount_total
		amount_untaxed_signed = self.amount_untaxed
		if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
			currency_id = self.currency_id.with_context(date=self.date_invoice)
			amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
			amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
		sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
		self.amount_total_company_signed = amount_total_company_signed * sign
		self.amount_total_signed = self.amount_total * sign
		self.amount_untaxed_signed = amount_untaxed_signed * sign

	@api.multi
	def get_taxes_values(self):
		tax_grouped = {}
		price_unit = 0
		for line in self.invoice_line_ids:
			quantity = 1.0
			if line.discount_type == 'fixed':
				if self.type == 'in_invoice':
					price_unit = line.price_unit * line.quantity - (line.p_discount or 0.0)
				elif self.type == 'out_invoice':
					price_unit = line.price_unit * line.quantity - (line.s_discount or 0.0)
			else:
				quantity = line.quantity
				if self.type == 'in_invoice':
					price_unit = line.price_unit * (1 - (line.p_discount or 0.0) / 100.0)
				elif self.type == 'out_invoice':
					price_unit = line.price_unit * (1 - (line.s_discount or 0.0) / 100.0)
			taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, quantity, line.product_id, self.partner_id)['taxes']
			for tax in taxes:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
				if key not in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']
		return tax_grouped

	total_discount = fields.Monetary(string='Total Discount', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
	total_global_discount = fields.Monetary(string='Total Global Discount', store=True, readonly=True, compute='_compute_amount')
	global_discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type")
	global_order_discount = fields.Float(string='Global Discount', store=True, track_visibility='always', digits=dp.get_precision('Discount'))

	def _prepare_invoice_line_from_so_line(self, line):
		res = super(AccountInvoice, self)._prepare_invoice_line_from_so_line(line)
		res.update(
			s_discount=line.s_discount,
			discount_type=line.discount_type
			)
		return res

	@api.onchange('invoice_line_ids')
	def _onchange_origin(self):
		super(AccountInvoice, self)._onchange_origin()
		purchase_ids = self.invoice_line_ids.mapped('purchase_id')
		#sale_ids = self.invoice_line_ids.mapped('sale_id')
		if purchase_ids:
			self.global_discount_type = purchase_ids[0].global_discount_type
			self.global_order_discount = purchase_ids[0].global_order_discount
		#if sale_ids:
		#	self.global_discount_type = sale_ids[0].global_discount_type
		#	self.global_order_discount = sale_ids[0].global_order_discount

	@api.multi
	def finalize_invoice_move_lines(self, move_lines):
		inv_obj = self[0]
		if inv_obj.total_discount > 0.0 and self.type not in ('out_invoice', 'in_refund'):
			IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
			global_account = IrConfigPrmtr.get_param('purchase.discount_account_po')
			if not global_account:
				raise UserError(_("Global Discount!\nPlease first set account for global discount in purchase setting"))
			if global_account and int(global_account):
				global_account = self.env['account.account'].browse(int(global_account))
				for x, y, line in move_lines:
					if line.get('credit') and not line.get('product_id'):
						line['credit'] -= inv_obj.total_discount
						break
				amount_currency = 0.0
				currency = inv_obj.currency_id
				company_currency = inv_obj.company_id.currency_id
				diff_currency = currency != company_currency
				if diff_currency:
					date = self._get_currency_rate_date() or fields.Date.context_today(self)
					amount_currency = currency._convert(
						inv_obj.total_global_discount, company_currency, inv_obj.company_id, date)
				else:
					currency = False
				global_line =  {
					'type': 'dest',
					'name': global_account.name,
					'price': -(inv_obj.total_discount),
					'account_id': global_account.id,
					'date_maturity': inv_obj.date_due,
					'amount_currency': diff_currency and amount_currency,
					'currency_id': currency and currency.id,
					'invoice_id': inv_obj.id
				}
				part = self.env['res.partner']._find_accounting_partner(inv_obj.partner_id)
				global_line = [(0, 0, self.line_get_convert(global_line, part.id))]
				move_lines += global_line
		if inv_obj.total_discount > 0.0 and self.type not in ('in_invoice', 'out_refund'):
			IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
			global_account = IrConfigPrmtr.get_param('sale.discount_account_so')
			if not global_account:
				raise UserError(_("Global Discount!\nPlease first set account for global discount in sale setting"))
			if global_account and int(global_account):
				global_account = self.env['account.account'].browse(int(global_account))
				for x, y, line in move_lines:
					if line.get('debit') and not line.get('product_id'):
						line['debit'] -= inv_obj.total_discount
						break
				amount_currency = 0.0
				currency = inv_obj.currency_id
				company_currency = inv_obj.company_id.currency_id
				diff_currency = currency != company_currency
				if diff_currency:
					date = self._get_currency_rate_date() or fields.Date.context_today(self)
					amount_currency = currency._convert(
						inv_obj.total_global_discount, company_currency, inv_obj.company_id, date)
				else:
					currency = False
				global_line =  {
					'type': 'dest',
					'name': global_account.name,
					'price': (inv_obj.total_discount),
					'account_id': global_account.id,
					'date_maturity': inv_obj.date_due,
					'amount_currency': diff_currency and amount_currency,
					'currency_id': currency and currency.id,
					'invoice_id': inv_obj.id
				}
				part = self.env['res.partner']._find_accounting_partner(inv_obj.partner_id)
				global_line = [(0, 0, self.line_get_convert(global_line, part.id))]
				move_lines += global_line
		return move_lines


class AccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"

	s_discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'), default=0.0)
	discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type")
		
		
		
class AccountInvoiceRefund(models.TransientModel):
    """Credit Notes"""

    _inherit = "account.invoice.refund"

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'cancel']:
                    raise UserError(_('Cannot create credit note for the draft/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_('Cannot create a credit note for the invoice which is already reconciled, invoice should be unreconciled first, then only you can add credit note for this invoice.'))

                date = form.date or False
                description = form.description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)
                refund.write({'total_discount':inv.total_discount})
                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    aasasas
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False
                        inv_refund = inv_obj.create(invoice)
                        body = _('Correction of <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a><br>Reason: %s') % (inv.id, inv.number, description)
                        inv_refund.message_post(body=body)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = inv.type == 'out_invoice' and 'action_invoice_out_refund' or \
                         inv.type == 'out_refund' and 'action_invoice_tree1' or \
                         inv.type == 'in_invoice' and 'action_invoice_in_refund' or \
                         inv.type == 'in_refund' and 'action_invoice_tree2'
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            if mode == 'modify':
                # When refund method is `modify` then it will directly open the new draft bill/invoice in form view
                if inv_refund.type == 'in_invoice':
                    view_ref = self.env.ref('account.invoice_supplier_form')
                else:
                    view_ref = self.env.ref('account.invoice_form')
                
                result['views'] = [(view_ref.id, 'form')]
                result['res_id'] = inv_refund.id
            else:
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', created_inv))
                result['domain'] = invoice_domain
            return result
        return True


