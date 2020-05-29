# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _

class BomCWUOM(models.Model):
    _inherit  = 'mrp.bom'
    

    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    
    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        res  = super(BomCWUOM,self).onchange_product_tmpl_id()
        self.product_cw_uom = self.product_id.cw_uom_id
        return res
    
class BomLineCWUOM(models.Model):
    _inherit  = 'mrp.bom.line'
    

    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res  = super(BomLineCWUOM,self).onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id
        return res
    
    