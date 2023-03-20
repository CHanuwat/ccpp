from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"
    
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

