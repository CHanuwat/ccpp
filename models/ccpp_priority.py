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
    _order = "name"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Name")
    description = fields.Char("Description")
    color = fields.Integer(string='Color', default=_get_default_color)
    point = fields.Integer(string='Point')
    period_id = fields.Many2one("ccpp.period", string="Period")
    lines = fields.One2many("ccpp.priority.line", "priority_id", string="Lines")
    
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s %s' %(rec.name, rec.description)))
        return result
    
    def unlink(self):
        raise UserError("ระบบไม่สามารถลบ Priority ได้")
        res = super().unlink()
    
class CCPPPrioirtyLine(models.Model):
    _name = "ccpp.priority.line"

    priority_id = fields.Many2one("ccpp.priority", index=True, ondelete='cascade', readonly=True, required=True)
    date = fields.Date(string="Start Date", required=True)
    frequency = fields.Selection(selection=[
        ('equal', 'Equal To'),
        ('greater', 'Greater than'),
        ('less', 'Less than')
    ], default='equal', string="Frequency") 
    frequency_time = fields.Integer(string="Frequency Time", required=True)
    period = fields.Selection(selection=[
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
    ], default='month', string="Period", required=True) 
    active = fields.Boolean(string="active")
    