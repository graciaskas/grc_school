# -*- coding: utf-8 -*-
{
    "name": "School management",
    "summary": "School management odoo application",
    "description": """
        Manage students,faculties,finance...
    """,
    "author": "ZeSlap Platforms",
    "website": "https://www.zeslap.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Industries",
    "version": "17.0",
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "fleet", "sale"],
    # always loaded
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/school_student.xml",
        "views/school_faculty.xml",
        "views/menus.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
