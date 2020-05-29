# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class ProductionTransformer(models.TransientModel):
    _name = 'production.transformer.wizard'

   
   
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.template',
        ondelete='restrict', default= lambda self: self.env['product.template'].search([('option', '=', '2')]) and  self.env['product.template'].search([('option', '=', '2')])[0] or False,
    )
    
  
    

    qty_quality = fields.Float('Quantity After Quality', default= lambda self:self._context.get('qty_quality', False))
    quality_uom = fields.Many2one(
        string='UOM',
        comodel_name='uom.uom',
        ondelete='restrict',)
    bom_id = fields.Many2one('mrp.bom', string='Bom')
    
    
    def create_mo(self):
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])[0]
        request = self.env['catching.request'].search([('id', '=', self._context.get('active_id', False))])
        if request:
            self.env['mrp.production'].create({'product_id': product.id,'product_uom_id': self.bom_id.product_uom_id.id,
            'bom_id': self.bom_id.id, 'product_qty': self.qty_quality, 'origin': request.name})
            request.state = '4'
        #self.state = '2'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_id.id)])[0]
            self.quality_uom = self.env['product.template'].search([('id', '=', self.product_id.id)])[0].uom_id.id
    
    @api.model
    def default_get(self, fields):
        res = super(ProductionTransformer, self).default_get(fields)
        if res and 'product_id' in res:
            res['quality_uom'] = self.env['product.template'].search([('id', '=', res['product_id'])])[0].uom_id.id
            if not 'bom_id' in res:
                res.update({'bom_id':[]})


            if self.env['mrp.bom'].search([('product_tmpl_id', '=', res['product_id'])]):
                res['bom_id'] = self.env['mrp.bom'].search([('product_tmpl_id', '=', res['product_id'])])[0].id
            elif not (self.env['mrp.bom'].search([('product_tmpl_id', '=', res['product_id'])])):

                raise ValidationError(_('Sorry, it seems that the product you are going to manufacture has no Bom, search for (For First Mo) product and set the Bom'))
        else:
            raise ValidationError(_('Please Be Sure that you have already setting up at least one product with For First MO option'))
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
