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
    #_rec_name = "customer_name"

    #@api.model
    #def default_get(self,fields):
    #    res = super(CCPPCustomerInformation,self).default_get(fields)
    #    if 'sale_person_id' in fields:
    #        sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #        if not sale_person_id:
    #            raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")

    def _get_default_sale_person(self):
        sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        if not sale_person_id:
            raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
        return sale_person_id
    
    def _get_default_color(self):
        return randint(1, 11)
    
    def _get_default_date_from(self):
        date_from = datetime.today().replace(day=1,month=1)
        return date_from
    
    def _get_default_date_to(self):
        date_to = datetime.today().replace(day=31,month=12)
        return date_to
        
    name = fields.Char("Name")
    date_from = fields.Date("From", required=True, default=_get_default_date_from)
    date_to = fields.Date("To", required=True, default=_get_default_date_to)
    customer_id = fields.Many2one("res.partner", string="Customer", required=True)
    active = fields.Boolean(string="Active", default=True)
    sale_person_id = fields.Many2one("hr.employee", string="Sales Person", default=_get_default_sale_person, required=True)
    user_id = fields.Many2one("res.users", string="User", related="sale_person_id.user_id")
    province_id = fields.Many2one("ccpp.province", string="Province", related="customer_id.province_id")
    sale_area_id = fields.Many2one("hr.work.location", string="Sales Area", related="sale_person_id.work_location_id")
    potential_ranking = fields.Integer(string="Ranking by Potential in Area")
    competitor_ranking = fields.Integer(string="Ranking by Competitor's Sales")
    actual_sale_ranking = fields.Integer(string="Ranking by Winmed Actual Sales", compute="_compute_actual_sale_ranking", store=True)
    total_sale_revenue = fields.Float(string="Total Sale Revenue Last Year(THB)")
    customer_category_id = fields.Many2one("ccpp.customer.category", string="Customer Category", related="customer_id.customer_category_id")
    hospital_size = fields.Integer(string="Hospital Size")
    budget = fields.Float(string="Funding/Budget")
    future_plan = fields.Text(string="Future Project/Plan (โครงการในอนาคต/แผนงาน)")
    connection = fields.Text(string="Connection with other hospital (ความสัมพันธ์กับโรงพยาบาลอื่นๆ)")
    note = fields.Text(string="Note")
    #actual_sale = fields.Float(string="Actual Sale")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    @api.constrains('potential_ranking','competitor_ranking',"customer_id","date_from","date_to")
    def constraint_customer(self):
        for obj in self:
            print("Y"*100)
            print(obj.date_from)
            print(obj.date_to)
            customer_potential_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                    ('potential_ranking','=',obj.potential_ranking),
                                                                                    ('potential_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            customer_competitor_rank = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                                    ('competitor_ranking','=',obj.competitor_ranking),
                                                                                    ('competitor_ranking','!=',False),
                                                                                    ('id','!=',obj.id)],limit=1)
            check_customer_date_from = self.env["ccpp.customer.information"].search([("sale_person_id",'=',obj.sale_person_id.id),
                                                                            ('id','!=',obj.id),
                                                                            ('customer_id','=',obj.customer_id.id),
                                                                            ('date_from','<=',str(obj.date_to)),
                                                                            ('date_to','>=',str(obj.date_from)),
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
                if check_customer_date_from:
                    date_from = str(check_customer_date_from.date_from).split('-')
                    date_from = date_from[2] + '/' + date_from[1] + '/' + date_from[0]
                    date_to = str(check_customer_date_from.date_to).split('-')
                    date_to = date_to[2] + '/' + date_to[1] + '/' + date_to[0]
                    date_from_obj = str(obj.date_from).split('-')
                    date_from_obj = date_from_obj[2] + '/' + date_from_obj[1] + '/' + date_from_obj[0]
                    date_to_obj = str(obj.date_to).split('-')
                    date_to_obj = date_to_obj[2] + '/' + date_to_obj[1] + '/' + date_to_obj[0]
                    raise UserError("Configure customer %s period %s - %s overlap with period %s - %s"%(obj.customer_id.name,date_from_obj,date_to_obj,date_from,date_to))
                #if check_customer_date_to:
                #    date_from = str(check_customer_date_to.date_from).split('-')
                #    date_from = date_from[2] + '/' + date_from[1] + '/' + date_from[0]
                #    date_to = str(check_customer_date_to.date_to).split('-')
                #    date_to = date_to[2] + '/' + date_to[1] + '/' + date_to[0]
                #    date_from_obj = date_from_obj[2] + '/' + date_from_obj[1] + '/' + date_from_obj[0]
                #    date_to_obj = str(obj.date_to).split('-')
                #    date_to_obj = date_to_obj[2] + '/' + date_to_obj[1] + '/' + date_to_obj[0]
                #    raise UserError("Configure customer %s period %s - %s overlap with period %s - %s"%(obj.customer_id.name,date_from_obj,date_to_obj,date_from,date_to))
                    
    
    @api.depends("total_sale_revenue")
    def _compute_actual_sale_ranking(self):
        for obj in self:
            customer_info_ids = self.env["ccpp.customer.information"].search([('date_from','=',obj.date_from),
                                                                              ('date_to','=',obj.date_to),
                                                                              ("sale_person_id",'=',obj.sale_person_id.id)],order="total_sale_revenue desc")
            rank = 1
            for info in customer_info_ids:
                info.actual_sale_ranking = rank
                rank += 1 
            #if obj.id in customer_info_ids:
            #    rank = customer_info_ids.index(obj.id) + 1
            #    obj.actual_sale_ranking = rank
            #else:
            #    obj.actual_sale_ranking = False
            
    