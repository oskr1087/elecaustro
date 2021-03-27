from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WorkOrder(models.Model):
    _name = "workorder.workorder"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Work Orders"

    def user_job_title(self, user):
        return user.employee_id.job_id.name

    def _get_sequence(self, user_id):
        department = self.env["hr.employee"].department_by_user(user_id)
        return (
            department.sequence_id
            if department.sequence_id
            else department.parent_id.sequence_id
        )

    @api.depends("request_user_id")
    def _compute_department(self):
        self.department_id = (
            self.env["hr.employee"].department_by_user(self.request_user_id.id).id
        )

    @api.model
    def create(self, values):
        seq_date = None
        if "date" in values:
            seq_date = fields.Datetime.context_timestamp(
                self, fields.Datetime.to_datetime(values["date"])
            )
        values["code"] = self._get_sequence(values["request_user_id"]).next_by_id(
            seq_date
        ) or _("New")
        return super().create(values)

    code = fields.Char(required=True, readonly=True, default=lambda self: _("New"))
    date = fields.Date(
        "Date",
        required=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
        default=fields.Date.today(),
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
        "Order Budget", states={"certified": [("readonly", False)]}, readonly=True,
    )
    budget_item = fields.Many2one(
        "account.analytic.account",
        string="Budget Item",
        domain=[("budget_type", "=", "budget"), ("internal_type", "=", "expense")],
        states={"certified": [("readonly", False)]},
        readonly=True,
    )

    department_id = fields.Many2one(
        "hr.department", compute="_compute_department", store=True, string="Department"
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
    certify_user_id = fields.Many2one(
        "res.users", string="Certificate by", readonly=True, tracking=True
    )
    approve_user_id = fields.Many2one(
        "res.users", string="Approved by", readonly=True, tracking=True
    )
    item_budget_available = fields.Monetary("Budget available on Item")
    days = fields.Integer(
        "Execution Time", states={"draft": [("readonly", False)]}, readonly=True,
    )
    type_days = fields.Selection(
        [("working", "Working Days"), ("calendar", "Calendar Days")],
        string="Calendar Type",
        states={"draft": [("readonly", False)]},
        required=True,
        default="working",
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
    acceptance_date = fields.Date("Acceptance Date", tracking=True, readonly=True)
    certificate_date = fields.Date("Certificate Date", tracking=True, readonly=True)
    acceptance_done = fields.Boolean("Supplier Done Acceptance?", readonly=True)

    approve_level = fields.Selection(
        [("director", "Director"), ("manager", "Manager")],
        string="Type Approve",
        required=True,
        default="director",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("certified", "Certified"),
            ("requested", "Requested"),
            ("authorized", "Authorized"),
            ("approved", "Approved"),
        ],
        required=True,
        index=True,
        default="draft",
        tracking=True,
    )

    @api.constrains("date")
    def _check_date_allowed(self):
        if self.date < fields.Date.today():
            raise UserError(_("Workorder can't have date less than today."))

    @api.onchange("payment_term_id")
    def _onchange_payment_term(self):
        self.payment_terms = self.payment_term_id.name

    @api.onchange("penalty_id")
    def _onchange_penalty_id(self):
        self.penalty_terms = self.penalty_id.name

    def action_request(self):
        self.state = "requested"
        self.certificate_date = fields.Date.today()
        self.certify_user_id = self.env.user

    def action_authorize(self):
        self.state = "authorized"
        self.authorize_user_id = self.env.user
        if self.approve_level == "director":
            view = self.env.ref("workorders.view_wizard_approve_workorder_form")
            return {
                "type": "ir.actions.act_window",
                "name": _("Approve Details"),
                "view_mode": "form",
                "res_model": "wizard.approve.workorder",
                "views": [(view.id, "form")],
                "view_id": view.id,
                "target": "new",
            }

    def action_approve(self):
        self.state = "approved"
        self.approved_date = fields.Date.today()
        self.approve_user_id = self.env.user

    def action_certified(self):
        self.state = "certified"

    def print_report(self):
        return self.env.ref("workorders.workorder_report").report_action(
            self.filtered(lambda r: r.state == "approved")
        )

    def register_acceptance(self):
        if not self.acceptance_date:
            raise UserError(_("Must define acceptance date."))
        self.acceptance_done = True

    def _get_report_base_filename(self):
        return self.code


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
