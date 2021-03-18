from odoo import fields, models


class WizardApproveWorkOrder(models.TransientModel):
    _name = "wizard.approve.workorder"
    _description = "Wizard to Approve Workorders"

    comment = fields.Html(default=lambda self: self.env.company.approved_comments)

    def action_register_approve(self):
        workorder_id = self.env.context.get("active_id")
        workorder = self.env["workorder.workorder"].browse(workorder_id)
        workorder.write({"approved_details": self.comment})
        workorder.action_approve()
        return {"type": "ir.actions.act_window_close"}
