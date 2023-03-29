from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class Approval(models.Model):
    _name = "approval"
    _inherit = ['mail.thread','portal.mixin','mail.activity.mixin']
    _order = "name"

    name = fields.Char(string="Name", compute="_compute_name")
    model_id = fields.Many2one("ir.model", string="Document")
    department_id = fields.Many2one("hr.department", string="Department", required="True")
    job_request_id = fields.Many2one("hr.job", string="Request Approval By", required="True")
    lines = fields.One2many("approval.line", "approve_id", string="Lines")
    
    _sql_constraints = [
        ('model_department_job_uniq', 'unique(model_id, department_id, job_request_id)', 'The code of the job position must be unique in company!'),
    ]
    
    @api.depends("model_id","department_id","job_request_id")
    def _compute_name(self):
        for obj in self:
            name = ''
            name_list = []
            if obj.model_id:
                name_list.append(obj.model_id.name)
            if obj.department_id:
                name_list.append(obj.department_id.name)
            if obj.job_request_id:
                name_list.append(obj.job_request_id.name)
            name = ' '.join(name_list)
            obj.name = name  
    
class ApprovalLine(models.Model):
    _name = "approval.line"

    approve_id = fields.Many2one("approval", index=True, ondelete='cascade', readonly=True, required=True)
    sequence = fields.Integer(string="Sequence")
    job_approve_ids = fields.Many2many("hr.job", "hr_job_approval_rel", "apporve_line_id", "job_id", string="Approver", required=True)
    
    