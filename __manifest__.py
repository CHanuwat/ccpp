# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Cytology',
    'version': '1',
    'category': 'customize',
    'sequence': 101,
    'summary': 'Cytology',
    'description': "Project Cytology",
    'depends': ['base','mail','web','barcodes'],
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/cytology_menu.xml",
        "views/cytology_register_result_view.xml",
        "views/cytology_users_view.xml",
        ],
    'qweb': [ 
        ],
    
    'installable': True,
    "application": True,
    'license': 'LGPL-3',
    'assets': {
    'web.assets_backend': [
            "cytology/static/src/js/stock_barcode.js",
            "cytology/static/src/js/cytology_scan_barcode.js",
            'cytology/static/src/xml/**/*',  
            'cytology/static/src/css/**/*',      
        ],
    'web.assets_qweb': [
    ],
    'web.assets_frontend':[        
    ],
    'web.assets_common' :[
    ]
    },
}