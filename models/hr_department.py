from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class Department(models.Model):
    _inherit = "hr.department"
    
    code = fields.Char(string="Department Code")

    def unlink(self):
        raise UserError("ระบบไม่สามารถลบฝ่ายและแผนกได้")
        res = super().unlink()
        
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for department in self:
            department.complete_name = department.name