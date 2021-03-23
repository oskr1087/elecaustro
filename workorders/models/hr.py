from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = "hr.department"

    code = fields.Char("Code")
    sequence_id = fields.Many2one(
        "ir.sequence", string="Workorder Sequence", readonly=True
    )

    def generate_sequence(self):
        if self.sequence_id:
            return
        self.sequence_id = self.env["ir.sequence"].create(
            {
                "name": f"Department Sequence {self.code}",
                "code": self.code,
                "implementation": "no_gap",
                "prefix": f"{self.code}-",
                "padding": 5,
                "use_date_range": True,
            }
        )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def department_by_user(self, user_id):
        empl = self.search([("user_id", "=", user_id)], limit=1)
        return empl.department_id

    def fullname_report(self):
        return f"{self.job_title} {self.name}"
