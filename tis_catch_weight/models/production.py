from odoo import models, fields, api, _

class MrpProductionCWUOM(models.Model):
    _inherit  = 'mrp.production'
    

    
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=1.0)
    cw_qty_produced = fields.Float(compute="_get_cw_produced_qty", string="Quantity Produced")
    
    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        res  = super(MrpProductionCWUOM,self).onchange_product_id()
        if not self.product_id:
            self.bom_id = False
        else:
            bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id, company_id=self.company_id.id)
            if bom.type == 'normal':
                self.product_cw_uom_qty = self.bom_id.product_cw_uom_qty
                self.product_cw_uom = self.bom_id.product_cw_uom
            else:
                self.bom_id = False
                self.product_cw_uom = self.product_id.cw_uom_id
        return res 
        

    def _generate_finished_moves(self):
        move = super(MrpProductionCWUOM, self)._generate_finished_moves()
        move.product_cw_uom = self.product_cw_uom
        move.product_cw_uom_qty = self.product_cw_uom_qty
        move._action_confirm()
        return move
    
    def _generate_raw_move(self, bom_line, line_data):
        move = super(MrpProductionCWUOM, self)._generate_raw_move(bom_line, line_data)

        cw_original_quantity = (self.product_cw_uom_qty - self.qty_produced) or 1.0
        move.product_cw_uom_qty = bom_line.product_cw_uom_qty
        if bom_line.product_cw_uom_qty != self.product_cw_uom_qty:
            move.product_cw_uom_qty = (bom_line.product_cw_uom_qty * self.product_cw_uom_qty)
        elif bom_line.product_cw_uom_qty < self.product_cw_uom_qty:
            move.product_cw_uom_qty = (bom_line.product_cw_uom_qty / self.product_cw_uom_qty)
        
        move.cw_unit_factor = move.product_cw_uom_qty / cw_original_quantity
        return move

    @api.multi
    def action_assign(self):
        assign = super(MrpProductionCWUOM, self).action_assign()
        if assign:
            for rec in self.move_raw_ids:
                if rec.product_uom_qty == rec.reserved_availability:
                    rec.cw_qty_reserved = rec.product_cw_uom_qty
        return assign

    @api.multi
    def button_mark_done(self):
        super(MrpProductionCWUOM, self).button_mark_done()
        moves_done = self.move_raw_ids.filtered(lambda x: x.state == 'done')
        moves_finish = self.move_finished_ids.filtered(lambda x: x.state =='done')
        for moves_finish in moves_finish:
            moves_finish.cw_qty_done = moves_finish.product_cw_uom_qty
        for move_done in moves_done:
            move_done.cw_qty_consumed = move_done.cw_qty_reserved

    @api.multi
    @api.depends('workorder_ids.state', 'move_finished_ids', 'is_locked')
    def _get_cw_produced_qty(self):
        for production in self:
            done_moves = production.move_finished_ids.filtered(lambda x: x.state != 'cancel' and x.product_id.id == production.product_id.id)
            cw_qty_produced = sum(done_moves.mapped('cw_qty_done'))
            wo_done = True
            if any([x.state not in ('done', 'cancel') for x in production.workorder_ids]):
                wo_done = False
            production.check_to_done = production.is_locked and done_moves and (cw_qty_produced >= production.product_cw_uom_qty) and (production.state not in ('done', 'cancel')) and wo_done
            production.cw_qty_produced = cw_qty_produced
        return True

    @api.multi
    def button_unreserve(self):
        super_unreserved = super(MrpProductionCWUOM, self).button_unreserve()
        for move in self.move_raw_ids:
            move.cw_qty_reserved = 0.0
        return super_unreserved

class ChangeProductionQtyCW(models.TransientModel):
    _inherit = 'change.production.qty'



    @api.multi
    def change_prod_qty(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for wizard in self:
            production = wizard.mo_id
            produced = sum(production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id).mapped('quantity_done'))
            cw_produced = sum(production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id).mapped('cw_qty_done'))
            if wizard.product_qty < produced:
                format_qty = '%.{precision}f'.format(precision=precision)
                raise UserError(_("You have already processed %s. Please input a quantity higher than %s ") % (format_qty % produced, format_qty % produced))
            old_production_qty = production.product_qty
            old_production_cw_qty = production.product_cw_uom_qty
            production.write({'product_qty': wizard.product_qty, 'product_cw_uom_qty': old_production_cw_qty*wizard.product_qty})
            done_moves = production.move_finished_ids.filtered(lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')), production.product_uom_id)
            qty_cw_produced = production.product_id.cw_uom_id._compute_quantity(sum(done_moves.mapped('product_cw_uom_qty')), production.product_cw_uom)
            factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced, production.bom_id.product_uom_id) / production.bom_id.product_qty
            cw_factor = production.product_cw_uom._compute_quantity(production.product_cw_uom_qty - qty_cw_produced, production.bom_id.product_cw_uom) / production.bom_id.product_cw_uom_qty
            boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
            documents = {}
            for line, line_data in lines:
                move, old_qty, new_qty = production._update_raw_move(line, line_data)
                move.product_cw_uom_qty = cw_factor
                move.cw_qty_reserved = cw_factor
                iterate_key = production._get_document_iterate_key(move)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move: (new_qty, old_qty)}, iterate_key, 'UP')
                    for key, value in document.items():
                        if documents.get(key):
                            documents[key] += [value]
                        else:
                            documents[key] = [value]
            production._log_manufacture_exception(documents)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']
            finished_moves_modification = self._update_product_to_produce(production, production.product_qty - qty_produced, old_production_qty)
            #finished_moves_cw_modification = self._update_product_to_produce(production, production.product_cw_uom_qty - qty_cw_produced, old_production_cw_qty)
            production._log_downside_manufactured_quantity(finished_moves_modification)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves._action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id
                if operation_bom_qty.get(operation.id):
                    cycle_number = float_round(operation_bom_qty[operation.id] / operation.workcenter_id.capacity, precision_digits=0, rounding_method='UP')
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                quantity = wo.qty_production - wo.qty_produced
                if production.product_id.tracking == 'serial':
                    quantity = 1.0 if not float_is_zero(quantity, precision_digits=precision) else 0.0
                else:
                    quantity = quantity if (quantity > 0) else 0
                if float_is_zero(quantity, precision_digits=precision):
                    wo.final_lot_id = False
                    wo.active_move_line_ids.unlink()
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                if wo.qty_produced == wo.qty_production and wo.state == 'progress':
                    wo.state = 'done'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_line_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if quantity > 0 and wo.move_raw_ids.filtered(lambda x: x.product_id.tracking != 'none') and not wo.active_move_line_ids:
                    wo._generate_lot_ids()
        return {}
