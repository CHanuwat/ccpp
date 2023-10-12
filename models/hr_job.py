from email.policy import default
from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class Job(models.Model):
    _inherit = "hr.job"
    _order = "code"
    
    
    name = fields.Char(translate=False)
    code = fields.Char(string="Code", required=True, default="New")
    parent_id = fields.Many2one("hr.job", string="Parent Job Position")
    child_lines = fields.One2many("hr.job", 'parent_id', string="Child Job Position")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    division_id = fields.Many2one("hr.department", string="Division")
    domain_division_ids = fields.Many2many("hr.department", string="Domain Division", compute="_compute_domain_division")
    temp_approve_id = fields.Many2one("hr.employee", string="ผู้รักษาการแทน")
    # domain_parent_ids = fields.Many2many("hr.job", string="Domain Parent", compute="_compute_domain_parent")
    
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id, department_id)', 'The name of the job position must be unique per department in company!'),
        # ('name_company_uniq', 'unique(code, company_id)', 'The code of the job position must be unique in company!'),
        ('no_of_recruitment_positive', 'CHECK(no_of_recruitment >= 0)', 'The expected number of new employees must be positive.')
    ]
    
    # def unlink(self):
    #     raise UserError("ระบบไม่สามารถลบตำแหน่งได้")
    #     res = super().unlink()

    # @api.depends('department_id')
    # def _compute_domain_parent(self):
    #     for obj in self:
    #         domain_parent_ids = self.env['hr.job']
    #         if obj.department_id:
    #             domain_parent_ids = self.env['hr.job'].search([('department_id','=',obj.department_id.id)])
    #         obj.domain_parent_ids = domain_parent_ids

    @api.depends('department_id')
    def _compute_domain_division(self):
        for obj in self:
            domain_division_ids = self.env['hr.department']
            if obj.department_id:
                domain_division_ids = obj.department_id.child_ids
            obj.domain_division_ids = domain_division_ids
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        for obj in self:
            if obj.employee_id:
                job_position_id = self.env['res.partner.position'].search([('name','=',obj.name),('type','=','internal')],limit=1)
                if not job_position_id:
                    job_position_id = self.env['res.partner.position'].sudo().create({
                        'name': obj.name,
                        'type': 'internal',
                    })
                obj.employee_id.work_contact_id.job_position_id = job_position_id
            else:
                obj._origin.employee_id.work_contact_id.job_position_id = False
                
        

    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = []
        args = list(args or [])
        if name:
            domain = ['|', ('code', '=', name), ('name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
