# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_catch_weight = fields.Boolean("Catch Weight", implied_group='tis_catch_weight_free.group_catch_weight')