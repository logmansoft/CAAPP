from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_catch_weight = fields.Boolean("Catch Weight", implied_group='tis_catch_weight.group_catch_weight')