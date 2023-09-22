from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPCustomerCategory(models.Model):
    _name = "ccpp.customer.category"
    _description = "CCPP Customer Category"

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)