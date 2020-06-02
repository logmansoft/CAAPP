# -*- coding: utf-8 -*-
##########################################################################
#
#
#
#
#
##########################################################################

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
	_inherit = "sale.order"
	

	@api.model
	def _wk_discount_so_settings(self):
		configModel = self.env['res.config.settings']
		vals = {
			'group_discount_sale_line' : 1,
			'group_order_global_discount_so' : True,
			'global_discount_tax_so' : 'untax',
		}
		defaultSetObj = configModel.create(vals)
		defaultSetObj.execute()
		return True

	@api.depends('order_line.price_total', 'global_order_discount', 'global_discount_type')
	def _amount_all(self):
		super(SaleOrder, self)._amount_all()
		for order in self:
			amount_untaxed = amount_tax = 0.0
			total_discount = 0.0
			for line in order.order_line:
				amount_untaxed += line.line_sub_total
				if line.discount_type == 'fixed':
					total_discount += line.s_discount
				else:
					total_discount += line.product_uom_qty*(line.price_unit - line.price_reduce)
				if order.company_id.tax_calculation_rounding_method == 'round_globally':
					quantity = 1.0
					if line.discount_type == 'fixed':
						price = line.price_unit * line.product_uom_qty - (line.s_discount or 0.0)
					else:
						price = line.price_unit * (1 - (line.s_discount or 0.0) / 100.0)
						quantity = line.product_uom_qty
					taxes = line.tax_id.compute_all(
						price, line.order_id.currency_id, quantity, product=line.product_id, partner=line.order_id.partner_id)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
			discTax = IrConfigPrmtrSudo.get_param('sale.global_discount_tax_so')
			if discTax == 'untax':
				total_amount = amount_untaxed - total_discount
			else:
				total_amount = amount_untaxed - total_discount + amount_tax
			if order.global_discount_type == 'percent':
				beforeGlobal = total_amount
				total_amount = total_amount * (1 - (order.global_order_discount or 0.0)/100)
				total_discount += beforeGlobal - total_amount
			else:
				total_amount = total_amount - (order.global_order_discount or 0.0)
				total_discount += order.global_order_discount
			if discTax == 'untax':
				total_amount = total_amount - total_discount + amount_tax
			order.update({
				'amount_untaxed': order.currency_id.round(amount_untaxed),
				'amount_tax': order.currency_id.round(amount_tax),
				'amount_total': total_amount,
				'total_discount': total_discount,
			})

	total_discount = fields.Monetary(string='Total Discount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	global_discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type",)
	global_order_discount = fields.Float(string='Global Discount', store=True,  track_visibility='always', digits=dp.get_precision('Discount'))

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	@api.depends('price_unit', 'discount_type', 'discount', 'tax_id', 'product_uom_qty')
	def _get_price_reduce(self):
		for line in self:
			if line.discount_type == 'fixed' and line.product_uom_qty:
				price_reduce = line.price_unit * line.product_uom_qty - line.discount
				line.price_reduce = price_reduce/line.product_uom_qty
			else:
				line.price_reduce = line.price_unit * (1.0 - line.s_discount / 100.0)
			price = line.price_unit
			quantity = line.product_uom_qty
			taxes = line.tax_id.compute_all(
				price, line.order_id.currency_id, quantity, product=line.product_id, partner=line.order_id.partner_id)
			line.line_sub_total = taxes['total_excluded']

	price_reduce = fields.Monetary(compute='_get_price_reduce', string='Price Reduce', readonly=True, store=True)
	line_sub_total = fields.Monetary(compute='_get_price_reduce', string='Line Subtotal', readonly=True, store=True, digits=dp.get_precision('Discount'))
	s_discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'), default=0.0)
	discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type",)

	@api.depends('product_uom_qty', 'price_unit', 'tax_id', 'discount', 'discount_type')
	def _compute_amount(self):
		super(SaleOrderLine, self)._compute_amount()
		for line in self:
			quantity = 1.0
			if line.discount_type == 'fixed':
				price = line.price_unit * line.product_uom_qty - (line.s_discount or 0.0)
			else:
				price = line.price_unit * (1 - (line.s_discount or 0.0) / 100.0)
				quantity = line.product_uom_qty
			taxes = line.tax_id.compute_all(
				price, line.order_id.currency_id, quantity, product=line.product_id, partner=line.order_id.partner_id)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
			
			
	@api.multi
	def _prepare_invoice_line(self, qty):
		"""
		Prepare the dict of values to create the new invoice line for a sales order line.
		:param qty: float quantity to invoice
		"""
		self.ensure_one()
		res = {}
		account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

		if not account and self.product_id:
			raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
			(self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

		fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
		if fpos and account:
			account = fpos.map_account(account)

		res = {
		    'name': self.name,
		    'sequence': self.sequence,
		    'origin': self.order_id.name,
		    'account_id': account.id,
		    'price_unit': self.price_unit,
		    'quantity': qty,
		    'discount_type': self.discount_type,
		    's_discount': self.s_discount,
		    'uom_id': self.product_uom.id,
		    'product_id': self.product_id.id or False,
		    'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
		    'account_analytic_id': self.order_id.analytic_account_id.id,
		    'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
		    'display_type': self.display_type,
		}
		return res
