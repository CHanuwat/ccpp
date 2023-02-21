from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class CCPPDepartment(models.Model):
    _name = "ccpp.department"
    _inherit = ['mail.thread']

    name = fields.Char("Name")
    
    