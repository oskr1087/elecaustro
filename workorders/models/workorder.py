from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WorkOrder(models.Model):
    _name = "workorder.workorder"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Work Orders"

    code = fields.Char(required=True, default="/", readonly=True)
    date = fields.Date(
        "Date",
        required=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    name = fields.Char(
        "Work Order",
        required=True,
        size=124,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    justification = fields.Html(
        required=True, states={"draft": [("readonly", False)]}, readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, index=True, default=lambda self: self.env.company
    )
    partner_id = fields.Many2one("res.partner", string="Supplier")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    budget = fields.Monetary(
        "Order Budget", states={"draft": [("readonly", False)]}, readonly=True,
    )
    budget_item = fields.Many2one(
        "account.analytic.account",
        string="Budget Item",
        domain=[("budget_type", "=", "budget"), ("internal_type", "=", "expense")],
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    request_user_id = fields.Many2one(
        "res.users",
        string="Requested by",
        default=lambda self: self.env.user,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    authorize_user_id = fields.Many2one(
        "res.users", string="Authorized by", readonly=True, tracking=True
    )
    approve_user_id = fields.Many2one(
        "res.users", string="Approved by", readonly=True, tracking=True
    )
    item_budget_available = fields.Monetary("Budget available on Item")
    days = fields.Integer(
        "Execution Time", states={"draft": [("readonly", False)]}, readonly=True,
    )
    technical_detail = fields.Html(
        states={"draft": [("readonly", False)]}, readonly=True,
    )

    payment_term_id = fields.Many2one(
        "workorder.payment.term",
        string="Payment Term",
        required=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    payment_terms = fields.Html(states={"draft": [("readonly", False)]}, readonly=True)

    penalty_id = fields.Many2one(
        "workorder.penalty",
        string="Penalty",
        required=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    penalty_terms = fields.Html(states={"draft": [("readonly", False)]}, readonly=True,)
    penalty_fee = fields.Float(
        "Penalty Fee (%)", states={"draft": [("readonly", False)]}, readonly=True,
    )

    approved_date = fields.Date("Approved Date", tracking=True)
    approved_details = fields.Html(readonly=True)

    supplier_acceptance_terms = fields.Html(
        default=lambda self: self.env.company.workorder_supplier_acceptance
    )
    acceptance_date = fields.Date("Acceptance Date", tracking=True)
    acceptance_done = fields.Boolean("Supplier Done Acceptance?", readonly=True)

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
        tracking=True,
    )

    @api.onchange("payment_term_id")
    def _onchange_payment_term(self):
        self.payment_terms = self.payment_term_id.name

    @api.onchange("penalty_id")
    def _onchange_penalty_id(self):
        self.penalty_terms = self.penalty_id.name

    def action_request(self):
        self.state = "requested"

    def action_authorize(self):
        self.state = "authorized"
        self.authorize_user_id = self.env.user

    def action_approve(self):
        self.state = "approved"
        self.approve_user_id = self.env.user

    def print_report(self):
        pass

    def register_acceptance(self):
        if not self.acceptance_date:
            raise UserError(_("Must define acceptance date."))
        self.acceptance_done = True


class WorkOrderPenalty(models.Model):
    _name = "workorder.penalty"
    _description = "Penalties"
    _rec_name = "code"

    code = fields.Char("Short Name", required=True)
    name = fields.Html()


class WorkOrderPaymentTerm(models.Model):
    _name = "workorder.payment.term"
    _description = "Workorder Payment Terms"
    _rec_name = "code"

    code = fields.Char("Short Name", required=True)
    name = fields.Html()
