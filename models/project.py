from email.policy import default
from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from odoo.addons.project.models.project_update import ProjectUpdate

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
    'process': 3,  # orangeq
    'done': 20,  # red / danger
    'cancel': 23,  # light blue
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
    sale_team_id = fields.Many2one("crm.team", string="Sale Team", default="_get_default_sale_team")
    partner_contact_id = fields.Many2one("res.partner", string="Host of CCPP")
    domain_partner_contact_ids = fields.Many2many("res.partner", string="Domain partner contact", compute="_compute_domain_partner_contact_ids")
    domain_task_solution_ids = fields.Many2many('project.task', string="Domain task solution")
    tasks_solution = fields.One2many('project.task', 'project_solution_id', string="Solution", context={'is_solution': True})
    name = fields.Char(string="Name of CCPP")
    user_id = fields.Many2one(string="CCPP User")
    job_position_id = fields.Many2one("res.partner.position", string="Host of CCPP")
    domain_job_position_ids = fields.Many2many("res.partner.position", string="Domain Job Position", compute="_compute_domain_job_position_ids")
    color = fields.Integer(related="priority_id.color", store=True)
    
    ## impact customer ##
    is_income_cus = fields.Boolean("Income/Funding", default=False)
    is_effectiveness_cus = fields.Boolean("Effectiveness/Personal Performance", default=False)
    is_repulation_cus = fields.Boolean("Repulation", default=False)
    is_competitive_cus = fields.Boolean("Competitive Advantage", default=False)
    is_critical = fields.Boolean("Need help Now!", default=False)
    is_not_critical = fields.Boolean("I can wait", default=False)
    
    ## impact winmed ##
    is_income_comp = fields.Boolean("Sale Revenue/Cost", default=False)
    is_effectiveness_comp = fields.Boolean("Effectiveness/Personal Performance", default=False)
    is_repulation_comp = fields.Boolean("Repulation", default=False)
    is_competitive_comp = fields.Boolean("Competitive Advantage", default=False)
    is_short_time = fields.Boolean("Short")
    is_long_time = fields.Boolean("Long")
    
    is_verify_impact_cus = fields.Boolean("Verify impact Customer", default=False)
    is_stamp_record = fields.Boolean("Aready have record", default=False)
    show_critical = fields.Char(string="Customer Impact", compute="_compute_show_time")
    show_time = fields.Char(string="Period", compute="_compute_show_time")
    code = fields.Char(string="Code")
    period_id = fields.Many2one("ccpp.period", string="Priority Period", compute="_get_priority", store=True)
    deadline_date = fields.Date(string="Deadline")
    state = fields.Selection([
        ('open', 'Open'),
        ('waiting_approve', 'Waiting Approve'),
        ('process', 'On Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('delay', 'delayed'),
    ], default='open', index=True, string="State", track_visibility="onchange", tracking=True)
    
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
                
    #@api.onchange("is_critical", "is_not_critical", "is_short_time", "is_long_time")       
    #def onchange_unique(self):
        #if self.is_critical and self.is_not_critical:
            #raise UserError("กรุณาเลือกความเร่งด่วนอย่างใดอย่างหนึ่ง")
        #if self.is_short_time and self.is_long_time:
            #raise UserError("กรุณาเลือกระยะเวลาในการแก้ปัญหาใดอย่างหนึ่ง")
    
    @api.onchange("is_critical") 
    def onchange_is_critical(self):
        if self.is_critical:
            self.is_not_critical = False
            
    @api.onchange("is_not_critical") 
    def onchange_is_not_critical(self):
        if self.is_not_critical:
            self.is_critical = False
            self.is_income_comp = False
            self.is_effectiveness_comp = False
            self.is_repulation_comp = False
            self.is_competitive_comp = False
            self.is_long_time = False
            self.is_short_time = False

    @api.onchange("is_short_time") 
    def onchange_is_short_time(self):
        if self.is_short_time:
            self.is_long_time = False
            
    @api.onchange("is_long_time") 
    def onchange_is_long_time(self):
        if self.is_long_time:
            self.is_short_time = False    
    
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
            if not employee_id:
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
            sequence_code = 'ccpp.'+'cp.'+self.department_id.code
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
            sequence_code = 'ccpp.'+'cp.'+self.department_id.code
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
            obj.state = 'waiting_approve'
        
    def button_approve(self):
        for obj in self:
            obj.state = 'process'
        
    def button_reject(self):
        for obj in self:
            obj.state = 'open'
        
    def button_done(self):
        for obj in self:
            obj.state = 'done'
        
    def button_cancel(self):
        for obj in self:
            obj.state = 'cancel'
            for solution_id in obj.tasks_solution:
                if solution_id.state != 'done':
                    solution_id.state = 'cancel'
                for strategy_id in solution_id.child_ids:
                    if strategy_id.state != 'done':
                        strategy_id.state = 'cancel'
        
    def button_to_open(self):
        for obj in self:
            obj.state = 'open'
            for solution_id in obj.tasks_solution:
                solution_id.state = 'open'
                for strategy_id in solution_id.child_ids:
                    strategy_id.state = 'open'
            
    def check_ccpp_delayed(self):
        date_today = datetime.now().strftime("%Y-%m-%d")
        ccpp_ids = self.env['project.project'].search([('state','=','process'),('deadline_date','<',date_today)])
        ccpp_ids.write({'state': 'delay'})
       
    # overide change color 
    @api.depends('last_update_status')
    def _compute_last_update_color(self):
        for project in self:
            project.last_update_color = STATUS_COLOR[project.last_update_status]
        
class Task(models.Model):
    _inherit = "project.task" 
    #_rec_name = "code"
    
    def _get_default_level(self):
        if self._context.get('is_create_solution'):
            return True
        else:
            return False
    
    is_solution = fields.Boolean(string='Is Solution', default=_get_default_level, compute="_compute_level")
    is_strategy = fields.Boolean(string='Is Strategy', default=False, compute="_compute_level")
    is_task = fields.Boolean(string='Is Task', default=False, compute="_compute_level")
    is_subtask = fields.Boolean(string='Is SubTask', default=False, compute="_compute_level")
    project_solution_id = fields.Many2one("project.project", string="Relate Project Solution")
    code = fields.Char(string="Code")
    period_id = fields.Many2one("ccpp.period", string="Priority Period", related="project_id.period_id")
    partner_id = fields.Many2one(related="project_id.partner_id")
    job_position_id = fields.Many2one("res.partner.position", string="Host of CCPP",related="project_id.job_position_id")
    priority_id = fields.Many2one("ccpp.priority", string="Priority", related="project_id.priority_id")
    evaluate_method = fields.Char("วิธีวัดผล")
    situation_ids = fields.One2many("project.update", 'strategy_id', string="Current Situation")
    last_situation_id = fields.Many2one("project.update", string="Last Update Situation Strategy") # last update at strategy
    last_situation_solution_id = fields.Many2one("project.update", string="Last Update Situation Solution") # last update at solution
    state = fields.Selection([
        ('open', 'Open'),
        ('process', 'On Process'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
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
            print("project ------>", rec.project_id)
            print("project solution ------>", rec.project_solution_id)
            
            if rec.is_solution:
                rec.project_id = rec.project_solution_id
            if rec.is_solution and rec.project_id.department_id:
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                sequence_code = 'ccpp.'+'sl.'+rec.project_id.department_id.code
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                rec.code = code
            if rec.is_strategy and rec.project_id.department_id:
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                sequence_code = 'ccpp.'+'st.'+rec.project_id.department_id.code
                code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
                rec.code = code
            #if rec.is_task and rec.project_id.department_id:
            #    sequence_date = datetime.now().strftime("%Y-%m-%d")
            #    sequence_code = 'ccpp.'+'ta.'+rec.project_id.department_id.code
            #    code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
            #    rec.code = code
            if rec.parent_id:
                rec.project_id = rec.parent_id.project_id.id
            

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
        return action
    
    def button_open_project(self): 
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.open_view_project_all_ccpp')
        action['res_id'] = self.project_id.id
        return action
    
    def action_open_task2(self):
        return {
            'view_mode': 'form',
            'res_model': 'project.task',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }
    
    def solution_update_all_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.solution_update_all_action')
        #action['display_name'] = _("%(name)s's Updates", name=self.name)
        return action
    
    def button_update_strategy(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.strategy_update_all_action')
        #action['display_name'] = _("%(name)s's Updates", name=self.name)
        return action
    
    def button_done(self):
        for obj in self:
            obj.state = 'done'
            obj.update_solution_done()
        
    def button_cancel(self):
        for obj in self:
            obj.state = 'cancel'
            if obj.is_solution:
                for strategy_id in obj.child_ids:
                    if strategy_id.state != 'done':
                        strategy_id.state = 'cancel'
            if obj.is_strategy:
                obj.update_solution_done()
                   
    def button_to_process(self):
        for obj in self:
            obj.state = 'process'
            obj.update_solution_process()
            
    def update_solution_process(self):
        for obj in self:
            obj.parent_id.state = 'process'
            #if obj.project_id.state in ['done','cancel'] and obj.project_id.state != 'delay':
            #    obj.project_id.state = 'process'
               
    def update_solution_done(self):
        for obj in self:
            if obj.is_strategy:
                is_done = True
                for strategy_id in obj.parent_id.child_ids:
                    if strategy_id.state not in ['done','cancel']:
                        is_done = False
                if is_done:
                    obj.parent_id.state = 'done'
                    #obj.update_ccpp_done()
                        
    #def update_ccpp_done(self):
    #    for obj in self:
    #        is_done = True
    #        for solution_id in obj.project_id.tasks_solution:
    #            if solution_id.state not in ['done','cancel']:
    #                is_done = False
    #        if is_done:
    #            obj.project_id.state = 'done'

class ProjectUpdate(models.Model):
    _inherit = "project.update"
    _order = 'date desc, id desc'
    
    strategy_id = fields.Many2one("project.task", string="Strategy")
    solution_id = fields.Many2one("project.task", string="Solution", related="strategy_id.parent_id")
    project_id = fields.Many2one(required=False, default=False, related="strategy_id.project_id")
    location = fields.Char("Location")
    code = fields.Char("Situation No.")
    date = fields.Datetime(default=lambda self: fields.datetime.now(), tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProjectUpdate,self).create(vals_list)
        for update in res:
            update.strategy_id.sudo().last_situation_id = update
            update.strategy_id.parent_id.sudo().last_situation_solution_id = update
            if not update.code:
                sequence_date = datetime.now().strftime("%Y-%m-%d")
                try:
                    sequence_code = 'ccpp.'+'ta.'+update.strategy_id.project_id.department_id.code
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
        res = super().unlink()
        for strategy_id in strategies:
            strategy_id.last_situation_id = self.search([('strategy_id', "=", strategy_id.id)], order="date desc", limit=1)
        for solution_id in solutions:
            solution_id.last_situation_solution_id = self.search([('solution_id', "=", solution_id.id)], order="date desc", limit=1)
        return res

    def default_get(self, fields):
        #result.pop('project_id')
        result = super().default_get(fields)
        if result.get('project_id') and self._context.get('update_strategy'):
            #result.update({'strategy_id':   result.get('project_id')})
            result.pop('project_id')
        print("Y"*100)
        if 'strategy_id' in fields and not result.get('strategy_id'):
            print("Y"*100)
            result['strategy_id'] = self.env.context.get('active_id')
            strategy = self.env.context.get('active_id')
            strategy_id = self.env['project.task'].browse(strategy)
            result['solution_id'] = strategy_id.parent_id.id
            result['project_id'] = strategy_id.project_id.id
        return result
    
    # overide change color
    @api.depends('status')
    def _compute_color(self):
        for update in self:
            update.color = STATUS_COLOR[update.status]