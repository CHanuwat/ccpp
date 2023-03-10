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
        
    name = fields.Char("Name")
    date_from = fields.Date("From", required=True, default=_get_default_date_from)
    date_to = fields.Date("To", required=True, default=_get_default_date_to)
    customer_id = fields.Many2one("res.partner", string="Customer")
    active = fields.Boolean(string="Active", default=True)
    sale_person_id = fields.Many2one("hr.employee", string="Sales Person", default=_get_default_sale_person, required=True)
    user_id = fields.Many2one("res.users", string="User", related="sale_person_id.user_id", store=True)
    province_id = fields.Many2one("ccpp.province", string="Province", related="customer_id.province_id", store=True)
    sale_area_id = fields.Many2one("hr.work.location", string="Sales Area", related="sale_person_id.work_location_id", store=True)
    potential_ranking = fields.Integer(string="Ranking by Potential in Area", group_operator=False)
    competitor_ranking = fields.Integer(string="Ranking by Competitor's Sales", group_operator=False)
    actual_sale_ranking = fields.Integer(string="Ranking by Winmed Actual Sales", compute="_compute_actual_sale_ranking", store=True, group_operator=False)
    total_sale_revenue = fields.Float(string="Total Sale Revenue Last Year(THB)", default=0.0)
    customer_category_id = fields.Many2one("ccpp.customer.category", string="Customer Category", related="customer_id.customer_category_id", store=True)
    hospital_size = fields.Integer(string="Hospital Size")
    customer_budget_id = fields.Many2one("ccpp.customer.budget",string="Funding/Budget")
    is_other_budget = fields.Boolean("Is Other Funding/Budget")
    budget = fields.Char(string="Other Funding/Budget")
    future_plan = fields.Text(string="Future Project/Plan (??????????????????????????????????????????/??????????????????)")
    connection = fields.Text(string="Connection with other hospital (???????????????????????????????????????????????????????????????????????????????????????)")
    note = fields.Text(string="Note")
    #actual_sale = fields.Float(string="Actual Sale")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    #year_text = fields.Char(string="Year", compute="_compute_year_text", store=True)
    company_name = fields.Char(string="Company Name")
    state = fields.Selection(selection=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], default='active', string="Status") 
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
    ], required=True, string="Year", default=_get_default_year_selection)
    year_text = fields.Char("Year")
    
    @api.constrains('potential_ranking','competitor_ranking',"customer_id","year_selection")
    def constraint_customer(self):
        for obj in self:
            print("Y"*100)
            print(obj.date_from)
            print(obj.date_to)
            customer_potential_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                    ("year_selection",'=',obj.year_selection),
                                                                                    ('potential_ranking','=',obj.potential_ranking),
                                                                                    ('potential_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            customer_competitor_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                     ("year_selection",'=',obj.year_selection),
                                                                                    ('competitor_ranking','=',obj.competitor_ranking),
                                                                                    ('competitor_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            check_customer_date_from = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                            ('id','!=',obj.id),
                                                                            ('customer_id','=',obj.customer_id.id),
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
    
    @api.depends("total_sale_revenue")
    def _compute_actual_sale_ranking(self):
        for obj in self:
            customer_info_ids = self.env["ccpp.customer.information"].search([('year_selection','=',obj.year_selection),
                                                                              ("sale_person_id",'=',obj.sale_person_id.id),
                                                                              ("total_sale_revenue",'!=',False),
                                                                              ],order="total_sale_revenue desc")
            customer_info_norank_ids = self.env["ccpp.customer.information"].search([('year_selection','=',obj.year_selection),
                                                                              ("sale_person_id",'=',obj.sale_person_id.id),
                                                                              ("total_sale_revenue",'=',False),
                                                                              ],order="date_from asc")
            
            print(customer_info_ids)
            print(customer_info_norank_ids)
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
        sales_target_ids = self.env['ccpp.sale.target'].search([('user_id','=',self.user_id.id)])
        action['domain'] = [('id', 'in', sales_target_ids.ids)]
        return action
    
    def open_purchase_history(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        purchase_history_ids = self.env['ccpp.purchase.history'].search([('user_id','=',self.user_id.id),('customer_id','=',self.customer_id.id)])
        action['domain'] = [('id', 'in', purchase_history_ids.ids)]
        action['context'] = {}
        return action
            
    def open_ccpp(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project.open_view_project_all')
        ccpp_ids = self.env['project.project'].search([('user_id','=',self.user_id.id),('partner_id','=',self.customer_id.id)])
        action['domain'] = [('id', 'in', ccpp_ids.ids)]
        return action
    
    def open_current_situation(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_project_update_action')
        update_ids = self.env['project.update'].search([('user_id','=',self.user_id.id),('customer_id','=',self.customer_id.id)])
        action['domain'] = [('id', 'in', update_ids.ids)]
        return action
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        orderby = "year_selection desc, potential_ranking asc"
        res = super(CCPPCustomerInformation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res