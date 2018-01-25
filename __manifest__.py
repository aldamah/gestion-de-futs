# -*- coding: utf-8 -*-
{
    'name': "Gestion de Futs",

    'summary': """
        Module de gestion des mouvements de fûts de la société ANKARANA""",

    'description': """
        Ce module permet de gerer les entrées et sorties de fûts,
    """,

    'author': "Andoniraina",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','stock','purchase','report','fleet'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/client.xml',
        'views/mouvement.xml',
       
       # 'views/stock_wharehouse.xml',
        'reports/client_report_pdf_view.xml',
        'reports/achat_report.xml',
        'reports/vente_report.xml',
   
        
        
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}