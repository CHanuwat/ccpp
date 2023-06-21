from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class Users(models.Model):
    _inherit = "res.users"
    
#    partner_id = fields.Many2one(auto_join=True)
    job_ids = fields.Many2many('hr.job',compute="_compute_job_ids")
    employee_level_ids = fields.Many2many('hr.employee', 'res_user_hr_employee_rel', 'user_id', 'employee_id', compute="_compute_employee_level_ids")
    
    def _compute_employee_level_ids(self):
        for obj in self:
            employee_id = self.env['hr.employee'].search([('user_id','=',obj.id)], limit=1)
            if obj.has_group('ccpp.group_ccpp_backoffice_user') or obj.has_group('ccpp.group_ccpp_frontoffice_user'):
                obj.employee_level_ids = employee_id
            elif obj.has_group('ccpp.group_ccpp_backoffice_manager') or obj.has_group('ccpp.group_ccpp_frontoffice_manager'):
                job_ids = self.get_child_job(employee_id.job_id)
                obj.employee_level_ids = job_ids.mapped("employee_ids")
            elif obj.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or obj.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
                job_ids = self.env['hr.job'].search([('department_id','=',employee_id.department_id.id)])                
                obj.employee_level_ids = job_ids.mapped("employee_ids")
            elif obj.has_group('ccpp.group_ccpp_ceo'):
                all_job_ids = self.env['hr.job'].search([])
                obj.employee_level_ids = all_job_ids.mapped("employee_ids")
            else:
                obj.employee_level_ids = self.env['hr.employee']  

    def _compute_job_ids(self):
        for obj in self:
            employee_id = self.env['hr.employee'].search([('user_id','=',obj.id)], limit=1)
            if obj.has_group('ccpp.group_ccpp_backoffice_user') or obj.has_group('ccpp.group_ccpp_frontoffice_user'):
                obj.job_ids = employee_id.job_id.ids
            elif obj.has_group('ccpp.group_ccpp_backoffice_manager') or obj.has_group('ccpp.group_ccpp_frontoffice_manager'):
                job_ids = self.get_child_job(employee_id.job_lines)
                obj.job_ids = job_ids
            elif obj.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or obj.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
                job_ids = self.env['hr.job'].search([('department_id','=',employee_id.department_id.id)])                
                obj.job_ids = job_ids
            elif obj.has_group('ccpp.group_ccpp_ceo'):
                all_job_ids = self.env['hr.job'].search([])
                obj.job_ids = all_job_ids
            else:
                obj.job_ids = self.env['hr.job']
                
                
            
    def get_child_job(self,job_lines,job_ids=False):
        if not job_ids:
            job_ids = self.env['hr.job']
        for job_id in job_lines:
            job_ids |= job_id
            job_ids |= self.get_child_job(job_id.child_lines, job_ids)   
        return job_ids
    
    def unlink(self):
        raise UserError("ระบบไม่สามารถลบผู้ใช้งานได้")
        res = super().unlink()