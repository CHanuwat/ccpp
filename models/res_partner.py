from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from odoo.osv import expression

class Partner(models.Model):
    _inherit = "res.partner"
    
    def _get_default_potential(self):
        if self._context.get('create_potential') or self._context.get('create_external_customer') or self._context.get('create_external_contact') or self._context.get('create_customer_contact'):
            is_potential = True
        else:
            is_potential = False
        return is_potential
    
    def _get_default_is_company(self):
        if self._context.get('create_potential') or self._context.get('create_external_customer'):
            is_company = True
        else:
            is_company = False
        return is_company
    
    #def _get_default_is_customer(self):
    #    if  self._context.get('create_external_contact') or self._context.get('create_customer_contact'):
    #        is_customer = True
    #    else:
    #        is_customer = False
    #    return is_customer
    
    def _get_default_parent_id(self):
        parent_id = self.env['res.partner']
        if self._context.get('create_external_contact'):
            if self._context.get('external_parent'):
                parent_id = self._context.get('external_parent')
                partner_id = self.env['res.partner'].browse(parent_id)
                if partner_id.company_type == 'person':
                    parent_id = self.env['res.partner']
        if self._context.get('create_customer_contact'):
            if self._context.get('customer_parent'):
                parent_id = self._context.get('customer_parent')
                partner_id = self.env['res.partner'].browse(parent_id)
                if partner_id.company_type == 'person':
                    parent_id = self.env['res.partner']
        return parent_id
    
    job_position_id = fields.Many2one('res.partner.position', string='Job Position', index=True, copy=False ,help="replace instead function field char")
    province_id = fields.Many2one('ccpp.province', string="Province")
    customer_category_id = fields.Many2one('ccpp.customer.category', string="Customer Category")
    is_customer = fields.Boolean(string="Customer")#default=_get_default_is_customer
    is_vendor = fields.Boolean(string="Vendor", default=False)
    is_competitor = fields.Boolean(string="Competitor", default=False)
    is_potential = fields.Boolean(string="Potential", default=_get_default_potential)
    is_employee = fields.Boolean(string="Employeee", default=False)
    potential_ranking = fields.Integer(string="Potential rank by user", compute="_compute_potential_rank")
    department_code = fields.Char(string="Department Code", compute="_compute_department_code")
    is_company = fields.Boolean(default=_get_default_is_company)
    parent_id = fields.Many2one(default=_get_default_parent_id)
    job_position_name = fields.Char(string="Job Position Name", related="job_position_id.name", store=True)
    
    #@api.model_create_multi
    #def create(self, vals_list):
    #    for vals in vals_list:
    #        if self._context.get("create_external"):
    #            vals['is_customer'] = True
    #            vals['company_type'] = 'company'
    #            vals['company_type'] = 'person'
    #    res = super(Partner, self).create(vals_list)
   
    def _compute_potential_rank(self):
        for obj in self:
            year = str(datetime.now().year)
            customer_info = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id),
                                                                          ('customer_id','=',obj.id),
                                                                          ('year_selection','=',year),
                                                                          ('type','=','customer')], limit=1)
            obj.potential_ranking = customer_info.potential_ranking
                    
    def _compute_department_code(self):
        for obj in self:
            department_code = ''
            employee_id = self.env['hr.employee'].search([('work_contact_id','=',obj.id)],limit=1)
            department_code = employee_id.department_id.code
            obj.department_code = department_code

    def name_get(self):
        #res = []
        #for partner in self:
        #    name = partner._get_name()
        #    res.append((partner.id, name))
        res = super(Partner, self).name_get()
        if self._context.get("show_title_position", False):
            res = []
            for obj in self:
                new_name_list = []
                if obj.department_code:
                    new_name_list.append(obj.department_code)
                if obj.title:
                    new_name_list.append(obj.title.name)
                if obj.name:
                    new_name_list.append(obj.name)
                if obj.function:
                    new_name_list.append(obj.function)
                if obj.job_position_id:
                    new_name_list.append(obj.job_position_id.name)
                new_name = ', '.join(new_name_list)
                res.append((obj.id, new_name))
                obj.display_name = new_name
        if self._context.get("show_rank", False):
            res = []
            for obj in self:     
                year = str(datetime.now().year)           
                customer_info = self.env['ccpp.customer.information'].search([('customer_id','=',obj.id),
                                                                              ('active','=',True),
                                                                              ('year_selection','=',year),
                                                                              ('type','=','customer')],limit=1)
                new_name_list = []
                if customer_info.potential_ranking:
                    new_name_list.append('Rank' + str(customer_info.potential_ranking))
                if obj.name:
                    new_name_list.append(obj.name)
                new_name = ' '.join(new_name_list)
                res.append((obj.id, new_name))
        return res
    
    #@api.model
    #def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        #domain = [('job_position_name', operator, name)]
    #    domain = []
    #    if name:
    #        domain = ['|',('name', operator, name),('job_position_name', operator, name)]
            #domain.append(('job_position_name', operator, name))
    #    return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
    
    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'job_position_id')
    def _compute_display_name(self):
        # retrieve name_get() without any fancy feature
        names = dict(self.with_context({}).name_get())
        res = super(Partner, self)._compute_display_name()
        for obj in self:
            if obj.parent_id:
                new_name_list = []
                if obj.title:
                    new_name_list.append(obj.title.name)
                if obj.name:
                    new_name_list.append(obj.name)
                if obj.function:
                    new_name_list.append(obj.function)
                if obj.job_position_id:
                    new_name_list.append(obj.job_position_id.name)
                new_name = ', '.join(new_name_list)
                obj.display_name = new_name
                
    @api.constrains('name')
    def _constrains_name(self):
        for obj in self:
            if obj.name:
                partner_duplicate = self.env['res.partner'].search([('id','!=',obj.id),('name','=',obj.name)],limit=1)
                if partner_duplicate:
                    raise ValidationError(_("Contact name must be unique"))
                
class PartnerPosition(models.Model):
    _name = "res.partner.position"
    
    name = fields.Char("Position Name", required=True)
    type = fields.Selection([
        ('external', 'External'),
        ('internal', 'Internal'),
    ], default='external', string="Position Type")
    parent_partner_id = fields.Many2one("res.partner", string="Position Of", domain=[('is_company','=',True)])
    partner_lines = fields.One2many('res.partner', 'job_position_id', string='Partner')
    active = fields.Boolean("Active", default=True)
    
    @api.constrains('name')
    def _constrains_name(self):
        for obj in self:
            if obj.name:
                position_duplicate = self.env['res.partner.position'].search([('id','!=',obj.id),('name','=',obj.name),('type','=',obj.type)],limit=1)
                if position_duplicate:
                    raise ValidationError(_("Job Postition name must be unique"))