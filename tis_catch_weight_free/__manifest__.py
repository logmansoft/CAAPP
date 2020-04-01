# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Catch Weight Management',
    'version': '1.0',
    'sequence': 1,
    'category': 'Inventory',
    'summary': 'Catchw8 - Catch Weight Management',
    'description': """
    This module is for activating Catch weight management
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'price': 0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'sale'
    ],
    'data': [
        'security/catch_weight_security.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',

    ],
    'images': ['images/main_screenshot.gif'],
    'installable': True,
    'auto_install': False,
    'application': True
}

