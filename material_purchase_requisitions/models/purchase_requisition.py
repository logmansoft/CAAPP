# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

class MaterialPurchaseRequisition(models.Model):
    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel', 'reject'):
                raise Warning(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
        return super(MaterialPurchaseRequisition, self).unlink()

    @api.model
    def _get_user_requisition(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('material_purchase_requisitions.group_purchase_requisition_user').id)],
                                            limit=1,
                                            order="id desc")

    @api.model
    def _get_project_manager_approve(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('material_purchase_requisitions.group_purchase_requisition_manager').id)],
                                            limit=1,
                                            order="id desc")

    @api.model
    def _get_department_manager_approve(self):
        for rec in self:
            if rec.employee_id.department_id and rec.employee_id.department_id.manager_id:
                return rec.employee_id.department_id.manager_id.user_id.id
            

        #return self.env['res.users'].search([('groups_id', 'in', self.env.ref('material_purchase_requisitions.group_purchase_requisition_manager').id)],
                                            #limit=1,
                                            #order="id desc")
    @api.model
    def _get_purchase_manager_approve(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('material_purchase_requisitions.group_purchase_requisition_department').id)],
                                            limit=1,
                                            order="id desc")

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )
    
    @api.multi
    def check_avaiabilty(self):
        for rec in self:
            for product in rec.requisition_line_ids:
                if product.product_id:
                    on_hand = product.product_id.qty_available
                    product.available_qty = on_hand
                
        return True
            
    #state = fields.Selection([
    #    ('draft', 'New'),
    #    ('pm_confirm', 'Waiting Projects Manager Approval'),
    #    ('pum_approve', 'Waiting Purchase Manager Approval'),
    #    ('approve', 'Approved'),
    #    ('stock', 'Purchase Order Created'),
    #    ('receive', 'Received'),
    #    ('cancel', 'Cancelled'),
    #    ('reject', 'Rejected')],
    #    default='draft',
    #   track_visibility='onchange',
    #)
    state = fields.Selection([
        ('draft', 'New'),
        ('dept_confirm', 'Department Manager Approval'),
        ('qa_approve', 'Quality Manager Approval'),
        ('st_approve', 'Store Manager Approval'),
        ('fm_approve', 'Finance Manager Approval'),
        ('gm_approve', 'General Manager Approval'),
        ('approve', 'Approved'),
        #('picking', 'Picking Created'),
        #('stock', 'Purchase Order Created'),
        ('receive', 'Received'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft',
        track_visibility='onchange',
    )
    request_date = fields.Date(
        string='Requisition Date',
        default=fields.Date.today(),
        required=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        copy=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)] or False, limit=1),
        required=True,
        copy=True,
    )
    approve_manager_id = fields.Many2one(
        'hr.employee',
        string='Quality Manager',
        readonly=True,
        copy=False,
    )
    reject_manager_id = fields.Many2one(
        'hr.employee',
        string='Quality Manager Reject',
        readonly=True,
    )
    approve_st_manager_id = fields.Many2one(
        'hr.employee',
        string='Store Manager',
        readonly=True,
        copy=False,
    )
    reject_st_manager_id = fields.Many2one(
        'hr.employee',
        string='Store Manager Reject',
        readonly=True,
    )
    approve_fn_manager_id = fields.Many2one(
        'hr.employee',
        string='Finance Manager',
        readonly=True,
        copy=False,
    )
    approve_gm_manager_id = fields.Many2one(
        'hr.employee',
        string='General Manager',
        readonly=True,
        copy=False,
    )
    approve_employee_id = fields.Many2one(
        'hr.employee',
        string='Approved by',
        readonly=True,
        copy=False,
    )
    reject_employee_id = fields.Many2one(
        'hr.employee',
        string='Rejected by',
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        copy=True,
    )
    requisition_line_ids = fields.One2many(
        'material.purchase.requisition.line',
        'requisition_id',
        string='Purchase Requisitions Line',
        copy=True,
    )
    date_end = fields.Date(
        string='Requisition Deadline', 
        readonly=True,
        help='Last date for the product to be needed',
        copy=True,
    )
    date_done = fields.Date(
        string='Date Done', 
        readonly=True, 
        help='Date of Completion of Purchase Requisition',
    )
    managerapp_date = fields.Date(
        string='Quality Approval Date',
        readonly=True,
        copy=False,
    )
    stmanagerapp_date = fields.Date(
        string='Store Approval Date',
        readonly=True,
        copy=False,
    )
    fnmanagerapp_date = fields.Date(
        string='Finance Approval Date',
        readonly=True,
        copy=False,
    )
    gmmanagerapp_date = fields.Date(
        string='General Approval Date',
        readonly=True,
        copy=False,
    )
    manareject_date = fields.Date(
        string='Quality Manager Reject Date',
        readonly=True,
    )
   
    userreject_date = fields.Date(
        string='Rejected Date',
        readonly=True,
        copy=False,
    )
    userrapp_date = fields.Date(
        string='Approved Date',
        readonly=True,
        copy=False,
    )
    receive_date = fields.Date(
        string='Received Date',
        readonly=True,
        copy=False,
    )
    reason = fields.Text(
        string='Reason for Requisitions',
        required=False,
        copy=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        copy=True,
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=False,
        copy=True,
    )
    delivery_picking_id = fields.Many2one(
        'stock.picking',
        string='Internal Picking',
        readonly=True,
        copy=False,
    )
    employee_confirm_id = fields.Many2one(
        'hr.employee',
        string='Department Manager',
        readonly=True,
        copy=False,
    )
    confirm_date = fields.Date(
        string='Deprtment Manager Approval Date',
        readonly=True,
        copy=False,
    )
    
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'custom_requisition_id',
        string='Purchase Ordes',
    )
    custom_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
        copy=False,
    )
    request_flag = fields.Boolean('Requested Stock Flag', default=False)
    driver_name = fields.Many2one('res.partner', string='Driver')
    requisition_user_id = fields.Many2one('res.users', string='Requisition User', default=_get_user_requisition)
    dept_user_id = fields.Many2one('res.users', string='Department Managers', default=_get_department_manager_approve)
    pm_user_id = fields.Many2one('res.users', string='Projects Managers', default=_get_project_manager_approve)
    pum_user_id = fields.Many2one('res.users', string='Purchase Managers', default=_get_purchase_manager_approve)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    move_ids = fields.One2many('stock.move.requistion.line', 'current_requisition_id', 'Consuming',
        copy=False)
    required_purchase_order = fields.Boolean('Required PO')
    
    last_puchase_ids = fields.One2many('pruchase.order.link', 'requsition_link_id', 'Last puchase Orders')
    #fields.Many2many('puchase.order', 'requisition_order_ids', string="Puchase Orders",
                                       # copy=False, 
                                        #domain=[('state','=', 'done')]
                                       # )
    @api.multi
    def get_last_purchased_order(self):
        for rec in self:

            dict_list = []
            for line in rec.requisition_line_ids:
                if line.requisition_type == 'purchase':

                    line_ids = self.env['purchase.order.line'].search([('product_id', '=', line.product_id.id)])
                    filter_line_ids = line_ids.filtered(lambda x: x.order_id.state not in ('done', 'purchase'))
                    if filter_line_ids:
                        if len(filter_line_ids)>=3:
                            i = -3
                            while i >=-3 :
                                if i != 0 :

                                    dict_list.append((0, 0, {'product_id': filter_line_ids[i].product_id.id,
                                                            'vendor_id': filter_line_ids[i].order_id.partner_id.id,
                                                            'date': filter_line_ids[i].order_id.date_order,
                                                            'unit_price': filter_line_ids[i].price_unit,
                                                            'product_uom_qty': filter_line_ids[i].product_qty,
                                                            'qty_uom': filter_line_ids[i].product_uom,
                                                            'total': filter_line_ids[i].order_id.date_order.amount_total,
                                                            'purchase_order_id': filter_line_ids[i].order_id.id}))
                                else:
                                    break
                                i += 1
                        elif len(filter_line_ids) == 2:
                            
                            i = -2
                            while i >=-2 :
                                if i != 0 :

                                    dict_list.append((0, 0, {'product_id': filter_line_ids[i].product_id.id,
                                                            'vendor_id': filter_line_ids[i].order_id.partner_id.id,
                                                            'date': filter_line_ids[i].order_id.date_order,
                                                            'unit_price': filter_line_ids[i].price_unit,
                                                            'product_uom_qty': filter_line_ids[i].product_qty,
                                                            'qty_uom': filter_line_ids[i].product_uom.id,
                                                            'total': filter_line_ids[i].order_id.amount_total,
                                                            'purchase_order_id': filter_line_ids[i].order_id.id}))
                                else:
                                    break
                                i += 1
                            

                        else:
                            dict_list.append((0, 0, {'product_id': filter_line_ids[0].product_id.id}))
            if dict_list:

                rec.last_puchase_ids.unlink()
                rec.write({'last_puchase_ids': dict_list})
            else:
                raise UserError(_('It seems that there is no purchase orders done for the choosen product yet'))


        return True

    @api.multi
    def make_it_as_po(self):
        return True

    @api.multi
    def get_consuming_moves(self):
        for rec in self:
            if not rec.date_from or not rec.date_to or rec.date_to< rec.date_from:
                raise UserError(_('Either the Date From is not setting Corectly or the Date To please make sure about the values of these fields under (Consuming Page)'))

            else:
                for product in rec.requisition_line_ids:
                    moves_filtter = []
                    moves = self.env['stock.move'].search([('product_id', '=', product.product_id.id),
                                                            ('date', '>=', rec.date_from),
                                                            ('date', '<=', rec.date_to),
                                                            ('scrapped', '=', False)])
                    moves_filtter = moves.filtered(lambda x: x.picking_type_id.code  in ('internal', 'mrp_operation'))
                    if moves_filtter:
                        rec.move_ids.unlink()
                        rec.write({'move_ids': [(0, 0, {'product_id': x.product_id.id,
                                                    'date': x.date,
                                                    'product_uom_qty': x.product_uom_qty,
                                                    'current_requisition_id': rec.id,
                                                    'qty_uom': x.product_uom.id}) for x in moves_filtter  if x.state in ('done')]})
                    else:

                        raise UserError(_('It seems that there is no Comsuption based on the specified dates for the choosen product yet '))
        return True

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
        vals.update({
            'name': name
            })
        
        res = super(MaterialPurchaseRequisition, self).create(vals)
        
        return res

    @api.multi
    def requisition_confirm(self):
        for rec in self:
            manager_mail_template = self.env.ref('material_purchase_requisitions.email_confirm_material_purchase_requistion')
            rec.employee_confirm_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.confirm_date = fields.Date.today()
            rec.state = 'dept_confirm'
            if manager_mail_template:
                manager_mail_template.send_mail(self.id)
            
            if rec.dept_user_id.id or self._get_department_manager_approve():
                rec.dept_user_id = self._get_department_manager_approve()
                notification = {
                    'activity_type_id': self.env.ref('material_purchase_requisitions.notification_confirm_order').id,
                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'material.purchase.requisition')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': rec.dept_user_id.id,
                    'note': 'Approval Request for Purchase Order'
                }
            else:
                raise UserError(_('Either the employee who made the request does not belong to specific department or his department has no manager.'))
            self.env['mail.activity'].create(notification)
            
    @api.multi
    def requisition_reject(self):
        for rec in self:
            rec.state = 'reject'
            rec.reject_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.userreject_date = fields.Date.today()

    @api.multi
    def project_manager_approve(self):
        for rec in self:
            rec.managerapp_date = fields.Date.today()
            rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            employee_mail_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition_iruser_custom')
            email_iruser_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition')
            employee_mail_template.send_mail(self.id)
            email_iruser_template.send_mail(self.id)
            rec.state = 'pum_approve'

            notification = {
                'activity_type_id': self.env.ref('material_purchase_requisitions.notification_to_purchase_manager').id,
                'res_id': rec.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'material.purchase.requisition')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': rec.pum_user_id.id,
                'note': 'Approval Request for Purchase Order'
            }
            self.env['mail.activity'].create(notification)

    @api.multi
    def department_manager_approve(self):
        for rec in self:
            if rec.dept_user_id.id or self._get_department_manager_approve():
                rec.dept_user_id = self._get_department_manager_approve()
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'dept_confirm'

    @api.multi
    def purchase_manager_approve(self):
        for rec in self:
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'approve'

    @api.multi
    def quality_manager_approve(self):
        for rec in self:
            rec.managerapp_date = fields.Date.today()
            rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'qa_approve'
    
    @api.multi
    def store_manager_approve(self):
        for rec in self:
            rec.stmanagerapp_date = fields.Date.today()
            rec.approved_st_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            result = rec.create_picking()
            if result and rec.required_purchase_order==False:
                rec.state = 'done'
            else:
                rec.state = 'st_approve'

            

    @api.multi
    def finanace_manager_approve(self):
        for rec in self:
            rec.fnmanagerapp_date = fields.Date.today()
            rec.approved_fn_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'fm_approve'

    
    @api.multi
    def gneral_manager_approve(self):
        for rec in self:
            rec.gmmanagerapp_date = fields.Date.today()
            rec.approved_gm_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'gm_approve'

    @api.multi
    def reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'product_uom': line.uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'name': line.product_id.name,
            'picking_type_id': self.custom_picking_type_id.id,
            'picking_id': stock_id.id,
            'custom_requisition_line_id': line.id
        }
        return pick_vals

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {
                 'product_id': line.product_id.id,
                 'name':line.product_id.name,
                 'product_qty': line.qty,
                 'product_uom': line.uom.id,
                 'date_planned': fields.Date.today(),
                 'price_unit': line.product_id.standard_price,
                 'order_id': purchase_order.id,
                 'account_analytic_id': self.analytic_account_id.id,
                 'custom_requisition_line_id': line.id
        }
        return po_line_vals

    @api.multi
    def create_picking(self):
        flag = False
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        
        for rec in self:
            if not rec.requisition_line_ids:
                raise Warning(_('Please create some requisition lines.'))
            if any(line.requisition_type =='internal' for line in rec.requisition_line_ids):
                flag = True
                if not rec.location_id.id:
                        raise Warning(_('Select Source location under the picking details.'))
                if not rec.custom_picking_type_id.id:
                        raise Warning(_('Select Picking Type under the picking details.'))
                if not rec.dest_location_id:
                    raise Warning(_('Select Destination location under the picking details.'))
#                 if not rec.employee_id.dest_location_id.id or not rec.employee_id.department_id.dest_location_id.id:
#                     raise Warning(_('Select Destination location under the picking details.'))
                picking_vals = {
                        'partner_id': rec.sudo().employee_id.address_home_id.id,
                        'min_date': fields.Date.today(),
                        'location_id': rec.location_id.id,
                        'location_dest_id': rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                        'picking_type_id': rec.custom_picking_type_id.id,#internal_obj.id,
                        'note': rec.reason,
                        'custom_requisition_id': rec.id,
                        'origin': rec.name,
                    }
                stock_id = stock_obj.sudo().create(picking_vals)
                delivery_vals = {
                        'delivery_picking_id': stock_id.id,
                    }
                rec.write(delivery_vals)
            for line in rec.requisition_line_ids:
                if line.requisition_type == 'internal':
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                    notification = {
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_back_to_user_manager').id,
                        'res_id': rec.delivery_picking_id.id,
                        'res_model_id': self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1).id,
                        'icon': 'fa-pencil-square-o',
                        'date_deadline': fields.Date.today(),
                        'user_id': rec.requisition_user_id.id,
                        'note': 'Receive The Order'
                    }
                    self.env['mail.activity'].create(notification)
            #rec.state = 'picking'
        return flag
    
    @api.multi
    def request_stock(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        for rec in self:

                
            po_dict = {}
            for line in rec.requisition_line_ids:
              
                if line.requisition_type == 'purchase':
                    if not line.partner_id:
                        raise Warning(_('PLease Enter Atleast One Vendor on Requisition Lines'))
                    if not(line.direct_purchase): 
                        for partner in line.partner_id:
                            if partner not in po_dict:
                               
                                po_vals = rec.create_vals(partner)
                                purchase_order = purchase_obj.create(po_vals)
                                po_dict.update({'partner': purchase_order})
                                po_line_vals = rec._prepare_po_line(line, purchase_order)
                        
                                purchase_line_obj.sudo().create(po_line_vals)
                            else:
                                purchase_order = po_dict.get(partner)
                                po_line_vals = rec._prepare_po_line(line, purchase_order)
    #                          
                                purchase_line_obj.sudo().create(po_line_vals)
                    else:
                        if line.partner_id[0] not in po_dict:
                            po_vals = rec.create_vals(line.partner_id[0])
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({'partner': purchase_order})
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                    
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(line.partner[0])
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
#                          
                            purchase_line_obj.sudo().create(po_line_vals)
                        purchase_order.state = 'purchase'
                rec.request_flag = True


    @api.multi
    def create_vals(self, partner):
        po_vals = {
            'partner_id': partner.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'date_order': fields.Date.today(),
            'company_id': self.env.user.company_id.id,
            'custom_requisition_id': self.id,
            'origin': self.name,
            'driver_name': self.driver_name,
        }
        return po_vals

    @api.multi
    def go_to_budget(self):
        budget_obj = self.env['crossovered.budget']
        for rec in self:
            if rec.request_date:
                budget = budget_obj.search([('date_from', '<=', rec.request_date), ('date_to', '>=', rec.request_date)])

                if budget:

                    return {
                        'name': _('Budget'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_id' : budget.id,
                        'res_model': 'crossovered.budget',
                        'view_id': self.env.ref('account_budget.crossovered_budget_view_form').id,
                        'type': 'ir.actions.act_window',
                        'target': 'current',
                        }
                else:
                    raise Warning(_('Please Make Sure if there is Budget for the year of the Requsistion Date'))



    @api.multi
    def action_received(self):
        for rec in self:
            rec.receive_date = fields.Date.today()
            rec.state = 'receive'
    
    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.onchange('employee_id')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.employee_id.department_id.id
            rec.dest_location_id = rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id 
            
    @api.multi
    def show_picking(self):
        for rec in self:
            res = self.env.ref('stock.action_picking_tree_all')
            res = res.read()[0]
            res['domain'] = str([('custom_requisition_id', '=', rec.id)])
        return res
        
    @api.multi
    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref('purchase.purchase_rfq')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('custom_requisition_id', '=', rec.id)])
        return purchase_action

class StockMoveRequisitionLine(models.Model):
    _name = 'stock.move.requistion.line'

    current_requisition_id = fields.Many2one('material.purchase.requisition', 'Requistion')
    product_uom_qty = fields.Float('Product Qty')
    product_id = fields.Many2one('product.product', 'Product')
    date = fields.Date('Date')
    qty_uom  = fields.Many2one('uom.uom', 'Product Uom')



class PurchaseOrderLink(models.Model):
    _name = 'pruchase.order.link'

    requsition_link_id = fields.Many2one('material.purchase.requisition', 'Requistion')
    product_uom_qty = fields.Float('Product Qty')
    product_id = fields.Many2one('product.product', 'Product')
    date = fields.Date('Order Date')
    qty_uom  = fields.Many2one('uom.uom', 'Product Uom')
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    total = fields.Float('Total')
    unit_price = fields.Float('Unit Price')
    purchase_order_id = fields.Many2one('purchase.order', 'Reference')


    