from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPDashboard(models.Model):
    _name = "ccpp.dashboard"
    _description = "CCPP Dashboard"
    _inherit = ['mail.thread','portal.mixin','mail.activity.mixin']
    #_rec_name = "customer_name"

    #@api.model
    #def default_get(self,fields):
    #    res = super(CCPPCustomerInformation,self).default_get(fields)
    #    if 'sale_person_id' in fields:
    #        sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
    #        if not sale_person_id:
    #            raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
        
    name = fields.Char("Name")
    priority_id = fields.Many2one("ccpp.priority", string="CCPP Priority")
    ranking_type = fields.Selection(selection=[
        ('potential', 'Potential'),
        ('actual', 'Actual Sale'),
        ('competitor', 'Ranking by Competitor')
    ], string="Ranking Type")
    color = fields.Integer(string="Color")
    count_doc = fields.Integer(string="Count Document", compute="_compute_count_doc",store=False)
    
    def _compute_count_doc(self):
        for obj in self:
            count_doc = 0
            if obj.priority_id:
                ccpp_ids = self.env['project.project'].search([('user_id','=',self.env.user.id),('priority_id','=',obj.priority_id.id)])
                count_doc = len(ccpp_ids)
            if obj.ranking_type:
                customer_info_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)])
                count_doc = len(customer_info_ids)
            obj.count_doc = count_doc
        
    def action_get_view(self):
        for obj in self:
            action = True
            if obj.ranking_type:
                if obj.ranking_type == 'potential':
                    customer_info_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)],order='potential_ranking',limit=3)
                    action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
                    action['domain'] = [('id', 'in', customer_info_ids.ids)]
                    #action['context'] = {'order': 'potential_ranking'}
                    tree_view_id = self.env.ref('ccpp.ccpp_customer_information_view_tree_order_potential').id
                    action['views'] = [(tree_view_id,'tree')]
                if obj.ranking_type == 'actual':
                    customer_info_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)],order='actual_sale_ranking',limit=3)
                    action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
                    action['domain'] = [('id', 'in', customer_info_ids.ids)]
                    #action['context'] = {'order': 'actual_sale_ranking'}
                    tree_view_id = self.env.ref('ccpp.ccpp_customer_information_view_tree_order_actual').id
                    action['views'] = [(tree_view_id,'tree')]
                if obj.ranking_type == 'competitor':
                    customer_info_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)],order='competitor_ranking',limit=3)
                    action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_customer_information_action')
                    action['domain'] = [('id', 'in', customer_info_ids.ids)]
                    #action['context'] = {'order': 'competitor_ranking'}
                    tree_view_id = self.env.ref('ccpp.ccpp_customer_information_view_tree_order_competitor').id
                    action['views'] = [(tree_view_id,'tree')]
                    
            if obj.priority_id:
                ccpp_ids = self.env['project.project'].search([('user_id','=',self.env.user.id),('priority_id','=',obj.priority_id.id)])
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_dashboard_project_action')
                action['domain'] = [('id', 'in', ccpp_ids.ids)]
                action['context'] = {'search_default_Partner': 1}
            return action
            
                

    def action_get_task(self):
        return True