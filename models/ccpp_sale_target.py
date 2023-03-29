from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

STATUS_COLOR = {
    'over': 20,
    'similar': 3,
    'less': 23,
    'to_define': 0,
}

class CCPPSaleTarget(models.Model):
    _name = "ccpp.sale.target"
    _inherit = ['mail.thread']
    
    """def _get_default_date_from(self):
        if datetime.today().month in range(1,3):
            date_from = datetime.today().replace(day=1,month=1)
        if datetime.today().month in range(4,6):
            date_from = datetime.today().replace(day=1,month=4)
        if datetime.today().month in range(7,9):
            date_from = datetime.today().replace(day=1,month=7)
        if datetime.today().month in range(10,12):
            date_from = datetime.today().replace(day=1,month=9)
        return date_from """
    
    """def _get_default_date_to(self):
        if datetime.today().month in range(1,3):
            date_to = datetime.today().replace(day=31,month=3)
        if datetime.today().month in range(4,6):
            date_to = datetime.today().replace(day=30,month=6)
        if datetime.today().month in range(7,9):
            date_to = datetime.today().replace(day=30,month=9)
        if datetime.today().month in range(10,12):
            date_to = datetime.today().replace(day=31,month=12)
        return date_to """
    
    @api.model
    def default_get(self,fields):
        res = super(CCPPSaleTarget,self).default_get(fields)
        if 'sale_person_id' in fields:
            sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            if not sale_person_id:
                raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
            res['sale_person_id'] = sale_person_id.id
        if 'year_selection' in fields:
            current_year = datetime.today().year
            res['year_selection'] = str(current_year)
        if 'period' in fields:
            current_period = datetime.today().month
            if current_period in range(1,3):
                res['period'] = '1'
            if current_period in range(4,6):
                res['period'] = '2'
            if current_period in range(7,9):
                res['period'] = '3'
            if current_period in range(10,12):
                res['period'] = '4'
        return res
        
    def _get_default_job(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        #if not employee_id:
        #    print(self.env.user.name)
        #    raise UserError("Not recognize the Employee. Please Configure User to Employee to get the job")
        return employee_id.job_id
        
    name = fields.Char(string="Name")
    sale_period_id = fields.Many2one("ccpp.sale.target.period", string="Period")
    period = fields.Selection(selection=[
        ('1', 'Q1'),
        ('2', 'Q2'),
        ('3', 'Q3'),
        ('4', 'Q4'),
    ], required=True, string="Period")
    year_selection = fields.Selection(selection=[
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
        ('2026', '2026'),
        ('2027', '2027'),
        ('2028', '2028'),
        ('2029', '2029'),
        ('2030', '2030'),
        ('2031', '2031'),
        ('2032', '2032'),
        ('2033', '2033'),
        ('2034', '2034'),
        ('2035', '2035'),
        ('2036', '2036'),
        ('2037', '2037'),
        ('2038', '2038'),
        ('2039', '2039'),
        ('2040', '2040'),
        ('2041', '2041'),
        ('2042', '2042'),
        ('2043', '2043'),
        ('2044', '2044'),
        ('2045', '2045'),
        ('2046', '2046'),
        ('2047', '2047'),
        ('2048', '2048'),
        ('2049', '2049'),
        ('2050', '2050'),
        ('2051', '2051'),
        ('2052', '2052'),
        ('2053', '2053'),
        ('2054', '2054'),
        ('2055', '2055'),
        ('2056', '2056'),
        ('2057', '2057'),
        ('2058', '2058'),
        ('2059', '2059'),
        ('2060', '2060'),
        ('2061', '2061'),
        ('2062', '2062'),
        ('2063', '2063'),
        ('2064', '2064'),
        ('2065', '2065'),
        ('2066', '2066'),
        ('2067', '2067'),
        ('2068', '2068'),
        ('2069', '2069'),
        ('2070', '2070'),
        ('2071', '2071'),
        ('2072', '2072'),
        ('2073', '2073'),
    ], required=True, string="Year")
    date_from = fields.Date(string="Date From", readonly=True)
    date_to = fields.Date(string="Date To", readonly=True)
    target = fields.Float(string="Sales Target")
    actual = fields.Float(string="Sales Actual")
    actual_percent = fields.Float(string="% Success", compute="_compute_actual_percent", store=True)
    sale_person_id = fields.Many2one("hr.employee", related="job_id.employee_id", string="Sales Person", required=True)
    job_id = fields.Many2one("hr.job", string="Job Position",  default=_get_default_job, required=True, track_visibility="onchange")#default=_get_default_job,
    domain_job_ids = fields.Many2many("hr.job", string="Domain Job", compute="_compute_domain_job_ids")
    department_id = fields.Many2one("hr.department", string="Deparment", related="job_id.department_id")
    status = fields.Selection(selection=[
        ('over', 'Over'),
        ('similar', 'Similar'),
        ('less', 'Less than'),
        ('to_define', 'Undefine'),
    ], compute='_compute_status', store=True, readonly=False, string="Target Result")
    status_color = fields.Integer(string="Status Color", compute='_compute_status_color')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one("res.users", string="User", related="sale_person_id.user_id", store=True)
    
    #@api.model_create_multi
    #def create(self, vals_list):
    #    for vals in vals_list:
    #        status = 'to_define'
    #        if vals.get('target') and vals.get('actual'):
    #            if vals.get('actual') < vals.get('target'):
    #                status = 'less'
    #            elif vals.get('actual') > vals.get('target'):
    #                status = 'over'
    #            else:
    #                status = 'similar'
    #        if vals.get('target') and not vals.get('actual'):
    #            status = 'less'
    #        if not vals.get('target') and vals.get('actual'):
    #            status = 'over'
    #        vals['status'] = status
    #    res = super(CCPPSaleTarget, self).create(vals_list)
    #    return res
    
    @api.constrains('year_selection','period')
    def constrains_year_selection_period(self):
        for obj in self:
            if obj.period and obj.year_selection:
                quater_dict = {'1': 'Q1',
                               '2': 'Q2',
                               '3': 'Q3',
                               '4': 'Q4'}
                check_duplicate = self.env['ccpp.sale.target'].search([('id','!=',obj.id),
                                                                       ('sale_person_id','=',obj.sale_person_id.id),
                                                                       ('year_selection','=',obj.year_selection),
                                                                       ('period','=',obj.period),
                                                                       ])
                if check_duplicate:
                    raise UserError("Already have sales target in %s year %s"%(quater_dict[obj.period],obj.year_selection))
    
    @api.onchange('year_selection','period')
    def onchange_year_period(self):
        for obj in self:
            if obj.year_selection and obj.period:
                if obj.period == '1':
                    date_from_str = '%s-01-01'%obj.year_selection
                    date_to_str = '%s-03-31'%obj.year_selection
                if obj.period == '2':
                    date_from_str = '%s-04-01'%obj.year_selection
                    date_to_str = '%s-06-30'%obj.year_selection
                if obj.period == '3':
                    date_from_str = '%s-07-01'%obj.year_selection
                    date_to_str = '%s-09-30'%obj.year_selection
                if obj.period == '4':
                    date_from_str = '%s-10-01'%obj.year_selection
                    date_to_str = '%s-12-31'%obj.year_selection
                
                obj.date_from = date_from_str
                obj.date_to = date_to_str
    
    @api.depends('target','actual')
    def _compute_actual_percent(self):
        for obj in self:
            if obj.actual and obj.target:
                obj.actual_percent = obj.actual / obj.target * 100
    
    @api.depends('target','actual')
    def _compute_status(self):
        for obj in self:
            if obj.actual < obj.target:
                obj.status = 'less'
            if obj.actual > obj.target:
                obj.status = 'over'
            if obj.actual == obj.target:
                obj.status = 'similar'
            if not obj.actual and not obj.target:
                obj.status = 'to_define'
            """
            if obj.target and obj.actual:
                if obj.actual < obj.target:
                    obj.status = 'less'
                if obj.actual > obj.target:
                    obj.status = 'over'
                if obj.actual == obj.target:
                    obj.status = 'similar'
            elif obj.target and not obj.actual:
                obj.status = 'less'
            elif not obj.target and obj.actual:
                obj.status = 'over'
            elif not obj.target and not obj.actual:
                obj.status = 'to_define'"""

    @api.depends('status')
    def _compute_status_color(self):
        for obj in self:
            obj.status_color = STATUS_COLOR[obj.status]
            
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        orderby = "year_selection desc"
        res = super(CCPPSaleTarget, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
            
    def action_sale_target_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_sale_target_action')
        department_id = self.env.user.employee_id.department_id
        sale_target_ids = self.env['ccpp.sale.target'].search([
                                                            ('department_id', '=', department_id.id),
                                                            ])
        action['domain'] = [('id','in',sale_target_ids.ids)]
        return action
    
    @api.depends("sale_person_id")
    def _compute_domain_job_ids(self):
        for obj in self:
            job_ids = self.env['hr.job']
            if obj.sale_person_id:
                for job_id in obj.sale_person_id.job_lines:
                    job_ids |= job_id
            obj.domain_job_ids = job_ids.ids