# -*- coding: utf-8 -*-
#################################################################################
# Author      : Mohamed Abdelhadi (Elhamari). (<https://webkul.com/>)
# Copyright(c): 2020- elhamari
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
#
#################################################################################
{
  "name"                 :  "Discount On Sale Order",
  "summary"              :  "The module allows you to set discount in fixed/percent basis for sale orders and order lines separately. The total discount in an order is sum of global discount and order line discount.",
  "category"             :  "Sales",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Mohamed Abdelhadi Elhag",
  "description"          :  """Odoo Discount on Sale Order
""",
  "depends"              :  [
                             'sale',
                             'account',
                            ],
  "data"                 :  [
                             'security/discount_security.xml',
                             'views/sale_views.xml',
                             'views/account_invoice_view.xml',
                             'views/res_config_views.xml',
                             #'report/sale_order_templates.xml',
                            ],
  "demo"                 :  [
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "pre_init_hook"        :  "pre_init_check",
}
