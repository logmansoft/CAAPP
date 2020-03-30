# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    @api.model
    def _get_user_requisition(self):
        return self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('material_purchase_requisitions.group_purchase_requisition_user').id)],
            limit=1,
            order="id desc")

    @api.model
    def _get_user_account_manager(self):
        return self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('account.group_account_manager').id)],
            limit=1,
            order="id desc")

    custom_requisition_id = fields.Many2one('material.purchase.requisition', string='Requisitions', copy=False)
    requisition_user_id = fields.Many2one('res.users', string='Requisition User', default=_get_user_requisition)
    account_manager_id = fields.Many2one('res.users', string='Account Manager User', default=_get_user_account_manager)

    @api.multi
    def button_confirm(self):
        super(PurchaseOrder, self).button_confirm()
        notification = {
            'activity_type_id': self.env.ref('material_purchase_requisitions.notification_back_to_manager_after_confirm').id,
            'res_id': self.picking_ids.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.requisition_user_id.id,
            'note': 'Receive The Order'
        }
        self.env['mail.activity'].create(notification)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string='Requisitions Line',
        copy=False
    )
