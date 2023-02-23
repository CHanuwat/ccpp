from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPPrioirty(models.Model):
    _name = "ccpp.priority"
    _inherit = ['mail.thread']

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Name")
    description = fields.Char("Description")
    color = fields.Integer(string='Color', default=_get_default_color)
    point = fields.Integer(string='Point')
    period_id = fields.Many2one("ccpp.period", string="Period")
    
    @api.model
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s %s' %(rec.name, rec.description)))
        return result
    
    