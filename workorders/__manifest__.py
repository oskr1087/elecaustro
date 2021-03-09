# Copyright 2021 Vauxoo
{
    "name": "WorkOrders Management",
    "summary": """
    Work orders management
    """,
    "author": "Vauxoo",
    "website": "https://www.vauxoo.com",
    "license": "OEEL-1",
    "category": "Governament",
    "version": "14.0.1.0.0",
    "depends": ["base", "mail", "budget_gob"],
    "test": [],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/workorder_views.xml",
        "views/settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
