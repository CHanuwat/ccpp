from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class CCPPWizardFillHistory(models.TransientModel):
    _name = "ccpp.wizard.fill.history"
    _description = "CCPP Wizard Fill History"

    def _default_value_task(self):
        task_id = False
        if self._context.get("default_task"):
            task_id = self._context.get("default_task")
        return task_id
    
    
    
    def _default_value_order_lines(self):
        list_order_lines = []
        current_year = str(datetime.today().year)
        if self._context.get("default_task"):
            task = self._context.get("default_task")
            task_id = self.env['account.analytic.line'].browse(task)
            purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',task_id.customer_id.id),
                                                                            ('year_selection','=',current_year),
                                                                            ('job_id','=',task_id.job_id.id)
                                                                            ])  
            for history_line_id in purchase_history_id.winmed_lines:
                val = (0,0,{'wizard_id': self.id,
                            'history_line_id': history_line_id.id,
                            })
                list_order_lines.append(val)
        return list_order_lines
    
    def _default_value_borrow_lines(self):
        list_borrow_lines = []
        current_year = str(datetime.today().year)
        if self._context.get("default_task"):
            task = self._context.get("default_task")
            task_id = self.env['account.analytic.line'].browse(task)
            purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',task_id.customer_id.id),
                                                                            ('year_selection','=',current_year),
                                                                            ('job_id','=',task_id.job_id.id)
                                                                            ])  
            for history_line_id in purchase_history_id.winmed_lines:
                val = (0,0,{'wizard_id': self.id,
                            'history_line_id': history_line_id.id,
                            })
                list_borrow_lines.append(val)
        return list_borrow_lines

    """ def _default_value_ccpp(self):
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
        return strategy_id """
        

    task_id = fields.Many2one("account.analytic.line", string="Task", default=_default_value_task)
    order_lines = fields.One2many("ccpp.wizard.fill.history.order", 'wizard_id', string="Order Lines", default=_default_value_order_lines)
    borrow_lines = fields.One2many("ccpp.wizard.fill.history.borrow", 'wizard_id', string="Borrow Lines", default=_default_value_borrow_lines)
    
    def button_done(self):
        for obj in self:
            history_line_ids = obj.order_lines.mapped("history_line_id")
            purchase_dict = {}
            for history_line_id in history_line_ids:
                purchase_dict.setdefault(history_line_id, {'borrow_qty': 0, 
                                                                    'order_borrow_qty': 0, 
                                                                    'order_qty': 0,
                                                                    'remain_qty': 0, })
            for order_line in obj.order_lines:
                purchase_dict[order_line.history_line_id].update({'order_qty': order_line.order_qty,
                                                                           'remain_qty': order_line.remain_qty
                                                                           })
            for borrow_line in obj.borrow_lines:
                purchase_dict[borrow_line.history_line_id].update({'borrow_qty': borrow_line.borrow_qty,
                                                                           'order_borrow_qty': borrow_line.order_borrow_qty
                                                                           })
            
            detail_line = self.env['ccpp.purchase.history.detail.line']
            date_today = date.today()
            for history_line_id, purchase_val in purchase_dict.items():
                if purchase_val['borrow_qty'] != 0 or purchase_val['order_borrow_qty'] != 0 or purchase_val['order_qty'] != 0 or purchase_val['remain_qty'] != 0:
                    vals = {'history_line_id': history_line_id.id,
                            'date': date_today,
                            'task_id': obj.task_id.id,
                            'borrow_qty': purchase_val['borrow_qty'],
                            'order_borrow_qty': purchase_val['order_borrow_qty'],
                            'order_qty': purchase_val['order_qty'],
                            'remain_qty': purchase_val['remain_qty'],
                            }
                    detail_line.create(vals)
                
    def button_skip(self):
        return True        

class CCPPWizardFillHistoryOrder(models.TransientModel):
    _name = "ccpp.wizard.fill.history.order"
    _description = "CCPP Wizard Fill History Order"
    
    wizard_id = fields.Many2one("ccpp.wizard.fill.history", index=True, ondelete='cascade', readonly=True, required=True)
    history_line_id = fields.Many2one("ccpp.purchase.history.line", string="Purchase History Line")
    product_id = fields.Many2one(related="history_line_id.product_id")
    asset_id = fields.Many2one(related="history_line_id.asset_id")
    order_qty = fields.Float(string="Ordered Qty")
    remain_qty = fields.Float(string="Remaining Qty")    

class CCPPWizardFillHistoryBorrow(models.TransientModel):
    _name = "ccpp.wizard.fill.history.borrow"
    _description = "CCPP Wizard Fill History Borrow"
    
    wizard_id = fields.Many2one("ccpp.wizard.fill.history", index=True, ondelete='cascade', readonly=True, required=True)
    history_line_id = fields.Many2one("ccpp.purchase.history.line", string="Purchase History Line")
    product_id = fields.Many2one(related="history_line_id.product_id")
    asset_id = fields.Many2one(related="history_line_id.asset_id")
    borrow_qty = fields.Float(string="Borrow Qty")
    order_borrow_qty = fields.Float(string="Ordered Borrow Qty")
    