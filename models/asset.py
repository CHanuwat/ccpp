from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class Asset(models.Model):
    _name = "asset"
    _inherit = ['mail.thread','portal.mixin','mail.activity.mixin']

    code = fields.Char(string="Asset No.")
    name = fields.Char(string="Asset Name", track_visibility="onchange", required=True)
    date = fields.Date(string="Create Date", default=fields.Date.today, track_visibility="onchange", required=True)
    active = fields.Boolean(string="Active", default="True")
    customer_id = fields.Many2one("res.partner", string="Customer", track_visibility="onchange", required=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(Asset,self).create(vals_list)
        for asset in res:
            sequence_code = 'asset'
            sequence_date = asset.date
            if not asset.code:
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                asset.code = code or 'New'
        return res
    
    def name_get(self):
        res = super(Asset, self).name_get()
        if self._context.get("show_code", False):
            res = []
            for obj in self:
                new_name_list = []
                if obj.code:
                    new_name_list.append(obj.code)
                if obj.name:
                    new_name_list.append(obj.name)
                new_name = ', '.join(new_name_list)
                res.append((obj.id, new_name))
        return res