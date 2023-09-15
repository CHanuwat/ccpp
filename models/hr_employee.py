from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"
    
    job_lines = fields.One2many("hr.job", 'employee_id', string="Job Lines")
    division_id = fields.Many2one("hr.department", string="Division")
    domain_division_ids = fields.Many2many("hr.department", string="Domain Division", compute="_compute_domain_division")
    timeoff_approve_user = fields.Char(string="Timeoff Approve User", compute="_compute_timeoff_approve_user")
    timeoff_approve_job = fields.Char(string="Timeoff Approve Job", compute="_compute_timeoff_approve_user")
    
    
    def unlink(self):
        raise UserError("ระบบไม่สามารถข้อมูลพนักงานได้")
        res = super().unlink()
    
    @api.depends('department_id')
    def _compute_domain_division(self):
        for obj in self:
            domain_division_ids = self.env['hr.department']
            if obj.department_id:
                domain_division_ids = obj.department_id.child_ids
            obj.domain_division_ids = domain_division_ids
        
    @api.constrains('name')
    def _constrains_name(self):
        for obj in self:
            if obj.name:
                employee_duplicate = self.env['hr.employee'].search([('id','!=',obj.id),('name','=',obj.name)],limit=1)
                if employee_duplicate:
                    raise ValidationError(_("Employee name must be unique"))
                
    def _inverse_work_contact_details(self):
        for employee in self:
            job_id = employee.job_id
            job_position_id = self.env['res.partner.position'].search([('name','=',job_id.name),('type','=','internal')],limit=1)
            if not job_position_id:
                job_position_id = self.env['res.partner.position'].sudo().create({
                    'name': job_id.name,
                    'type': 'internal',
                })
            if not employee.work_contact_id:
                employee.work_contact_id = self.env['res.partner'].sudo().create({
                    'email': employee.work_email,
                    'mobile': employee.mobile_phone,
                    'name': employee.name,
                    'image_1920': employee.image_1920,
                    'company_id': employee.company_id.id,
                    'parent_id': employee.address_id.id,
                    'job_position_id': job_position_id.id,
                    'is_employee': True,
                })
            else:
                employee.work_contact_id.sudo().write({
                    'email': employee.work_email,
                    'mobile': employee.mobile_phone,
                    'parent_id': employee.address_id.id,
                    'job_position_id': job_position_id.id,
                    'is_employee': True,
                })
                
    def write(self, vals):
        if 'job_id' in vals:
            partner_id = self.work_contact_id
            job_id = self.env['hr.job'].browse(vals['job_id'])
            job_position_id = self.env['res.partner.position'].search([('name','=',job_id.name),('type','=','internal')],limit=1)
            if not job_position_id:
                job_position_id = self.env['res.partner.position'].sudo().create({
                    'name': job_id.name,
                    'type': 'internal',
                })
            partner_id.job_position_id = job_position_id.id
            partner_id.parent_id = self.address_id.id
            partner_id.is_employee = True
        res = super(HrEmployeePrivate, self).write(vals)
        return res
    
    @api.onchange('job_lines','job_lines.employee_id')
    def onchange_employee(self):
        for obj in self:
            if obj.job_lines:
                if obj.job_lines.ids < obj._origin.job_lines.ids:
                    continue
                new_line = []
                for i in obj.job_lines.ids:
	                if i not in obj._origin.job_lines.ids:
		                new_line.append(i)
                print("Max"*100)
                print(obj.job_lines.ids)
                print(obj._origin.job_lines.ids)
                if not new_line:
                    continue
                new_line_id = self.env['hr.job'].browse(new_line[0])
                job_position_id = self.env['res.partner.position'].search([('name','=',new_line_id.name),('type','=','internal')],limit=1)
                if not job_position_id:
                    job_position_id = self.env['res.partner.position'].sudo().create({
                        'name': new_line_id.name,
                        'type': 'internal',
                    })
                obj.work_contact_id.job_position_id = job_position_id
            else:
                obj._origin.work_contact_id.job_position_id = False

    def _compute_timeoff_approve_user(self):
        for obj in self:
            approve_name = ''
            approve_job = ''
            model_id = self.env['ir.model'].sudo().search([('model','=','hr.leave')])
            approve_ids = self.env['approval'].search([('model_ids','in', model_id.ids),
                                                        ('department_id','=', obj.department_id.id),
                                                        ('contract_type_id','=', obj.job_id.contract_type_id.id),
                                                        ('contract_type_id','!=', False)])
            # ใช้กับพนักงานที่มีdivision_id
            if not approve_ids:
                approve_ids = self.env['approval'].search([('model_ids','in', model_id.ids),
                                                        ('department_id','=', obj.department_id.id),
                                                        ('division_id','=', obj.division_id.id),
                                                        ('division_id','!=', False)])
            # ใช้กับพนักงาน
            if not approve_ids:
                approve_ids = self.env['approval'].search([('model_ids','in', model_id.ids),
                                                        ('department_id','=', obj.department_id.id),
                                                        ('division_id','=', False),
                                                        ('contract_type_id','=', False),])
            for approve_id in approve_ids:
                for approve_line in approve_id.lines:
                    for job_id in approve_line.job_approve_ids:
                        approve_job += job_id.name
                        for employee_id in job_id.employee_ids:
                            approve_name += employee_id.name

            obj.timeoff_approve_user = approve_name
            obj.timeoff_approve_job = approve_job
    

# class HrExpense(models.Model):
#     _inherit = "hr.expense"
    
#     @api.model
#     def _default_employee_id(self):
#         employee = self.env.user.employee_id
#         #if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
#             #raise ValidationError(_('The current user has no related employee. Please, create one.'))
#         return employee