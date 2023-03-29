from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

#class Users(models.Model):
#    _inherit = "res.users"
    
#    partner_id = fields.Many2one(auto_join=True)