from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPCustomerInformation(models.Model):
    _name = "ccpp.customer.information"
    _inherit = ['mail.thread','portal.mixin','mail.activity.mixin']
    _description = "CCPP Customer Information"
    _order = "year_selection desc, potential_ranking asc"
    #_rec_name = "customer_name"

    #@api.model
    #def default_get(self,fields):
    #    res = super(CCPPCustomerInformation,self).default_get(fields)
    #    if 'sale_person_id' in fields:
    #        sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #        if not sale_person_id:
    #            raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")

    #@api.model
    #def default_get(self,fields):
    #    res = super(CCPPCustomerInformation,self).default_get(fields)
    #    if 'year_selection' in fields:
    #        current_year = datetime.today().year
    #        res['year_selection'] = str(current_year)

    def _get_default_job(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        #if not employee_id:
            #print(self.env.user.name)
            #raise UserError("Not recognize the Employee. Please Configure User to Employee to get the job")
        return employee_id.job_id

    def _get_default_sale_person(self):
        sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        if not sale_person_id:
            raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
        return sale_person_id
    
    def _get_default_color(self):
        return randint(1, 11)
    
    def _get_default_date_from(self):
        date_from = datetime.today()
        return date_from
    
    def _get_default_date_to(self):
        date_to = datetime.today().replace(day=31,month=12)
        return date_to
    
    def _get_default_year_selection(self):
        year = datetime.today().year
        return str(year)
    
    def _get_default_type(self):
        if self._context.get('default_type'):
            default_type = self._context.get('default_type')
        else:
            default_type = 'customer'
        return default_type
    
    def _get_default_customer(self):
        customer_id = self.env['res.partner']
        if self._context.get('default_my_company'):
            customer_id = self.env.user.company_id.partner_id
        return customer_id

    def _get_default_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    date_from = fields.Date("From", required=True, default=_get_default_date_from, tracking=True)
    date_to = fields.Date("To", required=True, default=_get_default_date_to)
    customer_id = fields.Many2one("res.partner", string="Customer", default=_get_default_customer, tracking=True)
    domain_customer_ids = fields.Many2many("res.partner", string="Domain Customer", compute="_compute_domain_customer_ids")
    partner_id = fields.Many2one("res.partner", string="Contact", tracking=True)
    partner_ids = fields.Many2many("res.partner", string="Contact", tracking=True)
    domain_partner_ids = fields.Many2many("res.partner", string="Domain partner", compute="_compute_domain_partner_ids")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    sale_person_id = fields.Many2one("hr.employee", string="Sales Person", default=_get_default_employee, required=True, store=True, tracking=True)
    department_id = fields.Many2one("hr.department",string="Department", related="sale_person_id.department_id", store=True, tracking=True)
    division_id = fields.Many2one("hr.department",string="Department", related="sale_person_id.division_id", store=True, tracking=True)
    job_id = fields.Many2one("hr.job", string="Job Position", default=_get_default_job, required=True, tracking=True)#default=_get_default_job, 
    domain_job_ids = fields.Many2many("hr.job", string="Domain Job", compute="_compute_domain_job_ids")
    user_id = fields.Many2one("res.users", string="User", related="sale_person_id.user_id", store=True, tracking=True)
    province_id = fields.Many2one("ccpp.province", string="Province", related="customer_id.province_id", store=True)
    sale_area_id = fields.Many2one("hr.work.location", string="Sales Area", related="sale_person_id.work_location_id", store=True, tracking=True)
    potential_ranking = fields.Integer(string="Potential in Area Rank", group_operator=False, tracking=True)
    competitor_ranking = fields.Integer(string="Competitor's Sales Rank", group_operator=False, tracking=True)
    actual_sale_ranking = fields.Integer(string="Winmed Actual Sales Rank", compute="_compute_actual_sale_ranking", store=True, group_operator=False, tracking=True)
    total_sale_revenue = fields.Float(string="Total Sale Revenue Last Year(THB)", default=0.0, tracking=True)
    customer_category_id = fields.Many2one("ccpp.customer.category", string="Customer Category", related="customer_id.customer_category_id", store=True)
    hospital_size = fields.Integer(string="Hospital Size", tracking=True)
    customer_budget_id = fields.Many2one("ccpp.customer.budget",string="Funding/Budget",tracking=True)
    is_other_budget = fields.Boolean("Is Other Funding/Budget")
    budget = fields.Char(string="Other Funding/Budget")
    future_plan = fields.Text(string="Future Project/Plan")
    connection = fields.Text(string="Connection with other hospital")
    note = fields.Text(string="Note")
    #actual_sale = fields.Float(string="Actual Sale")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    #year_text = fields.Char(string="Year", compute="_compute_year_text", store=True)
    company_name = fields.Char(string="Company Name")
    state = fields.Selection(selection=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], default='active', string="Status", compute="_compute_state", store=True, tracking=True) 
    type = fields.Selection(selection=[
        ('customer','Customer'),
        ('internal','Internal'),
        ('external','External'),
    ], default=_get_default_type, string="Type")
    year_selection = fields.Selection(selection=[
        ('2013', '2013'),
        ('2014', '2014'),
        ('2015', '2015'),
        ('2016', '2016'),
        ('2017', '2017'),
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022'),
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
    ], required=True, string="Year", default=_get_default_year_selection, tracking=True)
    year_text = fields.Char("Year")
    is_customer = fields.Boolean(string="Customer", compute="_compute_customer_type", store=True)
    is_potential = fields.Boolean(string="Potential", compute="_compute_customer_type", store=True)
    is_company_group = fields.Boolean(string="Is Company Group", compute="_compute_is_company_group")
    
    @api.depends("customer_id")
    def _compute_is_company_group(self):
        for obj in self:
            is_company_group = False
            partner_ids = self.env['res.company'].sudo().search([]).mapped('partner_id')
            if obj.customer_id in partner_ids:
                is_company_group = True
            obj.is_company_group = is_company_group
            
    
    @api.depends("customer_id")
    def _compute_domain_partner_ids(self):
        for obj in self:
            partner_ids = self.env['res.partner']
            if obj.customer_id:
                for child_id in obj.customer_id.child_ids:
                    if child_id != obj.sale_person_id.work_contact_id:
                        partner_ids |= child_id
            obj.domain_partner_ids = partner_ids.ids
            
    @api.depends("sale_person_id")
    def _compute_domain_job_ids(self):
        for obj in self:
            job_ids = self.env['hr.job']
            if obj.sale_person_id:
                for job_id in obj.sale_person_id.job_id:
                    job_ids |= job_id
            obj.domain_job_ids = job_ids.ids
            
    @api.depends("customer_id")
    def _compute_domain_customer_ids(self):
        for obj in self:
            customer_ids = self.env['res.company'].search([]).mapped('partner_id')
            obj.domain_customer_ids = customer_ids.ids
            
    @api.depends("customer_id")
    def _compute_customer_type(self):
        for obj in self:
            is_customer = False
            is_potential = False
            if obj.customer_id:
                if obj.customer_id.is_customer:
                    is_customer = True
                if obj.customer_id.is_potential:
                    is_potential = True
            obj.is_customer = is_customer
            obj.is_potential = is_potential        
    
    @api.constrains('potential_ranking','competitor_ranking',"customer_id","year_selection")
    def constraint_customer(self):
        for obj in self:
            customer_potential_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                    ("year_selection",'=',obj.year_selection),
                                                                                    ("type",'=',obj.type),
                                                                                    ('potential_ranking','=',obj.potential_ranking),
                                                                                    ('potential_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            customer_competitor_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                     ("year_selection",'=',obj.year_selection),
                                                                                     ("type",'=',obj.type),
                                                                                    ('competitor_ranking','=',obj.competitor_ranking),
                                                                                    ('competitor_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            if obj.type == 'customer':
                check_customer_date_from = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                ('id','!=',obj.id),
                                                                                ("type",'=',obj.type),
                                                                                ('customer_id','=',obj.customer_id.id),
                                                                                ('year_selection','=',obj.year_selection),
                                                                                ],limit=1)
            elif obj.type in ['external','internal']:
                check_customer_date_from = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                ('id','!=',obj.id),
                                                                                ("type",'=',obj.type),
                                                                                ('customer_id','=',obj.customer_id.id),
                                                                                ('partner_id','=',obj.partner_id.id),
                                                                                ('year_selection','=',obj.year_selection),
                                                                                ],limit=1)
            #check_customer_date_to = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
            #                                                                ('id','!=',obj.id),
            #                                                                ('customer_id','=',obj.customer_id.id),
            #                                                                ],limit=1)
            if customer_potential_rank and obj.potential_ranking:
                raise UserError("Potential Ranking Must be Unique")
            if customer_competitor_rank and obj.competitor_ranking:
                raise UserError("Competitor Ranking Must be Unique")
            if check_customer_date_from:# or check_customer_date_to:
                #date_from = str(check_customer_date_from.date_from).split('-')
                #date_from = date_from[2] + '/' + date_from[1] + '/' + date_from[0]
                #date_to = str(check_customer_date_from.date_to).split('-')
                #date_to = date_to[2] + '/' + date_to[1] + '/' + date_to[0]
                #date_from_obj = str(obj.date_from).split('-')
                #date_from_obj = date_from_obj[2] + '/' + date_from_obj[1] + '/' + date_from_obj[0]
                #date_to_obj = str(obj.date_to).split('-')
                #date_to_obj = date_to_obj[2] + '/' + date_to_obj[1] + '/' + date_to_obj[0]
                raise UserError("Already have configure customer %s in year %s"%(obj.customer_id.name,obj.year_selection))
                #if check_customer_date_to:
                #    date_from = str(check_customer_date_to.date_from).split('-')
                #    date_from = date_from[2] + '/' + date_from[1] + '/' + date_from[0]
                #    date_to = str(check_customer_date_to.date_to).split('-')
                #    date_to = date_to[2] + '/' + date_to[1] + '/' + date_to[0]
                #    date_from_obj = date_from_obj[2] + '/' + date_from_obj[1] + '/' + date_from_obj[0]
                #    date_to_obj = str(obj.date_to).split('-')
                #    date_to_obj = date_to_obj[2] + '/' + date_to_obj[1] + '/' + date_to_obj[0]
                #    raise UserError("Configure customer %s period %s - %s overlap with period %s - %s"%(obj.customer_id.name,date_from_obj,date_to_obj,date_from,date_to))
                    
    #@api.onchange("date_from","date_to")
    #def onchange_date_from_to(self):
    #    for obj in self:
    #        if obj.date_from > obj.date_to:
    #            raise UserError("Please set date from not over date to")
    
    @api.onchange("date_from")
    def onchange_date_from_to(self):
        for obj in self:
            if obj.date_from:
                year = str(obj.date_from.year)
                obj.year_selection = year
  
    @api.depends("year_selection","customer_id")
    def _compute_state(self):
        for obj in self:
            name = obj.year_selection + ' ' + obj.customer_id.name
            obj.name = name
            
    
    @api.depends("active")
    def _compute_state(self):
        for obj in self:
            if obj.active:
                obj.state = 'active'
            else:
                obj.state = 'inactive'
    
    @api.depends("total_sale_revenue")
    def _compute_actual_sale_ranking(self):
        for obj in self:
            customer_info_ids = self.env["ccpp.customer.information"].search([('year_selection','=',obj.year_selection),
                                                                              ("sale_person_id",'=',obj.sale_person_id.id),
                                                                              ("type",'=',obj.type),
                                                                              ("total_sale_revenue",'!=',False),
                                                                              ],order="total_sale_revenue desc, date_from")
            customer_info_norank_ids = self.env["ccpp.customer.information"].search([('year_selection','=',obj.year_selection),
                                                                              ("sale_person_id",'=',obj.sale_person_id.id),
                                                                              ("type",'=',obj.type),
                                                                              ("total_sale_revenue",'=',False),
                                                                              ],order="date_from desc")
            
            rank = 1
            for info in customer_info_ids:
                info.actual_sale_ranking = rank
                rank += 1 
                
            for info_norank in customer_info_norank_ids:
                info_norank.actual_sale_ranking = rank
                rank += 1
            #if obj.id in customer_info_ids:
            #    rank = customer_info_ids.index(obj.id) + 1
            #    obj.actual_sale_ranking = rank
            #else:
            #    obj.actual_sale_ranking = False
            
    def button_active(self):
        for obj in self:
            obj.state = "active"
            
    def button_inactive(self):
        for obj in self:
            obj.state = "inactive"
    
    def button_to_open(self):
        for obj in self:
            obj.state = "open"
            
    def open_sales_target(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_sale_target_action')
        sales_target_ids = self.env['ccpp.sale.target'].search([('sale_person_id','=',self.sale_person_id.id)])
        action['domain'] = [('id', 'in', sales_target_ids.ids)]
        return action
    
    def open_plan_task(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.act_rocker_timesheet_calendar')
        action['context'] = {'default_customer_id': self.customer_id}
        return action
    
    def open_purchase_history(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        purchase_history_ids = self.env['ccpp.purchase.history'].search([('sale_person_id','=',self.sale_person_id.id),('customer_id','=',self.customer_id.id)])
        action['domain'] = [('id', 'in', purchase_history_ids.ids)]
        action['context'] = {}
        return action
            
    def open_ccpp(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.action_my_ccpp_group_by_priority')
        ccpp_ids = self.env['project.project']
        if self.type == 'customer':
            ccpp_ids = self.env['project.project'].search([('employee_ids','in',[self.sale_person_id.id]),('partner_id','=',self.customer_id.id),('partner_contact_id','in',self.partner_ids.ids)])
        elif self.type in ['internal','external']:
            ccpp_ids = self.env['project.project'].search([('employee_ids','in',[self.sale_person_id.id]),('partner_id','=',self.customer_id.id),('partner_contact_id','=',self.partner_id.id)])
        action['domain'] = [('id', 'in', ccpp_ids.ids)]
        return action
    
    def open_current_situation(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.act_rocker_timesheet_tree')
        update_ids = self.env['account.analytic.line'].search([('sale_person_id','=',self.sale_person_id.id),('customer_id','=',self.customer_id.id)])
        action['domain'] = [('id', 'in', update_ids.ids)]
        action['context'] = {}
        return action
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        orderby = "year_selection desc, potential_ranking asc"
        res = super(CCPPCustomerInformation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
    
    def action_customer_information_user(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = self.env['ccpp.customer.information'].search([('type','=','customer'),
                                                                ('sale_person_id', '=', employee_id.id),
                                                                ('company_id','in', company_ids),
                                                                ])
        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    # def action_customer_information_manager(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     job_ids = self.get_child_job(employee_id.job_lines)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','customer'),
    #                                                             ('job_id', 'in', job_ids.ids),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_customer_information_manager_all_department(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','customer'),
    #                                                             ('department_id', '=', employee_id.department_id.id),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_customer_information_ceo(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','customer'),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    def action_external_information_user(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = self.env['ccpp.customer.information'].search([('type','=','external'),
                                                                ('sale_person_id', '=', employee_id.id),
                                                                ('company_id','in', company_ids),
                                                                ])
        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    # def action_external_information_manager(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     job_ids = self.get_child_job(employee_id.job_lines)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','external'),
    #                                                             ('job_id', 'in', job_ids.ids),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_external_information_manager_all_department(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','external'),
    #                                                             ('department_id', '=', employee_id.department_id.id),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_external_information_ceo(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','external'),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    def action_internal_information_user(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = self.env['ccpp.customer.information'].search([('type','=','internal'),
                                                                ('sale_person_id', '=', employee_id.id),
                                                                ('company_id','in', company_ids),
                                                                ])
        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    # def action_internal_information_manager(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     job_ids = self.get_child_job(employee_id.job_lines)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','internal'),
    #                                                             ('job_id', 'in', job_ids.ids),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_internal_information_manager_all_department(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','internal'),
    #                                                             ('department_id', '=', employee_id.department_id.id),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    # def action_internal_information_ceo(self):
    #     self = self.sudo()
    #     company_ids = self._context.get('allowed_company_ids')
    #     action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
    #     employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #     information_ids = self.env['ccpp.customer.information'].search([('type','=','internal'),
    #                                                             ('company_id','in', company_ids),
    #                                                             ])
    #     action['domain'] = [('id','in',information_ids.ids)]
    #     return action
    
    def get_child_job(self,job_lines,job_ids=False):
        if not job_ids:
            job_ids = self.env['hr.job']
        for job_id in job_lines:
            job_ids |= job_id
            job_ids |= self.get_child_job(job_id.child_lines, job_ids)   
        return job_ids
    
    @api.model
    def retrieve_dashboard_internal(self,context={}):
        result = {
            'my_customer': 0,
            'all_customer': 0,
        }
        
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        customer_information = self.env['ccpp.customer.information']
        employee_ids = self.get_child_job(employee_id.job_id).mapped("employee_ids")
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_user') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_user'):
            result['my_customer'] = customer_information.search_count([('type','=','internal'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','internal'),
                                                                        ('sale_person_id', '=', employee_id.id),
                                                                        ('company_id','in', company_ids)])
        
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager'):
            result['my_customer'] = customer_information.search_count([('type','=','internal'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','internal'),
                                                                        ('sale_person_id', 'in', employee_ids.ids),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
            result['my_customer'] = customer_information.search_count([('type','=','internal'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','internal'),
                                                                        ('department_id', '=', employee_id.department_id.id),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_ceo'):
            result['my_customer'] = customer_information.search_count([('type','=','internal'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','internal'),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        
        return result
    
    @api.model
    def retrieve_dashboard_external(self,context={}):
        result = {
            'my_customer': 0,
            'all_customer': 0,
        }
        
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        customer_information = self.env['ccpp.customer.information']
        employee_ids = self.get_child_job(employee_id.job_id).mapped("employee_ids")
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_user') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_user'):
            result['my_customer'] = customer_information.search_count([('type','=','external'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','external'),
                                                                        ('sale_person_id', '=', employee_id.id),
                                                                        ('company_id','in', company_ids)])
        
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager'):
            result['my_customer'] = customer_information.search_count([('type','=','external'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','external'),
                                                                        ('sale_person_id', 'in', employee_ids.ids),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
            result['my_customer'] = customer_information.search_count([('type','=','external'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','external'),
                                                                        ('department_id', '=', employee_id.department_id.id),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_ceo'):
            result['my_customer'] = customer_information.search_count([('type','=','external'),
                                                                       ('sale_person_id', '=', employee_id.id),
                                                                       ('company_id','in', company_ids)])
            result['all_customer'] = customer_information.search_count([('type','=','external'),
                                                                        ('company_id','in', company_ids),
                                                                            ])
        
        return result
    
    
    @api.model
    def set_my_customer_internal(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = self.env['ccpp.customer.information'].search([('type','=','internal'),
                                                                ('sale_person_id', '=', employee_id.id),
                                                                ('company_id','in', company_ids),
                                                                ])
        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    @api.model
    def set_all_customer_internal(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_internal_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = customer_information = self.env['ccpp.customer.information']
        employee_ids = self.get_child_job(employee_id.job_id).mapped("employee_ids")
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_user') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_user'):
            information_ids= customer_information.search([('type','=','internal'),
                                                        ('sale_person_id', '=', employee_id.id),
                                                        ('company_id','in', company_ids)])
        
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager'):
            information_ids = customer_information.search([('type','=','internal'),
                                                            ('sale_person_id', 'in', employee_ids.ids),
                                                            ('company_id','in', company_ids),
                                                        ])
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
            information_ids = customer_information.search([('type','=','internal'),
                                                            ('department_id', '=', employee_id.department_id.id),
                                                            ('company_id','in', company_ids),
                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_ceo'):
            information_ids = customer_information.search([('type','=','internal'),
                                                            ('company_id','in', company_ids),
                                                        ])

        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    @api.model
    def set_my_customer_external(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = self.env['ccpp.customer.information'].search([('type','=','external'),
                                                                ('sale_person_id', '=', employee_id.id),
                                                                ('company_id','in', company_ids),
                                                                ])
        action['domain'] = [('id','in',information_ids.ids)]
        return action
    
    @api.model
    def set_all_customer_external(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_external_information_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        information_ids = customer_information = self.env['ccpp.customer.information']
        employee_ids = self.get_child_job(employee_id.job_id).mapped("employee_ids")
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_user') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_user'):
            information_ids= customer_information.search([('type','=','external'),
                                                        ('sale_person_id', '=', employee_id.id),
                                                        ('company_id','in', company_ids)])
        
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager'):
            information_ids = customer_information.search([('type','=','external'),
                                                            ('sale_person_id', 'in', employee_ids.ids),
                                                            ('company_id','in', company_ids),
                                                        ])
        if self.env.user.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
            information_ids = customer_information.search([('type','=','external'),
                                                            ('department_id', '=', employee_id.department_id.id),
                                                            ('company_id','in', company_ids),
                                                            ])
        if self.env.user.has_group('ccpp.group_ccpp_ceo'):
            information_ids = customer_information.search([('type','=','external'),
                                                            ('company_id','in', company_ids),
                                                        ])

        action['domain'] = [('id','in',information_ids.ids)]
        return action