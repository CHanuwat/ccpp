from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class WizardRejectDoneTask(models.TransientModel):
    _name = "ccpp.wizard.done.task"
    _description = "CCPP Wizard Done Task"

    def _default_value_task(self):
        task_id = False
        if self._context.get("default_task"):
            task_id = self._context.get("default_task")
        return task_id

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
        

    task_id = fields.Many2one("account.analytic.line", string="Task", default=_default_value_task)
    ccpp_id = fields.Many2one("project.project", string="CCPP", default=_default_value_ccpp)
    solution_id = fields.Many2one("project.task", string="Solution", default=_default_value_solution)
    strategy_id = fields.Many2one("project.task", string="Strategy", default=_default_value_strategy)
    
    # def button_done(self):
    #     for obj in self:
    #         if obj.strategy_id:
    #             obj.strategy_id.button_done()
    #         obj.task_id.button_done()
            
    #         current_year = str(datetime.now().year)
    #         purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',obj.task_id.customer_id.id),
    #                                                                         ('year_selection','=',current_year),
    #                                                                         ('job_id','=',obj.task_id.job_id.id)
    #                                                                         ])  
    #         if purchase_history_id:
    #             action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_wizard_fill_history_action')
    #             action['context'] = {'default_task': obj.task_id.id}
    #             return action
            
    def button_done(self):
        for obj in self:
            if obj.strategy_id:
                obj.strategy_id.button_done()
            context = self._context.get("context")
            print(self._context)
            obj.task_id.update_check_in(context)
                
    # def button_done_and_skip(self):
    #     for obj in self:
    #         obj.task_id.button_done()
            
    #         current_year = str(datetime.now().year)
    #         purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',obj.task_id.customer_id.id),
    #                                                                         ('year_selection','=',current_year),
    #                                                                         ('job_id','=',obj.task_id.job_id.id)
    #                                                                         ])  
    #         if purchase_history_id:
    #             action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_wizard_fill_history_action')
    #             action['context'] = {'default_task': obj.task_id.id}
    #             return action
                

                