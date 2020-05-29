# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Catching Material',
    'version': '1.0.0',



    'summary': """This module allow your employees/users to create Product Catching by cars.""",
    'description': """
    
    """,
    'category': 'Manufacturing',
    'depends': [
                'fleet',
                'mrp',
                'product',
                'purchase',
                ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/catching_request_data.xml',
        'views/material_catching_view.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
