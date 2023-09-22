from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class WizardDoneCCPP(models.TransientModel):
    _name = "ccpp.wizard.done"
    _description = "CCPP Wizard Done"

    def _default_value_ccpp(self):
        ccpp_id = False
        if self._context.get("default_ccpp"):
            ccpp_id = self._context.get("default_ccpp")
        return ccpp_id
    
    def _default_value_solution(self):
        solution_id = False
        if self._context.get("default_solution"):
            solution_id = self._context.get("default_solution")
        return solution_id
    
    def _default_value_strategy(self):
        strategy_id = False
        if self._context.get("default_strategy"):
            strategy_id = self._context.get("default_strategy")
        return strategy_id
        

    ccpp_id = fields.Many2one("project.project", string="CCPP", default=_default_value_ccpp)
    solution_id = fields.Many2one("project.task", string="Solution", default=_default_value_solution)
    strategy_id = fields.Many2one("project.task", string="Strategy", default=_default_value_strategy)
    
    def button_confirm(self):
        for obj in self:
            if obj.ccpp_id:
                obj.ccpp_id.button_done()
            elif obj.solution_id:
                obj.solution_id.button_done()
            elif obj.strategy_id:
                obj.strategy_id.button_done()