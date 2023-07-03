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
    model_ids = fields.Many2many("ir.model","approval_model_rel", "approve_id", "model_id", string="Documents")
    department_id = fields.Many2one("hr.department", string="Department", required="True")
    contract_type_id = fields.Many2one("hr.contract.type", string="Request By Employee Type")
    domain_contract_type_ids = fields.Many2many("hr.contract.type", string="Domain Employee_ Type", compute="_compute_domain_contract_type")
    job_request_ids = fields.Many2many("hr.job", string="Request Approval By", required="True")
    job_request_id = fields.Many2one("hr.job", string="Request Approval By")
    domain_job_request_ids = fields.Many2many("hr.job", "hr_job_request_approval_rel", "apporve_id", "job_request_id", string="Doamin Job Request", compute="_compute_domain_job_request_ids")
    all_approve_ids = fields.Many2many("hr.job", "hr_job_approver_approval_rel", "apporve_line_id", "job_approve_id", string="All Approve", compute="_compute_all_approve", store="True")
    lines = fields.One2many("approval.line", "approve_id", string="Lines")
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('model_department_job_uniq', 'unique(model_ids, department_id, job_request_id)', 'The code of the job position must be unique in company!'),
    ]
    
    @api.depends("lines", "lines.job_approve_ids")
    def _compute_all_approve(self):
        for obj in self:
            all_approve_ids = self.env['hr.job']
            for line in obj.lines:
                all_approve_ids |= line.job_approve_ids
            obj.all_approve_ids = all_approve_ids
    
    @api.depends("department_id")
    def _compute_domain_contract_type(self):
        for obj in self:
            domain_contract_type_ids = self.env['hr.contract.type']
            if obj.department_id:
                job_position_ids = self.env['hr.job'].search([('department_id','=',obj.department_id.id)])
                domain_contract_type_ids = job_position_ids.mapped('contract_type_id')
            obj.domain_contract_type_ids = domain_contract_type_ids
    
    @api.depends("department_id","contract_type_id")
    def _compute_domain_job_request_ids(self):
        for obj in self:
            domain_job_request_ids = self.env['hr.job']
            if obj.department_id and obj.contract_type_id:
                domain_job_request_ids = self.env['hr.job'].search([('department_id','=',obj.department_id.id),('contract_type_id','=',obj.contract_type_id.id)])
            obj.domain_job_request_ids = domain_job_request_ids

                
    
    @api.depends("model_id","department_id","contract_type_id")
    def _compute_name(self):
        for obj in self:
            name = ''
            name_list = []
            if obj.model_ids:
                for model_id in obj.model_ids:
                    name_list.append(model_id.name)
            if obj.department_id:
                name_list.append(obj.department_id.name)
            if obj.contract_type_id:
                name_list.append(obj.contract_type_id.name)
            name = '/'.join(name_list)
            obj.name = name  
    
class ApprovalLine(models.Model):
    _name = "approval.line"

    approve_id = fields.Many2one("approval", index=True, ondelete='cascade', readonly=True, required=True)
    sequence = fields.Integer(string="Sequence")
    job_approve_ids = fields.Many2many("hr.job", "hr_job_approval_rel", "apporve_line_id", "job_id", string="Approvers", required=True)
    user_approve_ids = fields.Many2many("hr.employee", string="Users", compute="_compute_user_approve")
    
    @api.depends("job_approve_ids")
    def _compute_user_approve(self):
        for obj in self:
            user_approve_ids = self.env['hr.employee']
            if obj.job_approve_ids:
                user_approve_ids = self.env['hr.employee'].search([('job_id', 'in', obj.job_approve_ids.ids)])
            obj.user_approve_ids = user_approve_ids
            
    def unlink(self):
        for obj in self:
            ccpp_approve_line = self.env['ccpp.approve.line'].search([('approve_line_id','=',obj.id)])
            if ccpp_approve_line:
                raise UserError("ไม่สามารถลบ line นี้ได้เนื่องจากมีการนำไปใช้งานแล้ว กรุณา achieved แทน")
        res = super().unlink()
        return res