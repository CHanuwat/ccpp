from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class ApproveActivityType(models.Model):
    _name = "approve.activity.type"
    _inherit = ['mail.thread']

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Name")
    code = fields.Char("Code")
    color = fields.Integer(string="Color")
    count_doc = fields.Integer(string="Count Document", compute="_compute_count_doc",store=False)
    
    def _compute_count_doc(self):
        for obj in self:
            count_doc = 0
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            activity_ids = self.env['mail.activity'].search([('job_id','in',employee_id.job_lines.ids),('approve_activity_type_id','=',obj.id)])
            count_doc = len(activity_ids)
            obj.count_doc = count_doc
        
    def action_get_doc(self):
        for obj in self:
            action = True
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            activity_ids = self.env['mail.activity'].search([('job_id','in',employee_id.job_lines.ids),('approve_activity_type_id','=',obj.id)])
            record_ids = activity_ids.mapped('res_id')
            if obj.code == 'ccpp':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_ccpp_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            elif obj.code == 'solution':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_solution_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            elif obj.code == 'strategy':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_strategy_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            return action
    
    def unlink(self):
        #raise UserError("ระบบไม่สามารถลบ Appove Activity Type ได้")
        res = super().unlink()