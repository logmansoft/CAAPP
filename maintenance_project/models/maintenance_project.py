from odoo import api, fields, models, _
from odoo.exceptions import Warning,ValidationError

class MaintenanceProject(models.Model):
    _inherit = 'maintenance.request'

    def _get_total_cost(self):
        self.cost = self.material_cost + self.manpower_cost + self.other_cost
        return self.cost

    state = fields.Selection([('new', 'New'), ('approve', 'Maintenance Manager Approve'), ('approved', 'Approved'), ('in_progress', 'In Progress'), ('waiting_stock', 'Spare parts requested'),
                              ('done', 'Done'), ('canceled', 'Canceled')],string="State",default='new')
    type = fields.Selection([('regular', 'Regular'), ('project', 'Project')])
    material_cost = fields.Float(string='Material Cost')
    manpower_cost = fields.Float(string='Man-Power Cost')
    other_cost = fields.Float(string='Other Cost')
    cost = fields.Float(string='Total Cost',compute='_get_total_cost')
    line_id = fields.One2many('maintenance.project.line','project_id')
    parent_id = fields.Many2one('maintenance.request',string="Parent Project")

    def submit(self):
        self.write({'state': 'approve'})
    def approve(self):
        self.write({'state': 'approved'})
    def progress(self):
        self.write({'state': 'in_progress'})
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
            'origin': self.name,
            'note': 'Maintenance Project',
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
    def received(self):
        self.write({'state': 'in_progress'})
    def done(self):
        self.write({'state': 'done'})
    def cancel(self):

        self.write({'state': 'canceled'})

class MaintenanceProjectLine(models.Model):
    _name = 'maintenance.project.line'

    project_id = fields.Many2one('maintenance.request',string="Project")
    product_id = fields.Many2one('product.product',required=True,string="product",readonly=False)
    product_uom_qty = fields.Float(string="Quantity",required=True,readonly=False)
    flag = fields.Boolean(string="Sent",readonly=True)


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    team_type = fields.Selection([('internal', 'Internal'), ('external', 'External')],string="Type",default='internal')
    external_line_ids = fields.One2many('maintenance.external.team.line', 'team_id',string="Team Members")

class MaintenanceExternalTeamLine(models.Model):
    _name = 'maintenance.external.team.line'

    team_id = fields.Many2one('maintenance.team',string="Team")
    name = fields.Char(string='Name',required=True)
    manpower_cost = fields.Float(string='Man-Power Cost per hour')