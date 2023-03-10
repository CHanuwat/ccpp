from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class Partner(models.Model):
    _inherit = "res.partner"
    
    job_position_id = fields.Many2one('res.partner.position', string='Job Position', index=True, copy=False ,help="replace instead function field char")
    province_id = fields.Many2one('ccpp.province', string="Province")
    customer_category_id = fields.Many2one('ccpp.customer.category', string="Customer Category")
    is_customer = fields.Boolean(string="Customer", default=False)
    is_vendor = fields.Boolean(string="Vendor", default=False)
    is_competitor = fields.Boolean(string="Competitor", default=False)
    
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
        return res
    
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
                
class PartnerPosition(models.Model):
    _name = "res.partner.position"
    
    name = fields.Char("Position Name")
    parent_partner_id = fields.Many2one("res.partner", string="Position Of", domain=[('is_company','=',True)])
    partner_lines = fields.One2many('res.partner', 'job_position_id', string='Partner')
    active = fields.Boolean("Active", default=True)