from odoo import fields, models


class WorkOrder(models.Model):
    _name = "workorder.workorder"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Work Orders"

    code = fields.Char(required=True, default="/", readonly=True)
    name = fields.Char("Work Order", required=True, size=124)
    justification = fields.Html(required=True)
    company_id = fields.Many2one(
        "res.company", required=True, index=True, default=lambda self: self.env.company
    )
    partner_id = fields.Many2one("res.partner", string="Supplier")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    budget = fields.Monetary("Order Budget")
    budget_item = fields.Char("Budget Item")  # TODO: must be m2o

    request_user_id = fields.Many2one(
        "res.users", string="Requested by", default=lambda self: self.env.user
    )
    authorize_user_id = fields.Many2one(
        "res.users", string="Authorized by", readonly=True
    )
    approve_user_id = fields.Many2one("res.users", string="Approved by", readonly=True)

    item_budget_available = fields.Monetary("Budget available on Item")
    days = fields.Integer("Execution Time")
    technical_detail = fields.Html()
    payment_terms = fields.Html()
    penalty_terms = fields.Html()
    penalty_fee = fields.Float("Penalty Fee (%)")
    approved_date = fields.Date()
    approved_details = fields.Html()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("authorized", "Authorized"),
            ("approved", "Approved"),
        ],
        required=True,
        index=True,
        default="draft",
    )
    # TODO add accept details from  supplier

    def action_request(self):
        self.state = "requested"

    def action_authorize(self):
        self.state = "authorized"

    def action_approve(self):
        self.state = "approved"
