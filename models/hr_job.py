from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint

class Job(models.Model):
    _inherit = "hr.job"
    
    parent_id = fields.Many2one("hr.job", string="Parent Job Position")
    child_ids = fields.One2many("hr.job", 'parent_id', string="Child Job Position")
    

