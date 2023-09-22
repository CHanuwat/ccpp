from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPPeriod(models.Model):
    _name = "ccpp.period"
    _description = "CCPP Period"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name")
    count = fields.Integer(string="Every")
    period = fields.Selection([
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
            ('year', 'Year'),
        ],string = "Period")