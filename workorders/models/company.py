from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    workorder_supplier_acceptance = fields.Html()
    approved_comments = fields.Html()


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    workorder_supplier_acceptance = fields.Html(
        related="company_id.workorder_supplier_acceptance", readonly=False
    )
    approved_comments = fields.Html(
        related="company_id.approved_comments", readonly=False
    )
