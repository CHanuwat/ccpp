from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPSaleTargetPeriod(models.Model):
    _name = "ccpp.sale.target.period"
    _inherit = ['mail.thread']
    
    def _get_default_date_from(self):
        if datetime.today().month in range(1,3):
            date_from = datetime.today().replace(day=1,month=1)
        if datetime.today().month in range(4,6):
            date_from = datetime.today().replace(day=1,month=4)
        if datetime.today().month in range(7,9):
            date_from = datetime.today().replace(day=1,month=7)
        if datetime.today().month in range(10,12):
            date_from = datetime.today().replace(day=1,month=9)
        return date_from
    
    def _get_default_date_to(self):
        if datetime.today().month in range(1,3):
            date_to = datetime.today().replace(day=31,month=3)
        if datetime.today().month in range(4,6):
            date_to = datetime.today().replace(day=30,month=6)
        if datetime.today().month in range(7,9):
            date_to = datetime.today().replace(day=30,month=9)
        if datetime.today().month in range(10,12):
            date_to = datetime.today().replace(day=31,month=12)
        return date_to
        
    name = fields.Char(string="Name")
    year = fields.Char(string="Year")
    date_from = fields.Date(string="Date From", default=_get_default_date_from)
    date_to = fields.Date(string="Date To", default=_get_default_date_to)

            
    