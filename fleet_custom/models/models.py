from odoo import api, fields, models, _
from odoo.exceptions import Warning,ValidationError

class FleetService(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    line_id = fields.One2many('fleet.vehicle.line','service_id')

    def stock_request(self):
        count = 0
        for line in self.line_id:
            if line.flag == 0:
                count = count + 1
        if count == 0:
            raise ValidationError(_("There is no selected Spare parts"))
        for line in self.line_id:
            if line.product_uom_qty <= 0:
                raise ValidationError(_("Spare part %s Quantity contain unaccepted values" % line.product_id.name))
        stock_req = self.env['stock.picking']
        request_ids = self.env['stock.move']
        partner_id = self.env['res.users'].search([('id','=',self._uid)]).partner_id
        stock_id = stock_req.create({
            'partner_id': partner_id.id,
            'picking_type_id':2,
            'origin': self.vehicle_id.name,
            'note': 'Fleet Service',
            'location_id':1,
            'location_dest_id':1,
        })
        for line in self.line_id:
            request_line = request_ids.create({
                'name': 'Maintenance Project',
                'picking_id': stock_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.product_uom_qty,
                'location_id': 1,
                'location_dest_id': 1,
            })
            line.write({'flag': 1})
        self.write({'state':'waiting_stock'})

class MaintenanceProjectLine(models.Model):
    _name = 'fleet.vehicle.line'

    service_id = fields.Many2one('fleet.vehicle.log.services',string="Project")
    product_id = fields.Many2one('product.product',required=True,string="product",readonly=False)
    product_uom_qty = fields.Float(string="Quantity",required=True,readonly=False)
    flag = fields.Boolean(string="Sent",readonly=True)
