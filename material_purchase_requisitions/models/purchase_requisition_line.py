# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    
    requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions', 
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
#     layout_category_id = fields.Many2one(
#         'sale.layout_category',
#         string='Section',
#     )
    description = fields.Char(
        string='Description',
        required=True,
    )
    qty = fields.Float(
        string='Quantity',
        default=1,
        required=True,
    )
    uom = fields.Many2one(
        'uom.uom',#product.uom in odoo11
        string='Unit of Measure',
        required=True,
    )
    partner_id = fields.Many2many(
        'res.partner',
        string='Vendors',
    )
    requisition_type = fields.Selection(
        selection=[
                    ('internal','Internal Picking'),
                    ('purchase','Purchase Order'),
        ],
        string='Requisition Action',
        default='purchase',
        required=True,
    )
    available_qty = fields.Float('On Hand Qty')
    direct_purchase = fields.Boolean('Direct Purchase')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.uom = rec.product_id.uom_id.id

    @api.model
    def create(self, vals):
        line_id = super(MaterialPurchaseRequisitionLine, self).create(vals)
        if 'requisition_type' in vals and vals['requisition_type']=='purchase':
            line_id.requisition_id.required_purchase_order = True
        return line_id
    
    @api.multi
    def write(self, vals):
        line_id = super(MaterialPurchaseRequisitionLine, self).write(vals)
        flag = False
        for rec in self.search([('requisition_id', '=', self.requisition_id.id)]):
            if rec.requisition_type == 'purchase':
                flag = True
        self.requisition_id.required_purchase_order = flag
        return line_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
