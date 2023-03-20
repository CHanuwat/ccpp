from email.policy import default
from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from odoo.addons.project.models.project_update import ProjectUpdate
import requests
from urllib.request import urlopen
#from digidevice import location
#from geopy.geocoders import Nominatim
from odoo.http import request
from geopy.geocoders import Nominatim
import geopy
import urllib
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
import math
import googlemaps
from datetime import datetime
from pprint import pprint

STATUS_COLOR = {
    'on_track': 20,  # green / success
    'at_risk': 23,  # red / danger
    'off_track': 2,  # orange
    'on_hold': 8,  # light blue
    False: 0,  # default grey -- for studio
    # Only used in project.task
    'to_define': 0,
}

STATE_COLOR = {
    'open': 0,  # green / success
    'reject': 24,
    'waiting_approve': 8,
    'process': 3,  # orangeq
    'done': 20,  # red / danger
    'cancel': 23,  # light blue
    '1': 9,
    '2': 2,
    '3': 3,
    '4': 4,
    False: 0,  # default grey -- for studio
}

class Project(models.Model):
    _inherit = "project.project"
    #_rec_name = 'code'

    def _get_default_sale_team(self):
        print("x*50"+"pass pass pass")
        return self.env['crm.team'].search([('user_id','=',self.env.user.id)], limit=1)

    department_id = fields.Many2one("hr.department",string="Department")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    priority_id = fields.Many2one("ccpp.priority", string="CCPP Priority", compute="_get_priority", store=True)
    priority_select = fields.Selection([
        ('to_define', 'To Define'),
        ('1', '1st'),
        ('2', '2nd'),
        ('3', '3rd'),
        ('4', '4th'),
        #('delay', 'delayed'),
    ], compute="_get_priority", string="Priority Selection", store=True)
    
    sale_team_id = fields.Many2one("crm.team", string="Sale Team", default="_get_default_sale_team")
    domain_task_solution_ids = fields.Many2many('project.task', string="Domain task solution")
    tasks_solution = fields.One2many('project.task', 'project_solution_id', string="Solution", context={'is_solution': True})
    name = fields.Char(string="Name of CCPP", translate=False)
    user_id = fields.Many2one(related="employee_id.user_id", string="CCPP User", store=True)
    color = fields.Integer(related="priority_id.color", store=True)
    
    # Host CCPP
    partner_contact_id = fields.Many2one("res.partner", string="Host of CCPP")
    domain_partner_contact_ids = fields.Many2many("res.partner", string="Domain partner contact", compute="_compute_domain_partner_contact_ids")
    job_position_id = fields.Many2one("res.partner.position", string="Host of CCPP", related="partner_contact_id.job_position_id")
    domain_job_position_ids = fields.Many2many("res.partner.position", string="Domain Job Position", compute="_compute_domain_job_position_ids")
    
    ## impact customer ##
    is_income_cus = fields.Boolean("Income/Funding", default=False)
    is_effectiveness_cus = fields.Boolean("Effectiveness/Personal Performance", default=False)
    is_repulation_cus = fields.Boolean("Repulation", default=False)
    is_competitive_cus = fields.Boolean("Competitive Advantage", default=False)
    is_critical = fields.Boolean("Need help Now!", default=False)
    is_not_critical = fields.Boolean("I can wait", default=False)
    
    ## impact winmed ##
    is_income_comp = fields.Boolean("Sale Revenue/Cost", default=False)
    is_effectiveness_comp = fields.Boolean("Future Business Opportunity", default=False)
    is_repulation_comp = fields.Boolean("Repulation", default=False)
    is_competitive_comp = fields.Boolean("Competitive Advantage", default=False)
    is_short_time = fields.Boolean("Short")
    is_long_time = fields.Boolean("Long")
    
    is_verify_impact_cus = fields.Boolean("Verify impact Customer", default=False)
    is_stamp_record = fields.Boolean("Aready have record", default=False)
    show_critical = fields.Char(string="Customer Impact", compute="_compute_show_time")
    show_time = fields.Char(string="Time", compute="_compute_show_time")
    code = fields.Char(string="Code")
    #show_period = fields.Char(string="Period", compute="_compute_period_deadline", store=True)
    show_period = fields.Char(string="Period")
    period_id = fields.Many2one("ccpp.period", string="Priority Period", compute="_get_priority", store=True)
    #deadline_date = fields.Date(string="Deadline", compute="_compute_period_deadline", store=True)
    deadline_date = fields.Date(string="Deadline", compute="_compute_deadline", store=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('waiting_approve', 'Waiting For Approval'),
        ('reject', 'Rejected'),
        ('process', 'On Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        #('delay', 'delayed'),
    ], default='open', index=True, string="State", track_visibility="onchange", tracking=True)
    state_color = fields.Integer(compute='_compute_state_color')
    next_action = fields.Char("Next Action")
    is_ccpp_done = fields.Boolean(string="Is CCPP Done", compute="_compute_ccpp_done")
    is_delay = fields.Boolean(string="Is Delay", default=False)
    delay_date = fields.Date(string="Delayed Date")
    is_approve_strategy = fields.Boolean(string="Is Approve Strategy", default=False)
    is_ready_create_solution = fields.Boolean(string="Is Ready Create Solution", compute="_compute_ready_create_solution")
 
    def unlink(self):
        res = super().unlink()
        raise UserError("ระบบไม่สามารถลบ CCPP ได้ กรุณา cancel หากไม่ได้ใช้งาน")

    @api.depends('tasks_solution')   
    def _compute_ready_create_solution(self):
        for obj in self:
            is_ready_create_location = True
            if obj.tasks_solution:
                if len(obj.tasks_solution) - len(obj.tasks_solution.filtered(lambda o:o.state == 'cancel')) != 0:
                    is_ready_create_location = False
            obj.is_ready_create_solution = is_ready_create_location
    
    @api.depends('state')
    def _compute_state_color(self):
        for obj in self:         
            obj.state_color = STATE_COLOR[obj.state]
    
    @api.depends("tasks_solution.child_ids.state")
    def _compute_ccpp_done(self):
        for obj in self:
            is_done = True
            if len(obj.tasks_solution.filtered(lambda o:o.state == 'cancel')) == len(obj.tasks_solution):
                is_done = False
            for solution_id in obj.tasks_solution.filtered(lambda o:o.state not in ['done','cancel']):
                print(solution_id.name)
                for strategy_id in solution_id.child_ids:
                    print(strategy_id.name)
                    if strategy_id.state not in ['done','cancel']:
                        is_done = False
            obj.is_ccpp_done = is_done
    
    @api.depends("tasks_solution.start_date")
    def _compute_deadline(self):
        for obj in self:
            if len(obj.tasks_solution) < 2:
                for line in obj.tasks_solution:
                    if line.state not in ['cancel']:
                        obj.show_period = line.show_period
                        obj.deadline_date = line.deadline_date
                        
    
    #@api.depends("tasks_solution.start_date")
    def get_period_deadline(self):
        for obj in self:
            for line in obj.tasks_solution:
                if line.state not in ['cancel']:
                    obj.show_period = line.show_period
                    obj.deadline_date = line.deadline_date
            
    
    @api.depends("is_critical", "is_not_critical", "is_short_time", "is_long_time")
    def _compute_show_time(self):
        for obj in self:
            if obj.is_critical:
                obj.show_critical = "Critical"
            elif obj.is_not_critical:
                obj.show_critical = "Not Critical"
            else:
                obj.show_critical = ""
            if obj.is_short_time:
                obj.show_time = "ใช้เวลาน้อยกว่า 4 เดือน"
            elif obj.is_long_time:
                obj.show_time = "ใช้เวลามากกว่า 4 เดือน"
            else:
                obj.show_time = ""
    
    @api.depends("is_income_comp", "is_effectiveness_comp", "is_repulation_comp", "is_competitive_comp", "is_short_time", "is_long_time")
    def _get_priority(self):
        for obj in self:
            priority_id = self.env['ccpp.priority']
            count_impact = 0
            if obj.is_income_comp:
                count_impact += 1
            if obj.is_effectiveness_comp:
                count_impact += 1
            if obj.is_repulation_comp:
                count_impact += 1
            if obj.is_competitive_comp:
                count_impact += 1
            if obj.is_short_time and count_impact > 1:
                priority_id = self.env['ccpp.priority'].search([('point','=',1)])
            if obj.is_short_time and count_impact == 1:
                priority_id = self.env['ccpp.priority'].search([('point','=',2)])
            if obj.is_long_time and count_impact > 1:
                priority_id = self.env['ccpp.priority'].search([('point','=',3)])
            if obj.is_long_time and count_impact == 1:
                priority_id = self.env['ccpp.priority'].search([('point','=',4)])
            obj.priority_id = priority_id.id
            obj.period_id = priority_id.period_id.id
            obj.priority_select = str(priority_id.point) if priority_id else 'to_define'
                
    #@api.onchange("is_critical", "is_not_critical", "is_short_time", "is_long_time")       
    #def onchange_unique(self):
        #if self.is_critical and self.is_not_critical:
            #raise UserError("กรุณาเลือกความเร่งด่วนอย่างใดอย่างหนึ่ง")
        #if self.is_short_time and self.is_long_time:
            #raise UserError("กรุณาเลือกระยะเวลาในการแก้ปัญหาใดอย่างหนึ่ง")
    
    @api.onchange("is_critical") 
    def onchange_is_critical(self):
        for obj in self:
            if obj.is_critical:
                obj.is_not_critical = False
            
    @api.onchange("is_not_critical") 
    def onchange_is_not_critical(self):
        for obj in self:
            if obj.is_not_critical:
                obj.is_critical = False
                obj.is_income_comp = False
                obj.is_effectiveness_comp = False
                obj.is_repulation_comp = False
                obj.is_competitive_comp = False
                obj.is_long_time = False
                obj.is_short_time = False
                #obj.write({'is_income_comp': False})
                #obj.write({'is_effectiveness_comp': False})
                #obj.write({'is_repulation_comp': False})
                #obj.write({'is_competitive_comp': False})
                #obj.write({'is_long_time': False})
                #obj.write({'is_short_time': False})

    @api.onchange("is_short_time") 
    def onchange_is_short_time(self):
        for obj in self:
            if obj.is_short_time:
                obj.is_long_time = False
            
    @api.onchange("is_long_time") 
    def onchange_is_long_time(self):
        for obj in self:
            if obj.is_long_time:
                obj.is_short_time = False    
    
    @api.depends('tasks')
    def domain_task_ids(self):
        for obj in self:
            task_ids = self.env['project.task']
            for task_id in obj.tasks_solution:
                if task_id.is_solution:
                    task_ids |= task_id
            obj.domain_task_solution_ids.ids

    @api.depends("partner_id")
    def _compute_domain_partner_contact_ids(self):
        for obj in self:
            partner_contact_ids = self.env['res.partner']
            if obj.partner_id:
                for child_id in obj.partner_id.child_ids:
                    partner_contact_ids |= child_id
            obj.domain_partner_contact_ids = partner_contact_ids.ids
            
    @api.depends("partner_id")
    def _compute_domain_job_position_ids(self):
        for obj in self:
            job_position_ids = self.env['res.partner.position']
            if obj.partner_id:
                for child_id in obj.partner_id.child_ids:
                    job_position_ids |= child_id.job_position_id
            obj.domain_job_position_ids = job_position_ids.ids
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            user_id = self.env.user
            employee_id = self.env['hr.employee'].search([('user_id','=',user_id.id)],limit=1)
            if not employee_id or not employee_id.department_id:
                raise UserError("Not recognize the department. Please Configue User to Employee to get the department")
            sale_team_ids = self.env['crm.team'].search([])
            sale_team_id = self.env['crm.team']
            for sale_team_id in sale_team_ids:
                for member_id in sale_team_id.member_ids:
                    if member_id == user_id:
                        break
            sale_team_id = self.env['crm.team'].search([('user_id','=',self.env.user.id)], limit=1)
            vals['employee_id'] = employee_id.id
            vals['department_id'] = employee_id.department_id.id
            vals['sale_team_id'] = sale_team_id.id
            if not vals.get('is_income_cus') and not vals.get('is_effectiveness_cus') and not vals.get('is_repulation_cus') and not vals.get('is_competitive_cus'):
                raise UserError("กรุณาเลือกผลกระทบต่อลูกค้าอย่างน้อย 1 ข้อ")
            if not vals.get('is_critical') and not vals.get('is_not_critical'):
                raise UserError("กรุณาเลือกความเร่งด่วนของลูกค้าที่ต้องการความช่วยเหลือ")
            print(self._context)
            if self._context.get('create_from_tree') and not self._context.get('default_allow_billable'):
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                #sequence_code = 'ccpp.'+'cp.'+employee_id.department_id.code
                sequence_code = 'ccpp.'+'cp'
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                vals['code'] = code
            
        res = super(Project, self).create(vals_list)
        #if not res.is_income_cus and not res.is_effectiveness_cus and not res.is_repulation_cus and not res.is_competitive_cus:
        #    raise UserError("กรุณาเลือกผลกระทบต่อลูกค้าอย่างน้อย 1 ข้อ")
        #if not res.is_critical and not res.is_not_critical:
        #    raise UserError("กรุณาเลือกผลกระทบต่อลูกค้าอย่างน้อย 1 ข้อ")
        return res
    
    # replace for open project instead
    def action_view_tasks(self):
        if self._context.get('need_fill') and not self.is_verify_impact_cus and not self.is_income_cus and not self.is_effectiveness_cus and not self.is_repulation_comp and not self.is_competitive_cus:
            raise UserError("กรุณาเลือกผลกระทบต่อลูกค้าอย่างน้อย 1 ข้อ")
        if self._context.get('need_fill') and not self.is_verify_impact_cus and not self.is_critical and not self.is_not_critical:
            raise UserError("กรุณาเลือกความเร่งด่วนของลูกค้าที่ต้องการความช่วยเหลือ")
        if self._context.get('need_fill') and self.is_verify_impact_cus and not self.is_income_comp and not self.is_effectiveness_comp and not self.is_repulation_comp and not self.is_competitive_comp:
            raise UserError("กรุณาเลือกผลกระทบต่อบริษัทอย่างน้อย 1 ข้อ")
        if self._context.get('need_fill') and self.is_verify_impact_cus and not self.is_short_time and not self.is_long_time:
            raise UserError("กรุณาเลือกระยะเวลาการแก้ไขปัญหา")   
        if not self.code and self.department_id:
            sequence_date = datetime.now().strftime("%Y-%m-%d")
            #sequence_code = 'ccpp.'+'cp.'+self.department_id.code
            sequence_code = 'ccpp.'+'cp'
            code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
            self.code = code
            
        action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id('project.open_view_project_all')
        action['views'] = [(self.env.ref('project.edit_project').id, 'form')]
        action['res_id'] = self.id
        return action
    
    def button_skip_and_create(self):
        # reset value #
        self.is_income_comp = False
        self.is_effectiveness_comp = False
        self.is_repulation_comp = False
        self.is_competitive_comp = False
        self.is_short_time = False
        self.is_long_time = False
        if not self.code and self.department_id:
            sequence_date = datetime.now().strftime("%Y-%m-%d")
            #sequence_code = 'ccpp.'+'cp.'+self.department_id.code
            sequence_code = 'ccpp.'+'cp'
            code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
            self.code = code
            
        action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id('project.open_view_project_all')
        action['views'] = [(self.env.ref('project.edit_project').id, 'form')]
        action['res_id'] = self.id
        return action
    
    def button_back_create_ccpp(self):
        self.is_verify_impact_cus = False
        self.is_income_comp = False
        self.is_effectiveness_comp = False
        self.is_repulation_comp = False
        self.is_competitive_comp = False
        self.is_short_time = False
        self.is_long_time = False
        action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id('project.open_create_project')
        action['views'] = [(self.env.ref('project.project_project_view_form_simplified_footer').id, 'form')]
        action['res_id'] = self.id
        return action
    
    def button_discard_create_ccpp(self):
        self.unlink()
        return True

    def button_next_create_ccpp(self):
        if not self.is_income_cus and not self.is_effectiveness_cus and not self.is_repulation_cus and not self.is_competitive_cus:
            raise UserError("กรุณาเลือกผลกระทบต่อลูกค้าอย่างน้อย 1 ข้อ")
        if not self.is_critical and not self.is_not_critical:
            raise UserError("กรุณาเลือกความเร่งด่วนของลูกค้าที่ต้องการความช่วยเหลือ")
        self.is_verify_impact_cus = True
        self.is_stamp_record = True
        action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id('project.open_create_project')
        action['views'] = [(self.env.ref('project.project_project_view_form_simplified_footer').id, 'form')]
        action['res_id'] = self.id
        return action
        #return {'type': 'ir.actions.do_nothing'}
        
    def ccpp_update_all_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_update_all_action')
        #action['display_name'] = _("%(name)s's Updates", name=self.name)
        return action
    
    def button_send_approve(self):
        for obj in self:
            obj.check_information()
            obj.state = 'waiting_approve'
            for solution_id in obj.tasks_solution:
                if solution_id.state == 'open':
                    solution_id.state = 'waiting_approve'
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state == 'open':
                        strategy_id.state = 'waiting_approve'
    
    def check_information(self):
        for obj in self:
            if not obj.priority_id:
                raise UserError("กรุณาเลือกผลกระทบต่อบริษัทอย่างน้อย 1 ข้อ และเลือกระยะเวลาการแก้ไขปัญหา")
            if obj.priority_id.point > 2:
                raise UserError("Please send only CCPP 1st and 2nd priority")
            if not obj.partner_id:
                raise UserError("Please select Customer")
            if not obj.partner_contact_id:
                raise UserError("Please select Host of CCPP")
            for solution_id in obj.tasks_solution:
                if not solution_id.start_date:
                    raise UserError("Please select solution start date")
            if not obj.tasks_solution:
                raise UserError("Please set Solutions")
            else:
                for solution_id in obj.tasks_solution:
                    if not solution_id.child_ids:
                        raise UserError("Please set Strategy")
                                               
    def button_approve(self):
        for obj in self:
            obj.state = 'process'
            for solution_id in obj.tasks_solution:
                if solution_id.state == 'waiting_approve':
                    solution_id.state = 'process'
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state == 'waiting_approve':
                        strategy_id.state = 'process'
            obj.get_period_deadline()
            
    def button_reject(self):
        for obj in self:
            obj.state = 'reject'
            for solution_id in obj.tasks_solution:
                if solution_id.state == 'waiting_approve':
                    solution_id.state = 'reject'
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state == 'waiting_approve':
                        strategy_id.state = 'reject'
        
    def button_done(self):
        for obj in self:
            obj.state = 'done'
            for solution_id in obj.tasks_solution:
                if solution_id.state == 'process':
                    solution_id.state = 'done'
        
    def button_cancel(self):
        for obj in self:
            obj.state = 'cancel'
            for solution_id in obj.tasks_solution:
                if solution_id.state not in ['done','waiting_approve']:
                    solution_id.state = 'cancel'
                if solution_id.state == 'waiting_approve':
                    raise UserError("Please check solution %s is state in Waiting For Approval"%solution_id.name)
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state not in ['done','waiting_approve']:
                        strategy_id.state = 'cancel'
                    if strategy_id.state == 'waiting_approve':
                        raise UserError("Please check strategy %s is state in Waiting For Approval"%strategy_id.name)
        
    def button_to_open(self):
        for obj in self:
            obj.state = 'open'
            for solution_id in obj.tasks_solution:
                if solution_id.state == 'reject':
                    solution_id.state = 'open'
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state == 'reject':
                        strategy_id.state = 'open'
            
    def check_ccpp_delayed(self):
        date_today = datetime.now().strftime("%Y-%m-%d")
        ccpp_ids = self.env['project.project'].search([('state','=','process'),('deadline_date','<',date_today),('deadline_date','!=',False)])
        ccpp_ids.write({'is_delay': True, 'delay_date': date_today})
        for ccpp_id in ccpp_ids:
            for solution_id in ccpp_id.tasks_solution:
                if solution_id.state not in ['done','cancel']:
                    #solution_id.state = 'delay'
                    solution_id.is_delay = True
                    solution_id.delay_date = date_today
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state not in ['done','cancel']:
                        #strategy_id.state = 'delay'
                        strategy_id.is_delay = True
                        strategy_id.delay_date = date_today
                        
    def run_script_update(self):
        ccpp_ids = self.env['project.project'].search([])
        for ccpp_id in ccpp_ids:
            for solution_id in ccpp_id.tasks_solution:
                for strategy_id in solution_id.child_ids:
                    if solution_id.start_date:
                        strategy_id.start_date = solution_id.start_date
                    if solution_id.deadline_date:
                        strategy_id.deadline_date = solution_id.deadline_date

                
    # overide change color 
    @api.depends('last_update_status')
    def _compute_last_update_color(self):
        for project in self:
            project.last_update_color = STATUS_COLOR[project.last_update_status]
    
    def action_open_solution(self):
        #solution_ids = self.env['project.task'].search([("project_id","=",self.id),("is_solution","=",True)])
        solution_ids = self.env['project.task'].search([("project_id","=",self.id)])
        context = self.env.context.copy()
        context = context.update({'search_default_groupby_task_type': 1})
        #context = context.update({'default_groupby_task_type': 1})
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.action_solution_strategy_tree')
        action['domain'] = [('id','in',solution_ids.ids)]
        #action['context'] = {'search_default_groupby_task_type': 1}
        action['context'] = context
        #return action
        print("XXX"*50)
        print(context)
        print(self._context)
        print(self.env.context)
        strategy_ids = self.env['project.task'].search([("project_id","=",self.id),('is_strategy','=',True)])
        
        return {
            'name': self.name,
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'domain': [('id','in',strategy_ids.ids)],
            'type': 'ir.actions.act_window',
            'search_view_id': [self.env.ref('ccpp.strategy_search_form').id, 'search'],
            'context': {'search_default_groupby_solution': 1},
            'views' : [(self.env.ref('ccpp.solution_strategy_tree').id, 'tree'),(self.env.ref('project.view_task_form2').id, 'form')]
        }   
        
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        orderby = "priority_id asc"
        res = super(Project, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
        
    def create_solution(self):
        print("max"*50)
        print(
            "self_id", self.id
        )
        if not self.id:
            raise UserError("กรุณากดบันทึก CCPP ก่อน")
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.open_view_task_all_ccpp')
        action['context'] = {'is_create_button_solution': True, 'project_id': self.id, 'is_create_solution': True}
        return action
    
    def action_ccpp_department_approve_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_ccpp_approve_dashboard_action')
        department_id = self.env.user.employee_id.department_id
        ccpp_ids = self.env['project.project'].search([('state', '=', 'waiting_approve'),
                                                        ('department_id', '=', department_id.id),
                                                        ])
        action['domain'] = [('id','in',ccpp_ids.ids)]
        return action
    
    def action_ccpp_department_group_by_priority_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.action_all_ccpp_group_by_priority')
        department_id = self.env.user.employee_id.department_id
        ccpp_ids = self.env['project.project'].search([('department_id', '=', department_id.id)])
        action['domain'] = [('id','in',ccpp_ids.ids)]
        return action
        
    def action_ccpp_department_group_by_customer_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.action_my_ccpp_group_by_customer')
        department_id = self.env.user.employee_id.department_id
        ccpp_ids = self.env['project.project'].search([('department_id', '=', department_id.id)])
        action['domain'] = [('id','in',ccpp_ids.ids)]
        return action
        
class Task(models.Model):
    _inherit = "project.task" 
    _order = "code"
    #_rec_name = "code"
    
    def _get_default_level(self):
        if self._context.get('is_create_solution'):
            return True
        else:
            return False
    
    def _default_user_ids(self):
        return self.env.user.ids
    
    is_solution = fields.Boolean(string='Is Solution', default=_get_default_level, compute="_compute_level", store=True)
    is_strategy = fields.Boolean(string='Is Strategy', default=False, compute="_compute_level", store=True)
    is_task = fields.Boolean(string='Is Task', default=False, compute="_compute_level", store=True)
    is_subtask = fields.Boolean(string='Is SubTask', default=False, compute="_compute_level", store=True)
    task_type = fields.Selection([
        ('solution', 'Solution'),
        ('strategy', 'Strategy'),
    ], default="solution", string="Task Type", compute="_compute_level", store=True)
    project_solution_id = fields.Many2one("project.project", string="Relate Project Solution")
    code = fields.Char(string="Code")
    period_id = fields.Many2one("ccpp.period", string="Priority Period", related="project_id.period_id")
    partner_id = fields.Many2one(related="project_id.partner_id")
    job_position_id = fields.Many2one("res.partner.position", string="Host of CCPP",related="project_id.job_position_id")
    priority_id = fields.Many2one("ccpp.priority", string="Priority", related="project_id.priority_id")
    evaluate_method = fields.Char("วิธีวัดผล/เป้าหมาย")
    situation_ids = fields.One2many("project.update", 'strategy_id', string="Current Situation")
    last_situation_id = fields.Many2one("project.update", string="Last Update Situation Strategy") # last update at strategy
    last_situation_solution_id = fields.Many2one("project.update", string="Last Update Situation Solution") # last update at solution
    state = fields.Selection([
        ('open', 'Open'),
        ('waiting_approve', 'Waiting For Approval'),
        ('reject', 'Rejected'),
        ('process', 'On Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        #('delay', 'Delayed'),
    ], default='open', index=True, string="State", track_visibility="onchange", tracking=True)
    last_update_status_strategy = fields.Selection(selection=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
        ('to_define', 'Set Status'),
    ], default='to_define', compute='_compute_last_update_status', store=True, readonly=False, required=True)
    last_update_color_strategy = fields.Integer(compute='_compute_last_update_color')
    last_update_status_solution = fields.Selection(selection=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
        ('to_define', 'Set Status'),
    ], default='to_define', compute='_compute_last_update_status', store=True, readonly=False, required=True)
    last_update_color_solution = fields.Integer(compute='_compute_last_update_color')
    state_color = fields.Integer(compute='_compute_state_color')
    next_action_solution = fields.Char(string="Next Action Solution")
    next_action = fields.Char(string="Next Action")
    start_date = fields.Date(string="Start Date")
    deadline_date = fields.Date(string="Deadline", compute="_compute_deadline", store=True)
    priority_line_id = fields.Date(string="Priority Line") # stamp when approve :fix me
    show_period = fields.Char(string="Period", compute="_compute_deadline", store=True)
    is_delay = fields.Boolean(string="Is Delay", default=False)
    delay_date = fields.Date(string="Delayed Date")
    is_ccpp_on_process = fields.Boolean(string="Is CCPP on process", compute="_is_on_process", store=True)
    is_solution_on_approve = fields.Boolean(string="Is Solution on process", compute="_is_on_process", store=True)
    user_ids = fields.Many2many(default=_default_user_ids)
    priority_select = fields.Selection(related="project_id.priority_select")
    
    
    def unlink(self):
        if self.is_solution:
            raise UserError("ระบบไม่สามารถลบ Solution ได้ กรุณา cancel หากไม่ได้ใช้งาน")
        if self.is_strategy:
            raise UserError("ระบบไม่สามารถลบ Strategy ได้ กรุณา cancel หากไม่ได้ใช้งาน")
        res = super().unlink()
        
    @api.depends("is_solution","project_id.state","is_strategy","parent_id.project_id.state","parent_id.state")
    def _is_on_process(self):
        for obj in self:
            is_ccpp_on_process = False
            is_solution_on_approve = False
            if obj.is_solution:
                if obj.project_id.state == 'process':
                    is_ccpp_on_process = True
            if obj.is_strategy:
                if obj.parent_id.project_id.state == 'process':
                    is_ccpp_on_process = True
                if obj.parent_id.state in ['open','reject','waiting_approve']:
                    is_solution_on_approve = True
            obj.is_ccpp_on_process = is_ccpp_on_process
            obj.is_solution_on_approve = is_solution_on_approve
    
    @api.depends('project_id.priority_id','start_date')
    def _compute_deadline(self):
        for obj in self:
            deadline_date = False
            string_show_period = False
            if obj.project_id.priority_id and obj.start_date and obj.project_id.priority_id.point <= 2:
                start_date_obj = obj.start_date
                priority_line_id = obj.project_id.priority_id.lines.filtered(lambda o:o.active)
                
                if not priority_line_id:
                    raise UserError("Please Configure Time Frequenzy for Priority %s"%(obj.project_id.priority_id.name))
                if len(priority_line_id) > 1:
                    raise UserError("Configure Time Frequenzy more than 1")
                
                start_period_date_obj = priority_line_id.date
                
                if priority_line_id.period == "day":
                    period = 0
                    while True:
                        end_period_date_obj = start_period_date_obj + timedelta(days=priority_line_id.frequency_time -1)
                        if start_date_obj >= start_period_date_obj and start_date_obj <= end_period_date_obj:
                            deadline_date = end_period_date_obj.strftime("%Y-%m-%d")
                            break
                        else:
                            start_period_date_obj = end_period_date_obj + timedelta(days=1)
                            period += 1
                    
                elif priority_line_id.period == "week":
                    period = 0
                    while True:
                        end_period_date_obj = start_period_date_obj + timedelta(days=(priority_line_id.frequency_time*7)-1)
                        if start_date_obj >= start_period_date_obj and start_date_obj <= end_period_date_obj:
                            deadline_date = end_period_date_obj.strftime("%Y-%m-%d")
                            break
                        else:
                            start_period_date_obj = end_period_date_obj + timedelta(days=1)
                            period += 1

                elif priority_line_id.period in ["month","year"]:
                    period = 0
                    if priority_line_id.period == 'month':
                        frequency_time = priority_line_id.frequency_time
                    elif priority_line_id.period == 'year':
                        frequency_time = priority_line_id.frequency_time * 12
                    count = frequency_time
                    while True:
                        if count%frequency_time == 0:
                            month = start_period_date_obj.month
                            if start_period_date_obj.month + frequency_time <= 12:
                                replace_month = start_period_date_obj.month + frequency_time -1
                                replace_year = start_period_date_obj.year
                                period += 1
                            else:
                                replace_month = ((start_period_date_obj.month + frequency_time) %12) -1
                                if priority_line_id.period == 'month':
                                    replace_year = start_period_date_obj.year + 1
                                    period = 0
                                elif priority_line_id.period == 'year':
                                    replace_year = start_period_date_obj.year + priority_line_id.frequency_time
                                    period += 1
                            if replace_month == 0:
                                replace_month = 12
                                replace_year -= 1
                                
                            
                            print("x1")
                            print(start_period_date_obj)
                            print("x2")
                            print(replace_month,replace_year)
                            end_period_date_obj = start_period_date_obj
                            print("x3")
                            print(end_period_date_obj)
                            end_period_date_obj = end_period_date_obj.replace(month=replace_month,year=replace_year)
                            end_period_date_obj = end_period_date_obj + relativedelta(day=31)
                            print("x4")
                            print(end_period_date_obj)
                        
                        
                        if start_date_obj >= start_period_date_obj and start_date_obj <= end_period_date_obj:
                            deadline_date = end_period_date_obj.strftime("%Y-%m-%d")
                            break
                        else:
                            start_period_date_obj = end_period_date_obj + timedelta(days=1)
                            count += 1
                if period == 0:
                    period = math.ceil(12/frequency_time)
                string_show_period = 'Period '+ str(period)
                
            obj.show_period = string_show_period
            obj.deadline_date = deadline_date
            # write start date to strategy
            for strategy_id in obj.child_ids:
                strategy_id.show_period = string_show_period
                strategy_id.deadline_date = deadline_date
                strategy_id.start_date = obj.start_date
                
    @api.depends('last_situation_id.status','last_situation_solution_id.status')
    def _compute_last_update_status(self):
        for obj in self:
            #if obj.is_solution:
            obj.last_update_status_solution = obj.last_situation_solution_id.status or 'to_define'
            #if obj.is_strategy:
            obj.last_update_status_strategy = obj.last_situation_id.status or 'to_define'

    @api.depends('last_update_status_solution','last_update_status_strategy')
    def _compute_last_update_color(self):
        for obj in self:
            #if obj.is_solution:
            obj.last_update_color_solution = STATUS_COLOR[obj.last_update_status_solution]
            #if obj.is_strategy:
            obj.last_update_color_strategy = STATUS_COLOR[obj.last_update_status_strategy]
            
    @api.depends('state')
    def _compute_state_color(self):
        for obj in self:         
            obj.state_color = STATE_COLOR[obj.state]
        
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            print("X"*100)
            print(self.env.context)
            print(self._context)
            #if self._context.get('project_id'):
                #vals['project_id'] = self._context.get('project_id')
            #if self._context.get('is_solution',False) and not self._context.get('is_create_strategy',False) and self._context.get('active_id',False):
            #    params = self._context.get('params')
            #    if params:
            #        vals['project_id'] = params.get('id')
            #    else:
            #        vals['project_id'] = self._context.get('active_id')
        res = super(Task, self).create(vals_list)
        print("Y"*100)
        print(res)
        for rec in res:
            print("type solution/strategy----->",rec.is_solution,rec.is_strategy)
            print("project ------>", rec.project_id)
            print("project solution ------>", rec.project_solution_id)
            print("project ------>", rec.parent_id.project_id)
            print("project solution ------>", rec.parent_id.project_solution_id,rec.parent_id.project_solution_id.department_id.code )
            
            if rec.is_solution:
                if rec.project_solution_id:
                    rec.project_id = rec.project_solution_id.id
                if rec.project_id:
                    rec.project_solution_id = rec.project_id.id
                if self._context.get('project_id') and self._context.get('is_create_button_solution'):
                    rec.project_id = self._context.get('project_id')
                    rec.project_solution_id = self._context.get('project_id')
            if rec.is_solution and rec.project_id.department_id:
                if not rec.project_id.department_id.code:
                    raise UserError("Not recognize the department code. Please Configure code to Department to get the department code")
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                #sequence_code = 'ccpp.'+'sl.'+rec.project_id.department_id.code
                sequence_code = 'ccpp.'+'sl'
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                rec.code = code
            if rec.parent_id:
                
                rec.project_id = rec.parent_id.project_id.id or rec.parent_id.project_solution_id.id or self._context.get('project_id')
            
            if rec.is_strategy and (rec.project_id.department_id or rec.project_solution_id.department_id or rec.parent_id.project_id.department_id or rec.parent_id.project_solution_id.department_id):
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                code = ''
                if rec.project_id.department_id:
                    code = rec.project_id.department_id.code
                elif rec.project_solution_id.department_id:
                    code = rec.project_solution_id.department_id.code
                elif rec.parent_id.project_id.department_id:
                    code = rec.parent_id.project_id.department_id.code
                elif rec.parent_id.project_solution_id.department_id:
                    code = rec.parent_id.project_solution_id.department_id.code
                else:
                    raise UserError("Not recognize the department code. Please Configure code to Department to get the department code")
                #sequence_code = 'ccpp.'+'st.'+ code
                sequence_code = 'ccpp.'+'st'
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                rec.code = code
            #if rec.is_task and rec.project_id.department_id:
            #    sequence_date = datetime.now().strftime("%Y-%m-%d")
            #    sequence_code = 'ccpp.'+'ta.'+rec.project_id.department_id.code
            #    code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
            #    rec.code = code
            
            

        return res

    #@api.depends("display_project_id","project_id","is_solution","is_strategy","is_task","is_subtask")
    #def _compute_project_solution(self):
    #    for obj in self:
    #        project_id = self.env['project.project']
    #        if obj.is_solution:
    #            print("compute project xxx",obj.project_id.id)
    #            project_id = obj.project_id
    #        obj.project_solution_id = project_id.id

    @api.depends('parent_id')
    def _compute_level(self):
        for obj in self:
            print('check level xxx')
            print(obj.project_solution_id.id)
            is_solution = True
            is_strategy = False
            is_task = False
            is_subtask = False
            if obj.parent_id:
                is_solution = False
                is_strategy = True
                if obj.parent_id.parent_id:
                    is_solution = False
                    is_strategy = False
                    is_task = True
                    if obj.parent_id.parent_id.parent_id:
                        is_solution = False
                        is_strategy = False
                        is_task = False
                        is_subtask = True
            obj.is_solution = is_solution
            obj.is_strategy = is_strategy
            obj.is_task = is_task
            obj.is_subtask = is_subtask
            if is_solution:
                obj.task_type = 'solution'
            if is_strategy:
                obj.task_type = 'strategy'
            
    @api.depends('child_ids')
    def _compute_subtask_count(self):
        for task in self:
            #task.subtask_count = len(task._get_all_subtasks())
            task.subtask_count = len(task.child_ids)
            
    def button_open_child(self): 
        action = self.env['ir.actions.act_window']._for_xml_id('project.project_task_action_sub_task')
        action['domain'] = [('id', 'in', self.child_ids.ids)]
        return action
    
    def button_open_solution(self): 
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.open_view_task_all_ccpp')
        action['res_id'] = self.parent_id.id
        action['context'] = {'active_id': self.parent_id.id}
        return action
    
    def button_open_project(self): 
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.open_view_project_all_ccpp')
        action['res_id'] = self.project_id.id
        action['context'] = {'active_id': self.project_id.id}
        return action
    
    def action_open_task2(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.open_view_task_all_ccpp')
        action['res_id'] = self.id
        action['context'] = {'active_id': self.id}
        #return {
        #    'view_mode': 'form',
        #    'res_model': 'project.task',
        #    'res_id': self.id,
        #    'type': 'ir.actions.act_window',
        #    'context': self._context
        #}
        return action
    
    def solution_update_all_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.solution_update_all_action')
        #action['display_name'] = _("%(name)s's Updates", name=self.name)
        return action
    
    def button_update_strategy(self):
        
        """
        import requests
        

        page = requests.get("https://ava.win.clinic/geolocation")
        soup = BeautifulSoup(page.text, 'html.parser')
        title = soup.title.text # gets you the text of the <title>(...)</title>
        print("P'bank1",page.text)
        print('soup',soup)
        print("P'bank2",title)
        

        #link = "https://ava.win.clinic/geolocation"
        #f = urllib.urlopen(link)
        #myfile = f.read()
        #print("P'bank -->", myfile)
        x = requests.get("https://ava.win.clinic/geolocation")
        xx = x.json()
        print("P'bank -->",xx)
        
        
        
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get('https://get.geojs.io/', headers=headers)
        ip_request = requests.get('https://get.geojs.io/v1/ip.json', headers=headers)
        ip_address = ip_request.json()['ip']
        print("IP -->", ip_address)
        
        url = 'https://get.geojs.io/v1/ip/geo/' + ip_address +  '.json'
        geo_request = requests.get(url, headers=headers)
        geo_data = geo_request.json()
        
        print("new lati -->", geo_data['latitude'])
        print("new long -->", geo_data['longitude'])
        
        
        
        
        
        key = '7108a77ce6104fc7af3a37227fbace9a'
        url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={key}'
        response = urlopen(url)
        response_bytes = response.read()
        print(type(response_bytes))
        print(response.getheader('Content-Type'))
        response_json = response_bytes.decode()
        print(response_json)

        
        
        
        
        
        url = "https://www.googleapis.com/geolocation/v1/geolocate"
        params = {"key": "AIzaSyBGMY2ya5VHQ8_2GqA31xfKhpfFGOUQGwg"}

        response = requests.post(url, params=params)
        if response.ok:
            location = response.json()["location"]
            latitude = location["lat"]
            longitude = location["lng"]
            accuracy = response.json()["accuracy"]
            print("Latitude:", latitude)
            print("Longitude:", longitude)
            print("Accuracy:", accuracy)
        else:
            print("response:",response)
            print("Error:", response.status_code)
        
        
        
        geolocator = Nominatim(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

        location = geolocator.geocode(geopy.exc.GeocoderTimedOut)
        print("time out --> ")
        print("location --> ", location)
        #latitude = location.latitude
        #longitude = location.longitude
        #print("lati -->> ",latitude, longitude)
        """
        import socket   
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print(s.getsockname()[0])
        s.close()   
        
        

        ip = requests.get('https://api.ipify.org').content.decode('utf8')
        x = request.httprequest.environ['REMOTE_ADDR']
        
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get('https://get.geojs.io/', headers=headers)
        ip_request = requests.get('https://get.geojs.io/v1/ip.json', headers=headers)
        ip_address = ip_request.json()['ip']
        print("IP -->", ip_address)
        url = 'https://get.geojs.io/v1/ip/geo/' + x +  '.json'
        geo_request = requests.get(url, headers=headers)
        geo_data = geo_request.json()
        
        print("new lati -->", geo_data['latitude'])
        print("new long -->", geo_data['longitude'])
        print("xxx->",x)
        print('My public IP address is: {}'.format(ip))
        
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        test = employee_id._attendance_action_change()
        print("yyy-->",test)
        #print(resp_json_payload['results'][0]['geometry']['location'])
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.strategy_update_all_action')
        #action['display_name'] = _("%(name)s's Updates", name=self.name)
        
        

        #gmaps = googlemaps.Client(key='AIzaSyD3nsr3IPMf1VheJjOyujfcDArTtQli0YM') key p'bank
        gmaps = googlemaps.Client(key='AIzaSyD3nsr3IPMf1VheJjOyujfcDArTtQli0YM')

        # Geocoding an address
        geocode_result = gmaps.geocode('คณะแพทย์ศาสตร์ มหาลัยเชียงใหม่')

        # Geolocation
        geolocation_result = gmaps.geolocate(home_mobile_country_code=None,
                                        home_mobile_network_code=None, 
                                        radio_type=None, 
                                        carrier=None,
                                        consider_ip=True, 
                                        cell_towers=None, 
                                        wifi_access_points=None)

        print("Location  : ",geolocation_result)
        print("Geocoding : ")
        pprint(geocode_result)
        return action
    
    def button_done(self):
        for obj in self:
            obj.state = 'done'
            #obj.update_solution_done()
    
    def button_send_approve_strategy(self):
        for obj in self:
            obj.state = 'waiting_approve'
            #obj.parent_id.project_id.is_approve_strategy = True
            obj.start_date = obj.parent_id.start_date
            obj.deadline_date = obj.parent_id.deadline_date
            
    def button_send_approve_solution(self):
        for obj in self:
            if not obj.start_date:
                raise UserError("Please select solution start date")
            if not obj.child_ids:
                raise UserError("Please set Strategy")
            obj.state = 'waiting_approve'
            for strategy_id in obj.child_ids:
                if strategy_id.state == 'open':
                    strategy_id.state = 'waiting_approve'
        
    def button_approve_strategy(self):
        for obj in self:
            #obj.is_approve_strategy = False
            obj.state = 'process'
            
    def button_approve_solution(self):
        for obj in self:
            obj.project_id.get_period_deadline()
            obj.project_id.is_delay = False
            obj.state = 'process'
            for strategy_id in obj.child_ids:
                if strategy_id.state == 'waiting_approve':
                    strategy_id.state = 'process'
    
    def button_reject_strategy(self):
        for obj in self:
            obj.state = 'reject'
            
    def button_reject_solution(self):
        for obj in self:
            obj.state = 'reject'
            for strategy_id in obj.child_ids:
                if strategy_id.state == 'waiting_approve':
                    strategy_id.state = 'reject'   
    
    def button_to_open_strategy(self):
        for obj in self:
            obj.state = 'open'
            
    def button_to_open_solution(self):
        for obj in self:
            obj.state = 'open'
            for strategy_id in obj.child_ids:
                if strategy_id.state == 'reject':
                    strategy_id.state = 'open'
    
    def button_cancel(self):
        for obj in self:
            if obj.is_solution:
                obj.state = 'cancel'
                for strategy_id in obj.child_ids:
                    if strategy_id.state not in ['waiting_approve','done']:
                        strategy_id.state = 'cancel'
                    if strategy_id.state == 'waiting_approve':
                        raise UserError("Please check strategy %s is state in Waiting For Approval"%strategy_id.name)
            if obj.is_strategy:
                obj.state = 'cancel'
                   
    #def button_to_process(self):
        #for obj in self:
            #obj.state = 'process'
            #obj.update_solution_process()
            
    #def update_solution_process(self):
        #for obj in self:
            #obj.parent_id.state = 'process'
            #if obj.project_id.state in ['done','cancel'] and obj.project_id.state != 'delay':
            #    obj.project_id.state = 'process'
               
    #def update_solution_done(self):
    #    for obj in self:
    #        if obj.is_strategy:
    #            is_done = True
    #            for strategy_id in obj.parent_id.child_ids:
    #                if strategy_id.state not in ['done','cancel']:
    #                    is_done = False
    #            if is_done:
    #                obj.parent_id.state = 'done'
                    #obj.update_ccpp_done()
                        
    #def update_ccpp_done(self):
    #    for obj in self:
    #        is_done = True
    #        for solution_id in obj.project_id.tasks_solution:
    #            if solution_id.state not in ['done','cancel']:
    #                is_done = False
    #        if is_done:
    #            obj.project_id.state = 'done'

    def action_open_strategy(self):
        #strategy_ids = self.env['project.task'].search([("parent_id","=",self.id),("is_strategy","=",True)])
        #return {
        #    'name': self.name,
        #    'view_mode': 'tree,form',
        #    'res_model': 'project.task',
        #    'domain': [('id','in',strategy_ids.ids)],
        #    'type': 'ir.actions.act_window',
        #    'context': self._context,
        #    'views' : [(self.env.ref('ccpp.strategy_tree').id, 'tree')]
        #}   
        return {
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'project.task',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context,
            'views' : [(self.env.ref('project.view_task_form2').id, 'form')]
        }          
    
    def action_solution_department_approve_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_solution_approve_dashboard_action')
        department_id = self.env.user.employee_id.department_id
        solution_ids = self.env['project.task'].search([('state', '=', 'waiting_approve'),
                                                        ('project_id.department_id', '=', department_id.id),
                                                        ('is_solution','=',True),
                                                        ('state','=','waiting_approve'),
                                                        ('is_ccpp_on_process','=',True),
                                                        ])
        action['domain'] = [('id','in',solution_ids.ids)]
        return action
    
    def action_strategy_department_approve_manager(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_strategy_approve_dashboard_action')
        department_id = self.env.user.employee_id.department_id
        strategy_ids = self.env['project.task'].search([('state', '=', 'waiting_approve'),
                                                        ('project_id.department_id', '=', department_id.id),
                                                        ('is_strategy','=',True),
                                                        ('state','=','waiting_approve'),
                                                        ('is_ccpp_on_process','=',True),
                                                        ('is_solution_on_approve','=',False),
                                                        ])
        action['domain'] = [('id','in',strategy_ids.ids)]
        return action

class ProjectUpdate(models.Model):
    _inherit = "project.update"
    _order = 'date desc, id desc'
    
    strategy_id = fields.Many2one("project.task", string="Strategy")
    solution_id = fields.Many2one("project.task", string="Solution", related="strategy_id.parent_id", store=True)
    project_id = fields.Many2one(required=False, default=False, related="strategy_id.project_id", store=True)
    customer_id = fields.Many2one("res.partner", string="Customer", required=True)
    location = fields.Char("Location")
    code = fields.Char("Situation No.")
    date = fields.Datetime(default=lambda self: fields.datetime.now(), tracking=True)
    next_action = fields.Char(string="Next Action")
    task_id = fields.Many2one("account.analytic.line", string="Tasks")
    latitude = fields.Float(string="Latitude", digits=(12,6))
    longitude = fields.Float(string="Longitude", digits=(12,6))

    def unlink(self):
        res = super().unlink()
        raise UserError("ระบบไม่สามารถลบเอกสารได้")

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProjectUpdate,self).create(vals_list)
        for update in res:
            update.strategy_id.sudo().last_situation_id = update
            update.strategy_id.parent_id.sudo().last_situation_solution_id = update
            update.strategy_id.sudo().next_action = update.next_action
            update.strategy_id.parent_id.sudo().next_action_solution = update.next_action
            update.strategy_id.project_id.sudo().next_action = update.next_action
            if not update.code:
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                try:
                    #sequence_code = 'ccpp.'+'ta.'+update.strategy_id.project_id.department_id.code
                    sequence_code = 'ccpp.'+'ta.'
                except:
                    raise UserError("Please Check Sequence")
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                update.code = code or 'New'
            update.strategy_id.state = 'process'
            update.update_solution_process()
        return res
    
    def update_solution_process(self):
        for obj in self:
            if obj.strategy_id.parent_id.state == 'open':
                obj.strategy_id.parent_id.state = 'process'

    def unlink(self):
        strategies = self.strategy_id
        solutions = self.solution_id
        ccpps = self.project_id
        res = super().unlink()
        for strategy_id in strategies:
            last_situation_id = self.search([('strategy_id', "=", strategy_id.id)], order="date desc", limit=1)
            strategy_id.last_situation_id = last_situation_id
            strategy_id.next_action = last_situation_id.next_action
        for solution_id in solutions:
            last_situation_solution_id = self.search([('solution_id', "=", solution_id.id)], order="date desc", limit=1)
            solution_id.last_situation_solution_id = last_situation_solution_id
            solution_id.next_action_solution = last_situation_solution_id.next_action_solution
        for ccpp in ccpps:
            last_situation_ccpp_id = self.search([('project_id', "=", solution_id.id)], order="date desc", limit=1)
            ccpp.next_action = last_situation_ccpp_id.next_action
        return res

    def default_get(self, fields):
        #result.pop('project_id')
        result = super().default_get(fields)
        if result.get('project_id') and self._context.get('update_strategy'):
            #result.update({'strategy_id':   result.get('project_id')})
            result.pop('project_id')
        print("Y"*100)
        if 'strategy_id' in fields and not result.get('strategy_id') and not self.env.context.get("update_task"):
            print("Y"*100)
            strategy = self.env.context.get('active_id')
            result['strategy_id'] = strategy
            strategy_id = self.env['project.task'].browse(strategy)
            result['project_id'] = strategy_id.project_id.id
            result['solution_id'] = strategy_id.parent_id.id
            result['customer_id'] = strategy_id.project_id.partner_id.id
        if 'task_id' in fields and self.env.context.get("update_task"):
            task = self.env.context.get('task_id')
            result['task_id'] = task
            task_id = self.env['account.analytic.line'].browse(task)
            result['project_id'] = task_id.project_id.id
            result['solution_id'] = task_id.task_id.id
            result['strategy_id'] = task_id.task_strategy_id.id
            result['customer_id'] = task_id.customer_id.id

        return result
    
    # overide change color
    @api.depends('status')
    def _compute_color(self):
        for update in self:
            update.color = STATUS_COLOR[update.status]
            
    def get_location(self):
        latitude = self.env.context.get("latitude", False)
        longitude = self.env.context.get("longitude", False)
        print("la-->",latitude)
        print("long-->",longitude)
        self.latitude = latitude
        self.longitude = longitude