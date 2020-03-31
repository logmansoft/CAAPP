# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Catch Weight Management',
    'version': '12.0.0.3',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'Catch Weight Management',
    'description': """
    This module is for activating Catch weight management
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'price': 130,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'account',
        'sale_management', 
        'purchase',
        'stock',
        'product',
    ],
    'data': [
        'security/catch_weight_security.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_invoice_view.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_move_line_views.xml',
        'views/res_config_settings_views.xml',
        'report/sale_report_template.xml',
        'report/purchase_order_templates.xml',
        'report/purchase_quotation_templates.xml',
        'report/report_invoice.xml',
        'report/report_stockpicking_operations.xml',
        'report/report_deliveryslip.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True
}

