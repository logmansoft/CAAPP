# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

from odoo.addons import decimal_precision as dp

class CatchingRequest(models.Model):
    _name = 'catching.request'

    name = fields.Char('Refrence', default=lambda self: self.env['ir.sequence'].next_by_code('catching.request'))
    #Vehicle info
    driver_id = fields.Many2one(
        string='Driver',
        comodel_name='res.partner',
        ondelete='restrict',
    )
    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name='model.name',
        ondelete='restrict',
    )
    vehicle_no = fields.Char('Vehicle No')

    #Farm Info
    vendor_id = fields.Many2one('res.partner', string='Farm', domain=[('supplier', '=', True)])
    hanger_id = fields.Many2one('farm.hanger', string='Hanger', domain="[('partner_id', '=', vendor_id)]")
    hanger_no = fields.Char(string='Hanger No', related='hanger_id.code')
    
    #Material Info

    incoming_qty = fields.Integer('Incoming Quantity', default=9900)
    qty_uom = fields.Many2one(
        string='Qty UOM',
        comodel_name='uom.uom',
        ondelete='restrict', default= lambda self: self.product_id and self.product_id.product_uom_id.id or False
    )
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.template',
        ondelete='restrict', default = lambda self: self.env['product.template'].search([('option', '=', '1')]) and self.env['product.template'].search([('option', '=', '1')])[0] or False,
    )
    weight = fields.Float('Weight')
    uom = fields.Many2one(
        string='UOM',
        comodel_name='uom.uom',
        ondelete='restrict',
    )
    current_weight = fields.Float('Current Weight')
    current_uom = fields.Many2one(
        string='UOM',
        comodel_name='uom.uom',
        ondelete='restrict', default= lambda self: self.product_id and self.product_id.product_uom_id.id or False)
    #Other Info
    note = fields.Text('Note')
    leaving_time = fields.Float('Leaving Time')
    state = fields.Selection([('1', 'Draft'), ('2', 'Confirmed'),
                                ('3', 'Quality Done'), ('4', 'Mo Created')],
                                        string='State', 
                                        default='1'
                                        )
    

    date = fields.Date('Date', default=fields.Date.today())
    
    unit_price = fields.Float('Unit Price', digits=dp.get_precision('Product Price'))

    currency_id = fields.Many2one(
        'res.currency', 'Currency', compute='_compute_currency_id')
    qty_quality = fields.Float('Quantity After Quality')
    quality_uom = fields.Many2one(
        string='UOM',
        comodel_name='uom.uom',
        ondelete='restrict', default= lambda self: self.product_id and self.product_id.product_uom_id.id or False)
    
    purchase_order_id = fields.Many2one(
        string='Purchase Order',
        comodel_name='purchase.order',
        ondelete='restrict',
    )
    

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        copy=True,
    )

    production_id = fields.Many2one(
        string='MO',
        comodel_name='mrp.production',
        ondelete='restrict',
    )
    

    def send_to_manufacture(self):
        self.state = '2'

    def set_confirmed(self):

        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        for rec in self:
            po_vals = rec.create_vals(self.vendor_id)
            purchase_order = purchase_obj.create(po_vals)
            po_line_vals = rec._prepare_po_line(rec, purchase_order)

            purchase_line_obj.sudo().create(po_line_vals)
            if purchase_order:
                rec.purchase_order_id = purchase_order.id
        self.state = '2'

    @api.multi
    def show_mo(self):
        for rec in self:
            res = self.env.ref('mrp.mrp_production_action')
            res = res.read()[0]
            res['domain'] = str([('id', '=', rec.production_id.id)])
        return res

    @api.multi
    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref('purchase.purchase_form_action')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('id', '=', rec.purchase_order_id.id)])
        return purchase_action

    @api.multi
    def create_vals(self, partner):
        po_vals = {
            'partner_id': partner.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'date_order': fields.Date.today(),
            'company_id': self.env.user.company_id.id,
            'origin': self.name,
            'driver_name': self.driver_id.name,
            'state': 'purchase'
        }
        return po_vals
    
    def set_quality_done(self):
        for rec in self:
            print(rec.purchase_order_id, "====================")
            if not(rec.purchase_order_id.is_shipped):

                raise ValidationError(_('Please Be Sure that you have already recived The Products'))

        self.state = '3'


    @api.multi
    def _compute_currency_id(self):
        try:
            main_company = self.sudo().env.ref('base.main_company')
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
        for template in self:
           
            template.currency_id = main_company.sudo().currency_id.id

    @api.onchange('vehicle_no')
    def _onchange_vehicle_no(self):
        for rec in self:
            if rec.vehicle_no and self.env['fleet.vehicle'].search([('license_plate', '=', rec.vehicle_no)]):
                if self.env['fleet.vehicle'].search([('license_plate', '=', rec.vehicle_no)]).driver_id:
                    rec.driver_id = self.env['fleet.vehicle'].search([('license_plate', '=', rec.vehicle_no)]).driver_id






    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.qty_uom = self.env['product.template'].search([('id', '=', self.product_id.id)])[0].uom_id.id
            self.quality_uom = self.env['product.template'].search([('id', '=', self.product_id.id)])[0].uom_id.id
    
    @api.model
    def default_get(self, fields):
        res = super(CatchingRequest, self).default_get(fields)
        if res and 'product_id' in res and self.env['product.template'].search([('id', '=', res['product_id'])]):
            res['quality_uom'] = self.env['product.template'].search([('id', '=', res['product_id'])])[0].uom_id.id
            res['qty_uom'] = self.env['product.template'].search([('id', '=', res['product_id'])])[0].uom_id.id
            if self.env['uom.category'].search([('measure_type', '=', 'weight')]):
                categ_id = self.env['uom.category'].search([('measure_type', '=', 'weight')])
                if self.env['uom.uom'].search([('category_id', '=', categ_id.id)]):
                    res['uom'] = self.env['uom.uom'].search([('category_id', '=', categ_id.id)])[0].id
                    res['current_uom'] = self.env['uom.uom'].search([('category_id', '=', categ_id.id)])[0].id
        else:
            ValidationError(_('Please Be Sure that you have already setting up at least one product with For Catching option'))
        return res

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {}
        if self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])[0]:
            po_line_vals = {
                    'product_id': self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)])[0].id,
                    'name':line.product_id.name,
                    'product_qty': line.incoming_qty,
                    'product_uom': line.qty_uom.id,
                    'date_planned': fields.Date.today(),
                    'price_unit': line.unit_price,
                    'order_id': purchase_order.id,
                    'account_analytic_id': line.analytic_account_id.id,
                    #'custom_requisition_line_id': line.id
            }
        return po_line_vals



class res_partner(models.Model):
    _inherit = 'res.partner'

    is_farm = fields.Boolean('Is Farm')
    is_person = fields.Boolean('Is Person')
    hanger_ids = fields.One2many('farm.hanger', 'partner_id', string="Hangers")


    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Company'), ('farm', 'Farm')],
        compute='_compute_company_type', inverse='_write_company_type')

    @api.depends('is_company', 'is_farm', 'is_person')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company:
                partner.company_type = 'company'
            elif partner.is_farm:
                #partner.is_farm = True
                partner.company_type = 'farm'
            else:
                #partner.is_person = True
                partner.company_type = 'person'

   
    @api.onchange('company_type')
    def onchange_company_type(self):
        self.is_company = (self.company_type == 'company')
        self.is_person = (self.company_type=='person')
        self.is_farm = (self.company_type=='farm')

    

    def _write_company_type(self):
       # for partner in self:
        print (self.is_company, self.is_person, self.is_farm, "======================")
        self.is_company = (self.company_type == 'company')
        self.is_person = (self.company_type=='person')
        self.is_farm = (self.company_type=='farm')
class FarmHanger(models.Model):
    _name = 'farm.hanger'

    partner_id = fields.Many2one('res.partner', 'Farm')
    name = fields.Char('Name')
    code = fields.Char('Code')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
