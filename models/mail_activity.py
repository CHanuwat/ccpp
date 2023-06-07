from odoo import fields, models
from datetime import datetime, timedelta

class MailActivity(models.Model):
    _inherit="mail.activity"
    
    ccpp_approve_line_id = fields.Many2one('ccpp.approve.line', string="CCPP Approve Line")
    approve_activity_type_id = fields.Many2one('approve.activity.type', string="Approve Activity Type")
    job_id = fields.Many2one('hr.job', string="Job Position")
    