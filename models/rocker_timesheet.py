# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (C) 2021-Antti Kärki.
#    Author: Antti Kärki.
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import dataclasses
from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, AccessError, Warning
from odoo import tools
from datetime import timedelta, datetime, date, time, timezone
from dateutil.rrule import rrule, DAILY
from odoo.osv import expression
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import requests
from pprint import pprint
import googlemaps
import math

import logging

_logger = logging.getLogger(__name__)
# Default star/stop/amount/duration if compny or user default are not set
# set values to be created in _get_defaults method
default_start_time = 9
default_end_time = 17.0
default_duration = 8.0  # contains lunch hours
default_unit_amount = 7.5  # lunch not paid
default_rolling_amount = 1
default_time_roundup = -1

project_change = True
user_values = [(0, 0, 'filter', False)]         # this is like cookie pool or user context because I can not use those
daystocreate = 0
prev_company = -1

# btw....remember to check odoo global defaults....working day, is it 8 or 7.5 hours...has to be in sync with rocker company / user defaults


STATE_COLOR = {
    'open': 0,
    'done': 20,
    'cancel': 23,
}

class RockerTimesheet(models.Model):
    _inherit = ['account.analytic.line','mail.thread','portal.mixin','mail.activity.mixin']
    _name = 'account.analytic.line'
    _order = "start desc"
    #_rec_name = "display_name"

    @api.model
    def _default_company_id(self):
        #if self._context.get('default_project_id'):
        #    return self.env['project.project'].browse(self._context['default_project_id']).company_id
        return self.env.company

    @api.model
    def _default_user(self):
        # _logger.debug('_default_user')
        return self.env.context.get('user_id', self.env.user.id)

    @api.depends("customer_id","priority_id")
    def _domain_project_id(self):
        #domain = [('allow_timesheets', '=', True)]
        # odoo 14
        # return expression.AND([domain,
        #                        ['|', ('privacy_visibility', '!=', 'followers'), ('allowed_internal_user_ids', 'in', self.env.user.ids)]
        #                        ])
        # odoo 15
        #return expression.AND([domain,
        #                       ['|', ('privacy_visibility', '!=', 'followers'), ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
        #                       ])
        for obj in self:
            domain = []
            domain_project = []
            ccpp_ids = self.env['project.project']
            if obj.customer_id:
                domain = [('employee_id','=',obj.employee_id.id),
                          ('state','=','process'),
                          ('company_id','=',obj.company_id.id)
                          ]
                domain.append(('partner_id','=',obj.customer_id.id))
                if obj.priority_id:
                    domain.append(('priority_id','=',obj.priority_id.id))
                ccpp_ids = self.env['project.project'].search(domain)
            domain_project = (['id','in',ccpp_ids.ids])
            
            return domain_project
        
    def _domain_project_test_id(self):
        ccpp_ids = self.env['project.project'].search([('user_id','=',self.env.user.id)])
        domain = [('id', 'in', ccpp_ids.ids)]
        return domain

    def _domain_project_id_search(self):
        #company_ids = self._context.get('allowed_company_ids')
        #domain = [('company_id', 'in', company_ids)]
        #domain = [('company_id', '=', self.env.company.id)]
        domain = [('company_id', 'in', self.env.user.company_ids.ids)]
        return domain

    def _set_rolling(self, bset):
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][3] = bset
                _bfound = True
        if not _bfound:
            values1 = [_i, 0, '', False]
            user_values.append(values1)
        return True

    def _get_rolling(self):
        _i = 0
        _brolling = False
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _brolling = user_values[i][3]
                _bfound = True
        if not _bfound:
            # _logger.debug('Rolling factor not found')
            return False
        # _logger.debug('Rolling Factor: ' + str(_brolling))
        return _brolling

    def _set_search_id(self, id):
        _logger.debug('Setting search Id: ' + str(id))
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][1] = id  # selected task_id
                _bfound = True
        if not _bfound:
            values1 = [_i, id, '', False]
            user_values.append(values1)
        return True

    def _get_search_id(self):
        _i = 0
        _selected_id = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _selected_id = user_values[i][1]
                _bfound = True
        if not _bfound:
            # _logger.debug('Selected id not found')
            return -1
        # _logger.debug('Searchpanel selected id: ' + str(_selected_id))
        return _selected_id

    def _domain_get_search_filter(self):
        _i = 0
        _filt = ""
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _filt = user_values[i][2]
                _bfound = True
        if not _bfound:
            # _logger.debug('filter not found')
            return ""
        # _logger.debug('Returning _search_panel_filter: ' + str(_filt))
        return _filt

    def _domain_set_search_filter(self, filt):
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][2] = filt
                _bfound = True
        if not _bfound:
            values1 = [_i, 0, filt, False]
            user_values.append(values1)
        return True

    def _domain_get_search_domain(self, filt):
        # default = all
        _search_panel_domain = [('company_id', '=', self.env.company.id)]  # ok
        print("True"*100)
        if filt == 'all':
            _search_panel_domain = _search_panel_domain + []
        elif filt == 'member':
            # odoo 14
            # _search_panel_domain = _search_panel_domain + [('project_id', 'in', self.env['project.project'].search([('allowed_internal_user_ids', 'in', self.env.user.ids)]).ids)]
            # odoo 15
            _search_panel_domain = _search_panel_domain + [('project_id', 'in', self.env['project.project'].search([('message_partner_ids', 'in', [self.env.user.partner_id.id])]).ids)]
        elif filt == 'internal':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'internal')]).ids)]
        elif filt == 'billable':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'billable')]).ids)]
        elif filt == 'nonbillable':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'nonbillable')]).ids)]
        elif filt == 'mine':
            # odoo 14
            # _search_panel_domain = _search_panel_domain + \
            #                        ['|',
            #                         ('task_id', 'in',
            #                          self.env['project.task'].search([('user_id', '=', self.env.user.id)]).ids),
            #                         '&', ('task_id', '=', False),
            #                         ('project_id', 'in', self.env['project.task'].search(
            #                             [('user_id', '=', self.env.user.id)]).project_id.ids),
            #                         ]
            # odoo 15
            _search_panel_domain = _search_panel_domain + \
                                   ['|',
                                    ('task_id', 'in', self.env['rocker.task'].search([('user_id', '=', self.env.user.id)]).ids),
                                    '&',  ('task_id', '=', False),
                                    ('project_id', 'in', self.env['rocker.task'].search([('user_id', '=', self.env.user.id)]).project_id.ids),
                                    ]

        else:
            self._domain_get_search_domain('all')
        # odoo 14
        # _search_panel_domain = expression.AND([_search_panel_domain,
        # ['|', ('privacy_visibility', '!=', 'followers'), ('project_id.allowed_internal_user_ids', 'in', self.env.user.ids)]
        # ])
        # odoo 15
        _search_panel_domain = expression.AND([_search_panel_domain,
                                               ['|', ('privacy_visibility', '!=', 'followers'), ('project_id.message_partner_ids', 'in', [self.env.user.partner_id.id])]
                                               ])
        return _search_panel_domain

    def _get_defaults(self):
        # _logger.debug('_get_defaults')
        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup


        _defaults = None
        _company_defaults = None
        _company_defaults = self.env['rocker.company.defaults'].search([('company_id', '=', self.env.company.id)])
        _defaults = self.env['rocker.user.defaults'].search(
            [('user_id', '=', self.env.user.id), ('company_id', '=', self.env.company.id)]) \
                    or self.env['rocker.company.defaults'].search([('company_id', '=', self.env.company.id)])
        if _defaults:

            default_start_time = _defaults.rocker_default_start or _company_defaults.rocker_default_start
            default_end_time = _defaults.rocker_default_stop or _company_defaults.rocker_default_stop
            default_duration = (_defaults.rocker_default_stop - _defaults.rocker_default_start) or (_company_defaults.rocker_default_stop - _company_defaults.rocker_default_start)
            default_unit_amount = _defaults.rocker_default_work or _company_defaults.rocker_default_work or 7.5
            default_rolling_amount = _defaults.rocker_default_rolling_work or _company_defaults.rocker_default_rolling_work or 1
            default_time_roundup = int(_defaults.rocker_round_up) or int(_company_defaults.rocker_round_up) or 0
        else:
            _logger.debug('No defaults, creating company defaults')
            _start = self.to_UTC(9)
            _end = self.to_UTC(17)
            self.env['rocker.company.defaults'].sudo().create({
                'company_id': self.env.company.id,
                'rocker_default_start': _start,
                'rocker_default_stop': _end,
                'rocker_default_work': 7.5,
                'rocker_round_up': '0',
                'rocker_default_rolling_work': 1
            })
            self._get_defaults()
        return True

    def _default_start(self):
        _logger.debug('_set_default_start')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_date(self):
        _logger.debug('_set_default_date')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_stop(self):
        _logger.debug('_set_default_stop')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_duration(self):
        _logger.debug('_set_default_duration')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_work(self):
        _logger.debug('_set_default_work')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _calculate_duration(self, start, stop):
        # _logger.debug('_calculate_duration')
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)

    def _default_name(self):
        # _logger.debug('_default_name')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                return str(search_task.name) + ': '
        else:
            return None

    def _default_task_solution(self):
        # _logger.debug('_default_task')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0 and search_task.is_solution:
                return search_task.id
            elif search_task.id > 0 and search_task.is_strategy:
                return search_task.parent_id.id
        return None
    
    def _default_task_strategy(self):
        # _logger.debug('_default_task')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0 and search_task.is_strategy:
                return search_task.id
        return None

    
    def _default_project(self):
        # _logger.debug('_default_project')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                return search_task.project_id
        return None
    
    def _default_customer(self):
        # _logger.debug('_default_project')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                return search_task.project_id.partner_id
        return None

    def _domain_customer(self):
        customer_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)]).mapped('customer_id')
        domain = [('id', 'in', customer_ids.ids)]   
        return domain
    
    def _get_default_customer(self):
        customer_id = self.env['res.partner']
        if self._context.get('default_customer_id'):
            customer_id = self._context.get('default_customer_id')
        return customer_id
    
    #def _get_default_checkin_date(self):
    #    checkin_date = False
    #    if self._context.get('default_checkin_date'):
    #        checkin_date = datetime.now()
    #    return checkin_date
            
    def _get_default_job(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        #if not employee_id:
            #raise UserError("Not recognize the Employee. Please Configure User to Employee to get the job")
        return employee_id.job_id

    def _get_default_job_ids(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id.job_id

    def _get_default_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id
    
    def _get_default_employee_ids(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id

    # existing fields
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id, store=True,
                                 required=True)
    #task_id = fields.Many2one(
    #    'project.task', 'Task', compute='_compute_task_id', store=True, readonly=False, index=True,
    #    domain="[('company_id', '=', company_id), ('project_id.allow_timesheets', '=', True), ('project_id', '=?', project_id)]")
    task_id = fields.Many2one(
        'project.task', string='Solution', default=_default_task_solution, related="temp_task_id" ,store=True, readonly=False, index=True)
    temp_task_id = fields.Many2one(
        'project.task', string='Solution')
    task_strategy_id = fields.Many2one(
        'project.task', string='Strategy', default=_default_task_strategy, readonly=False, index=True)
    
    #project_id = fields.Many2one(
    #    'project.project', 'Project', compute='_compute_project_id', store=True, readonly=False,
    #    domain=_domain_project_id)
    
    project_id = fields.Many2one(
        'project.project', string='CCPP', default=_default_project, related="temp_project_id", readonly=False, store=True)
    temp_project_id = fields.Many2one(
        'project.project', string='CCPP') # add temp field because can't edit domain in project
    # name = fields.Char('Comments', required=False, default=_default_name)
    name = fields.Char(required=False, default=_default_name)

    # new fields
    display_name = fields.Text('Display Name', required=False, store=False, compute='_compute_display_name')
    rocker_type = fields.Selection([
        ('internal', 'Internal'),
        ('billable', 'Billable'),
        ('nonbillable', 'Non Billable'),
        ('time_off', 'Time Off'),
    ], 'Project Type', required=False, default='', store=False,
        related='project_id.rocker_type', compute='_compute_rocker_type')
    task_search = fields.Many2one(
        'rocker.task', 'Project', store=True, readonly=False, required=False)
    customer_potential = fields.Many2one(
        'customer.potential', 'Customer Potential', store=True, readonly=False, required=False)
    rocker_search_type = fields.Selection([
        ('all', 'All'),
        ('mine', 'My Tasks'),
        ('billable', 'Billable'),
        ('nonbillable', 'Non Billable')], 'Search Type', store=False, required=False, default='all')
    # required fields
    # changed to non required, we handle this in views, (otherwise old timesheet app does not work)
    start = fields.Datetime(
        # 'Start', required=False, readonly=False, default=_default_start, store=True,
        'Start', required=False, readonly=False, default=_default_start, store=True,
        help="Start datetime of a task")
    stop = fields.Datetime(
        'Stop', required=False, readonly=False, default=_default_stop, store=True,
        # 'Stop', required=False, readonly=False, store=True,
        help="Stop datetime of a task")
    allday = fields.Boolean('All Day', default=False, required=False)  # required in order calendar to work
    #
    daystocreateshow = fields.Integer('Generate', required=False, readonly=True, store=False,
                                      help="Create number of timeheet rows")
    duration = fields.Float('Duration', store=True, readonly=False, default=_default_duration, required=True, help="Work duration in hours")

    # existing fields
    # date = fields.Date('Date', required=True, index=True, default=_default_date, store=True)
    date = fields.Date('Date', required=True, index=True, store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    #employee_id = fields.Many2one('hr.employee', "Employee",
    #                              default=lambda self: self.env['hr.employee'].search(
    #                                  [('user_id', '=', self.env.user.id),
    #                                   ('company_id', '=', self.env.company.id)]).id, store=True)
    employee_id = fields.Many2one("hr.employee", string="User", default=_get_default_employee, track_visibility="onchange")
    employee_ids = fields.Many2many("hr.employee", "task_hr_employee_rel", "task_id", "employee_id", string="Task Team", default=_get_default_employee_ids, track_visibility="onchange", required=True)
    department_id = fields.Many2one('hr.department', "Department", compute='_compute_department_id', store=True,
                                    compute_sudo=True)
    unit_amount = fields.Float('Actual Work', default=_default_work, required=True, help="Work amount in hours")
    customer_id = fields.Many2one("res.partner", string="Customer", required=True, default=_get_default_customer)
    domain_customer_ids = fields.Many2many("res.partner", string="Domain Customer", compute="_compute_domain_customer_ids")
    customer_potential_id = fields.Many2one("res.partner", string="Customer Potential")
    state = fields.Selection(selection=[
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='open', string="Status")
    state_char = fields.Char(string="State", compute="_compute_state_char", store=True)
    account_id = fields.Many2one(required=False)
    is_go_ccpp_customer = fields.Boolean("CCPP Customer")
    is_go_potential = fields.Boolean("Potential")
    priority_id = fields.Many2one('ccpp.priority', string="Priority")
    domain_ccpp_ids = fields.Many2many("project.project", string="Domain CCPP", compute="_compute_domain_ccpp_ids")
    domain_solution_ids = fields.Many2many("project.task", string="Domain Solution", compute="_compute_domain_solution_ids")
    domain_strategy_ids = fields.Many2many("project.task", string="Domain Strategy", compute="_compute_domain_strategy_ids")
    log_lines = fields.One2many("account.analytic.line.log", "analytic_line_id", string="Log")
    current_action = fields.Char("Current Situation")
    next_action = fields.Char("Next Action")
    location = fields.Char("Location", compute="_compute_location")
    note = fields.Text("Note")
    checkin_date = fields.Datetime(string="Check In Date")
    
    department_id = fields.Many2one("hr.department",string="Department", related="employee_id.department_id", store=True, track_visibility="onchange")
    division_id = fields.Many2one("hr.department",string="Department", related="employee_id.division_id", store=True, track_visibility="onchange")
    job_id = fields.Many2one("hr.job", string="Job Position", default=_get_default_job, required=True, track_visibility="onchange")#default=_get_default_job, 
    domain_job_ids = fields.Many2many("hr.job", string="Domain Job", compute="_compute_domain_job_ids")
    job_ids = fields.Many2many("hr.job", "task_hr_job_rel", "task_id", "job_id", string="Task Team", default=_get_default_job_ids, track_visibility="onchange", required=True)

    state_color = fields.Integer(compute='_compute_state_color')
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    diff_distance = fields.Float(string="Diff.Distance(Km.)", compute="_compute_distance")
    is_diff_distance = fields.Boolean(string="Is Diff", compute="_compute_distance")
    
    is_owner = fields.Boolean(string="Is Owner", compute="_compute_is_owner")

    @api.depends('job_id')
    def _compute_is_owner(self):
        for obj in self:
            is_owner = False
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            if obj.job_id in employee_id.job_id:
                is_owner = True
            obj.is_owner = is_owner

    @api.depends("employee_id")
    def _compute_domain_job_ids(self):
        for obj in self:
            job_ids = self.env['hr.job']
            if obj.sale_person_id:
                for job_id in obj.sale_person_id.job_id:
                    job_ids |= job_id
            obj.domain_job_ids = job_ids.ids
            
    @api.depends("state")
    def _compute_state_char(self):
        for obj in self:
            states = {'open': 'Open',
                      'done': 'Done',
                      'cancel': 'Cancelld',}
            obj.state_char = states[obj.state]

    def duplicate_task(self):
        for obj in self:
            new_task = obj.copy()
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.act_rocker_timesheet_calendar')
        action['context'] = self._context 
        return action
        #return {
        #    'name': new_task.name,
        #    'view_mode': 'calendar',
        #    'res_model': 'account.analytic.line',
        #    'type': 'ir.actions.act_window',
        #    'context': self._context,
        #    'views' : [(self.env.ref('ccpp.rocker_timesheet_calendar').id, 'calendar')],
        #    'target' : 'main'
        #}  

    @api.onchange("is_go_ccpp_customer") 
    def onchange_is_go_ccpp_customer(self):
        for obj in self:
            if obj.is_go_ccpp_customer:
                obj.is_go_potential = False
                obj.customer_id = False
                
    @api.onchange("is_go_potential") 
    def onchange_is_go_potential(self):
        for obj in self:
            if obj.is_go_potential:
                obj.is_go_ccpp_customer = False
                obj.customer_id = False
                
    @api.depends("customer_id","priority_id")
    def _compute_domain_ccpp_ids(self):
        for obj in self:           
            domain = []
            ccpp_ids = self.env['project.project']
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            if obj.customer_id:
                domain = [('employee_ids','in',[employee_id.id]),('state','=','process')]
                domain.append(('partner_id','=',obj.customer_id.id))
                if obj.priority_id:
                    domain.append(('priority_id','=',obj.priority_id.id))
                ccpp_ids = self.env['project.project'].search(domain)
            obj.domain_ccpp_ids = ccpp_ids.ids
            
    @api.depends("project_id")
    def _compute_domain_solution_ids(self):
        for obj in self:           
            domain = [('state','=','process')]
            if obj.project_id:
                domain.append(('project_id','=',obj.project_id.id))
            solution_ids = self.env['project.task'].search(domain)
            obj.domain_solution_ids = solution_ids.ids
            
    @api.depends("project_id","task_id")
    def _compute_domain_strategy_ids(self):
        for obj in self:
            domain = [('state','=','process')]
            if obj.project_id:
                domain.append(('project_id','=',obj.project_id.id))
            if obj.task_id:
                domain.append(('parent_id','=',obj.task_id.id))
            strategy_ids = self.env['project.task'].search(domain)
            obj.domain_strategy_ids = strategy_ids
                             
    @api.depends("is_go_ccpp_customer","is_go_potential","priority_id")
    def _compute_domain_customer_ids(self):
        for obj in self:
            customer_ids = self.env['res.partner']
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            #if obj.is_go_ccpp_customer:
            #    customer_ids = self.env['project.project'].search([('user_id','=',self.env.user.id),
            #                                                       ('state','=','process')]).mapped('partner_id')
            if obj.is_go_ccpp_customer and obj.priority_id:
                customer_ids = self.env['project.project'].search([('employee_ids','in', [employee_id.id]),
                                                                   ('state','=','process'),
                                                                   ('priority_id','=',obj.priority_id.id)]).mapped('partner_id')
            if obj.is_go_potential:
                year = str(datetime.now().year)
                customer_ids = self.env['ccpp.customer.information'].search([('sale_person_id','=', employee_id.id),
                                                                             ('active','=',True),
                                                                             ('year_selection','=',year),
                                                                             ('type','in',['customer','external'])], order="potential_ranking").mapped('customer_id')
                customer_ids |= self.env['ccpp.customer.information'].search([('sale_person_id','=', employee_id.id),
                                                                             ('active','=',True),
                                                                             ('year_selection','=',year),
                                                                             ('type','in',['internal'])], order="potential_ranking").mapped('partner_id')
            obj.domain_customer_ids = customer_ids.ids
    
    def _compute_customer(self):
        customer_ids = self.env['ccpp.customer.information'].search([('user_id','=',self.env.user.id)]).mapped('customer_id')
        domain = [('id', 'in', customer_ids.ids)]
        return customer_ids
    
    
    # 2022

    # def init(self):
    #     # when module is installed or upgraded
    #     _logger.debug('init')

    # def __init__(self, pool, cr):
    #     # when server starts or restarted
    #     _logger.debug('Rocker: __init__')
    #     return super().__init__(pool, cr)

    @api.depends('task_id', 'task_id.project_id')
    def _compute_project_id(self):
        # _logger.debug('api depends task')
        if not self.task_id and self._get_search_id() > 0:
            search_task = self.env['project.task'].search([('id', '=', self._get_search_id())], limit=1)
            if not search_task.id:
                # _logger.debug('Task not found from project.task...')
                return False
            self.task_id = search_task.id
            self.project_id = search_task.project_id

    @api.depends('project_id')
    def _compute_task_id(self):
        # _logger.debug('api depends project')
        for line in self.filtered(lambda line: not line.project_id):
            line.task_id = False

    @api.depends('name','unit_amount')
    def _compute_display_name(self):
        # _logger.debug('api depends name')
        #for line in self:
            #line.display_name = "%s %s %s %s %0.1f %s" % (line.task_id.name , ': ' , line.name, ' - ', line.unit_amount or 0, ' h')
        for line in self:
            line.display_name = "%s - %s" % (line.name,line.customer_id.name)

    @api.depends('user_id')
    def _compute_employee_id(self):
        # _logger.debug('api depends user_id')
        for line in self.filtered(lambda line: not line.employee_id):
            line.employee_id = line.user_id.employee_id

    @api.depends('department_id')
    def _compute_department_id(self):
        # _logger.debug('api depends department_id')
        for line in self:
            line.department_id = line.employee_id.department_id or line.user_id.employee_id.department_id  # single or multi company

    @api.depends('company_id')
    def _compute_company_id(self):
        # _logger.debug('api depends company_id')
        for line in self:
            line.company_id = line.employee_id.company_id


    #############################
    # read search create unlink
    #############################

    @api.model_create_multi
    def create(self, vals_list):
        res = super(RockerTimesheet,self).create(vals_list)
        for update in res:
            update.task_strategy_id.sudo().task_last_situation_id = update
            update.task_strategy_id.parent_id.sudo().task_last_situation_solution_id = update
            update.task_strategy_id.sudo().task_next_action = update.next_action
            update.task_strategy_id.parent_id.sudo().task_next_action_solution = update.next_action
            update.task_strategy_id.project_id.sudo().task_next_action = update.next_action

            #if not update.code:
            #    sequence_date = datetime.now().strftime("%Y-%m-%d")
            #    try:
            #        #sequence_code = 'ccpp.'+'ta.'+update.strategy_id.project_id.department_id.code
            #        sequence_code = 'ccpp.'+'ta.'
            #    except:
            #        raise UserError("Please Check Sequence")
            #    code = self.env['ir.sequence'].next_by_code(sequence_code,sequence_date=sequence_date)
            #    update.code = code or 'New'
            #update.strategy_id.state = 'process'
            #if update.task_id:
            #    update.task_id.button_done()
            #update.update_solution_process()
        return res
    
    def unlink(self):
        strategy_id = self.task_strategy_id
        solution_id = self.task_id
        ccpp = self.project_id
        res = super().unlink()
        
        last_situation_id = self.search([('task_strategy_id', "=", strategy_id.id)], order="date desc", limit=1)
        strategy_id.task_last_situation_id = last_situation_id
        strategy_id.task_next_action = last_situation_id.next_action
        strategy_id.task_last_current_action = last_situation_id.current_action
        
        last_situation_solution_id = self.search([('task_id', "=", solution_id.id)], order="date desc", limit=1)
        solution_id.task_last_situation_solution_id = last_situation_solution_id
        solution_id.task_next_action_solution = last_situation_solution_id.next_action
        solution_id.task_last_current_action_solution = last_situation_solution_id.current_action
        
        last_situation_ccpp_id = self.search([('project_id', "=", solution_id.id)], order="date desc", limit=1)
        ccpp.last_update_id = last_situation_ccpp_id
        ccpp.task_next_action = last_situation_ccpp_id.next_action
        ccpp.task_current_action = last_situation_ccpp_id.current_action
        return res

    @api.model
    def create(self, vals):
        # creation from hr_timesheet or time_off: set stop & duration
        if not vals['is_go_ccpp_customer'] and not vals['is_go_potential']:
            raise UserError("Please select CCPP Customer or Potential")
        if 'project_id' in vals:
            ccpp_id = self.env['project.project'].browse(vals['project_id'])
            if ccpp_id:
                vals['job_ids'] = ccpp_id.job_ids.ids
                vals['employee_ids'] = ccpp_id.employee_ids.ids
        if 'date' in vals and not 'start' in vals:
            _logger.debug('Creation comes somewhere else than Rocker')
            global default_start_time
            global default_end_time
            global default_duration
            global default_unit_amount
            global default_rolling_amount
            global default_time_roundup
            self._get_defaults()
            # _logger.debug(vals['date'])
            if 'holiday_id' in vals and vals.get('holiday_id'):
                _logger.debug('Creation comes from time_off')
                # _logger.debug('Holiday id: ' + str(vals['holiday_id']))
                time_off = self.env['hr.leave'].search([('id', '=', vals['holiday_id'])])
                # _logger.debug('Hour from: ' + str(time_off.request_hour_from))
                if time_off.request_hour_from != False:
                    # _logger.debug(time_off.date_from)
                    vals['start'] = (time_off.date_from).strftime('%Y-%m-%d %H:%M')
                    vals['stop'] = (time_off.date_to).strftime('%Y-%m-%d %H:%M')
                    vals['duration'] = vals['unit_amount']
                    vals['allday'] = False
                else:
                    # _logger.debug(vals['date'])
                    vals['start'] = (fields.Datetime.from_string(vals['date']) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
                    vals['stop'] = (fields.Datetime.from_string(vals['start']) + timedelta(hours=float(vals['unit_amount']))).strftime('%Y-%m-%d %H:%M')
                    vals['duration'] = vals['unit_amount']
                    if float(vals['unit_amount']) >= default_unit_amount:
                        # I don't like this...better to show all in weekly calendar as timeslots
                        # btw....remember to check odoo global defaults....working day is it 8 or 7.5 hours
                        # vals['allday'] = True
                        vals['allday'] = False
                    else:  
                        vals['allday'] = False

            else:   # can not tell if it comes from sales tiimesheet or just hr_timesheet but who cares
                _logger.debug('Creation comes from hr_timesheet')
                vals['start'] = (fields.Datetime.from_string(vals['date']) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
                vals['stop'] = (fields.Datetime.from_string(vals['start']) + timedelta(hours=float(vals['unit_amount']))).strftime('%Y-%m-%d %H:%M')
                vals['duration'] = vals['unit_amount']
                vals['allday'] = False
            _logger.debug('Values:')
            _logger.debug(vals)

            record = super(RockerTimesheet, self).create(vals)
            return record
        # Rocker specific data
        _logger.debug('Rocker create used')
        _logger.debug('Values:')
        _logger.debug(vals)
        _brolling = self._get_rolling()

        # date exist on view
        # date field is invisible on Rocker timesheet tree view, it is not set
        if 'date' in vals and not vals.get('date'):
            vals['date'] = fields.Datetime.from_string(vals['start']).date()
        _selected_id = -1
        if vals.get('task_id') == False:
            # _logger.debug('Task selected from searchpanel')
            _selected_id = self._get_search_id()
            if _selected_id > 0:
                # _logger.debug('Selected id set, search task...')
                search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
                if not search_task.id:
                    # _logger.debug('Task not found from project.task...')
                    return False
                vals['task_id'] = search_task.id
                vals['project_id'] = search_task.project_id.id
            #else:
                #raise UserError(_('Select Project & Task from drop-down fields'))
        if vals['name'] == False:
            _name = 'new'
            if vals.get('task_id'):
                _name = self.env['project.task'].browse(vals['task_id']).name
            if _name:
                vals['name'] = _name

        # project implies analytic account
        # set none because some analytic line not have ccpp(project)
        if not vals.get('account_id'):
            task = self.env['project.task'].browse(vals.get('task_id'))
            project = self.env['project.project'].search([('id', '=', task.project_id.id)], limit=1)
            #vals['account_id'] = project.analytic_account_id.id
            #if not project.analytic_account_id.id:
            #    vals['account_id'] = 1
        record = super(RockerTimesheet, self).create(vals)
        global daystocreate
        #if daystocreate > 0:
        if False:
            i = 0
            while i < daystocreate:
                _logger.debug('Create more ' + str(i))
                vals['date'] = fields.Datetime.from_string(vals['date']) + timedelta(days=1)
                vals['start'] = fields.Datetime.from_string(vals['start']) + timedelta(days=1)
                vals['stop'] = fields.Datetime.from_string(vals['stop']) + timedelta(days=1)
                record = super(RockerTimesheet, self).create(vals)
                i += 1
        self._set_rolling(False)  # default is Create button with default starty & Stop, Rolling is set is Rolling button clicked
        return record

    def read(self, values):
        if 'start' in values: # rocker
            _logger.debug('Rocker read used')
            self._set_rolling(False)  # default is Create button with default start & Stop, Rolling is set when Rolling button clicked
            _logger.debug('Values...' + str(values))
        else:
            _logger.debug('Rocker read NOT used')
            self._set_search_id(0)

        try:
            records = super(RockerTimesheet, self).read(values)
            return records
        except Exception as e:
            raise exceptions.ValidationError(str(e))
            return False

    def write(self, vals):
        if self.state in ['done','cancel'] and not 'current_situation' in vals and not 'next_action' in vals and not 'state' in vals and not 'job_ids' in vals and not 'employee_ids' in vals:
            raise UserError("Cannot edit task in state done or cancel.")
        if (('name' in vals and vals['name'] != self.name) or \
        ('priority_id' in vals and vals['priority_id'] != self.priority_id.id) or \
        ('customer_id' in vals and vals['customer_id'] != self.customer_id.id) or \
        ('start' in vals and vals['start'] != str(self.start)) or \
        ('stop' in vals and vals['stop'] != str(self.stop)) or \
        ('project_id' in vals and vals['project_id'] != self.project_id.id) or \
        ('task_id' in vals and vals['task_id'] != self.task_id.id) or \
        ('task_strategy_id' in vals and vals['task_strategy_id'] != self.task_strategy_id.id)) and self.id:
            
            log_text = ''
            log_vals = {'analytic_line_id': self.id,
                        'sequence': int(len(self.log_lines)) + 1,
                        'date': datetime.now(),
                        'user_id': self.env.user.id}
        
            if 'name' in vals and vals['name'] != self.name:
                name = vals['name']
                log_text += 'From Task : %s \n'%(self.name)
                log_text += 'To Task      : %s \n'%(name)
                log_vals.update({'name_from': self.name,
                                 'name_to': vals['name']})
            
            if 'priority_id' in vals and vals['priority_id'] != self.priority_id.id:
                priority = vals['priority_id']
                priority_id = self.env['ccpp.priority'].browse(priority)
                log_text += 'From Priority : %s \n'%(self.priority_id.name)
                log_text += 'To Priority      : %s \n'%(priority_id.name)
                log_vals.update({'priority_id_from': self.priority_id.id,
                                 'priority_id_to': priority})
                
            if 'customer_id' in vals and vals['customer_id'] != self.customer_id.id:
                customer = vals['customer_id']
                customer_id = self.env['res.partner'].browse(customer)
                log_text += 'From Customer : %s \n'%(self.customer_id.name)
                log_text += 'To Customer      : %s \n'%(customer_id.name)
                log_vals.update({'customer_id_from': self.customer_id.id,
                                 'customer_id_to': customer})
                
            if 'start' in vals and vals['start'] != str(self.start):
                start = vals['start']
                try:
                    start_show = datetime.strptime(start,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
                except:
                    start = start + ' 00:00:00'
                    start_show = datetime.strptime(start,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
                start_show = start_show.strftime("%d-%m-%Y %H:%M:%S")
                log_text += 'From From : %s \n'%((self.start + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M:%S"))
                log_text += 'To From      : %s \n'%(start_show)
                log_vals.update({'start_from': self.start,
                                 'start_to': start})
                
            if 'stop' in vals and vals['stop'] != str(self.stop):
                stop = vals['stop']
                try:
                    stop_show = datetime.strptime(stop,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
                except:
                    stop = stop + ' 00:00:00'
                    stop_show = datetime.strptime(stop,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
                stop_show = stop_show.strftime("%d-%m-%Y %H:%M:%S")
                log_text += 'From To : %s \n'%((self.stop + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M:%S"))
                log_text += 'To To      : %s \n'%(stop_show)
                log_vals.update({'stop_from': self.stop,
                                 'stop_to': stop})
                
            if 'project_id' in vals and vals['project_id'] != self.project_id.id:
                project = vals['project_id']
                project_id = self.env['project.project'].browse(project)
                log_text += 'From CCPP : %s \n'%(self.project_id.name)
                log_text += 'To CCPP      : %s \n'%(project_id.name)
                log_vals.update({'project_id_from': self.project_id.id,
                                 'project_id_to': project})
                
            if 'task_id' in vals and vals['task_id'] != self.task_id.id:
                task = vals['task_id']
                task_id = self.env['project.task'].browse(task)
                log_text += 'From Solution : %s \n'%(self.task_id.name)
                log_text += 'To Solution      : %s \n'%(task_id.name)
                log_vals.update({'task_id_from': self.task_id.id,
                                 'task_id_to': task})
                
            if 'task_strategy_id' in vals and vals['task_strategy_id'] != self.task_strategy_id.id:
                task_strategy = vals['task_strategy_id']
                task_strategy_id = self.env['project.task'].browse(task_strategy)
                log_text += 'From Strategy : %s \n'%(self.task_strategy_id.name)
                log_text += 'To Strategy      : %s \n'%(task_strategy_id.name)
                log_vals.update({'task_strategy_id_from': self.task_strategy_id.id,
                                 'task_strategy_id_to': task_strategy})
                            
            log_vals.update({'log_text': log_text})
            self.env['account.analytic.line.log'].create(log_vals)
                
        _logger.debug('Write')
        # _logger.debug(self.holiday_id)
        # calendar changes duration if moved/sized but not unit_amount/work
        if 'duration' in vals and not vals.get('unit_amount'):
            _logger.debug('changing unit_amount')
            vals['unit_amount'] = vals['duration']

        if 'date' in vals and not 'start' in vals:
            result = super(RockerTimesheet, self).write(vals)
            return result
        else:
            _logger.debug('Rocker write used')

        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id and 'start' in vals:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        if vals.get('duration'):
            if vals['duration'] > 24:
                raise UserError(_('One timesheet row per day...duration can not exceed 24'))
            
        result = super(RockerTimesheet, self).write(vals)
        return result

    # ----------------------------------------------------------
    # SearchPanel
    # ----------------------------------------------------------

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        _logger.debug('Search...')
        args = args + self._domain_project_id_search()
        clause = []
        # selected_id = 0
        i = 0
        for clause in args:
            if clause[0] == 'task_search':
                # selected_id = int(clause[2])
                if int(clause[2]) > 0:  # id > 0 when task, project row has < 1
                    self._set_search_id(int(clause[2]))
                else:
                    self._set_search_id(0)
                clause[0] = 'task_search'
                clause[1] = '<>'
                clause[2] = ' '
            if clause[0] == 'customer_potential':
                # selected_id = int(clause[2])
                if int(clause[2]) > 0:  # id > 0 when task, project row has < 1
                    self._set_search_id(int(clause[2]))
                else:
                    self._set_search_id(0)
                clause[0] = 'customer_potential'
                clause[1] = '<>'
                clause[2] = ' '
            i += 1
        records = super(RockerTimesheet, self).search(args, limit=limit)
        return records

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name not in ['task_search','customer_potential']:
            # _logger.debug('Rocker search panel NOT used')
            return super(RockerTimesheet, self).search_panel_select_range(field_name, **kwargs)
        else:
            _logger.debug('Rocker search panel used')
        # rocker
        global prev_company
        _company_changed = False
        if prev_company != self.env.company.id:
            # we need to refresh searchpanel,someone changed company :-)
            prev_company = self.env.company.id
            _company_changed = True
            self._domain_set_search_filter('all')
        if field_name in ['task_search','customer_potential']:
            if self._domain_get_search_filter() == "":
                self._domain_set_search_filter('all')
            search_domain = self._domain_get_search_domain(self._domain_get_search_filter())
            # this works in Odoo 14
            return super(RockerTimesheet, self).search_panel_select_range(
                field_name, comodel_domain=search_domain, **kwargs
            )
            # odoo 13, does not work in odoo 14 (no hierarchy)
            # field = self._fields[field_name]
            # Comodel = self.env[field.comodel_name]
            # fields = ['display_name']
            # parent_name = Comodel._parent_name if Comodel._parent_name in Comodel._fields else False
            # if parent_name:
            #     fields.append(parent_name)
            # return {
            #     'parent_field': parent_name,
            #     'values': Comodel.with_context(hierarchical_naming=False).search_read(search_domain, fields),
            # }

        return super(RockerTimesheet, self).search_panel_select_range(field_name, **kwargs)

    def create_rolling(self):
        # _logger.debug('Create rolling item...')
        self._set_rolling(True)
        return

    def searchpanel_all(self, filt):        # called from javascript
        # _logger.debug('Searchpanel_all...')
        if filt == 'all':
            self._domain_set_search_filter('all')
        elif filt == 'member':
            self._domain_set_search_filter('member')
        elif filt == 'billable':
            self._domain_set_search_filter('billable')
        elif filt == 'nonbillable':
            self._domain_set_search_filter('nonbillable')
        elif filt == 'internal':
            self._domain_set_search_filter('internal')
        elif filt == 'mine':
            self._domain_set_search_filter('mine')
        else:
            self._domain_set_search_filter('all')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        # return


    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        # Checking the calendar directly allows to not grey out the leaves taken
        # by the employee
        calendar = self.env.user.employee_id.resource_calendar_id
        if not calendar:
            return {}
        tz = pytz.timezone('UTC')
        usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
        dfrom = pytz.utc.localize(datetime.combine(fields.Date.from_string(date_from), time.min)).astimezone(tz)
        dto = pytz.utc.localize(datetime.combine(fields.Date.from_string(date_to), time.max)).astimezone(tz)

        works = {d[0].date() for d in calendar._work_intervals_batch(dfrom, dto)[False]}
        return {fields.Date.to_string(day.date()): (day.date() not in works) for day in rrule(DAILY, dfrom, until=dto)}

    # ----------------------------------------------------------
    # On Change
    # ----------------------------------------------------------

    @api.onchange('duration')
    def _onchange_duration(self):
        _logger.debug('_onchange_duration')
        if self.duration and self.start and self.unit_amount:
            self.duration = self.rocker_round_up(self.duration) # do not change unit_amount, duration can be longer
            self.stop = fields.Datetime.from_string(self.start) + timedelta(hours=self.duration)
            if self._calculate_duration(self.start,self.stop) < self.unit_amount:
                self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=self.unit_amount)).strftime('%Y-%m-%d %H:%M')
                self.duration = self.rocker_round_up(self.unit_amount)
                raise UserError(_('Duration is less than Work Amount!'))
                return False
        if self.duration > 0 and not self.unit_amount:
            global default_unit_amount
            self._get_defaults()
            self.unit_amount = default_unit_amount

    @api.onchange('start')
    def _onchange_start(self):
        _logger.debug('_onchange_start')
        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup

        self._get_defaults()
        if not self.start:
            _broll = None
            _broll = self._get_rolling()
            if _broll == True:  # set start date = max stop
                query = 'SELECT MAX(stop) as max_stop FROM account_analytic_line where user_id = ' + str(self.env.user.id) + \
                        ' and company_id = ' + str(self.env.company.id)
                self.env.cr.execute(query)
                max_stop = None
                max_stop = self.env.cr.fetchone()
                if max_stop[0]:
                    self.start =  max_stop[0].strftime('%Y-%m-%d %H:%M')
            else:
                _now = fields.Date.today().strftime('%Y-%m-%d %H:%M')
                self.start = (fields.Datetime.from_string(_now) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')


        global daystocreate
        daystocreate = 0
        _delta = 0
        if self.stop and self.start:
            _delta = self.stop.date() - self.start.date()
            daystocreate = _delta.days
            _logger.debug('Needs to create ' + str(daystocreate) + ' extra timesheet rows')

        self.date = self.start.date()
        self.allday = False

        if not self.stop: # real stop setting later has to have something
            self.stop = self.start
        #
        fmt = "%Y-%m-%d %H:%M"
        _dt = fields.Datetime.from_string(self.start).time()
        if  (_dt.hour == 0 and _dt.minute == 0 and _dt.second == 0): # or self.stop.date() == self.start.date():
            self.daystocreateshow = daystocreate + 1
            # change to create only one day, create() then generates more days
            _date = fields.Datetime.from_string(self.start)
            self.start = (fields.Datetime.from_string(self.start.date()) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
            # we change this to one day, in create we create the rest
            self.stop = (fields.Datetime.from_string(self.start.date()) + timedelta(hours=default_end_time)).strftime('%Y-%m-%d %H:%M')
            self.duration = self._calculate_duration(self.start,self.stop)
            self.unit_amount = self._default_work()
        else:
            _broll = None
            _broll = self._get_rolling()
            self.date = fields.Datetime.from_string(self.start).date()
            if self.start == self.stop:    # stop was not set, we take defaults
                _amount = None
                if _broll:
                    self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=default_rolling_amount)).strftime('%Y-%m-%d %H:%M')
                    self.duration = self._calculate_duration(self.start, self.stop)
                    self.unit_amount = default_rolling_amount
                else:
                    self.stop = (fields.Datetime.from_string(self.start.date()) + timedelta(hours=default_end_time)).strftime('%Y-%m-%d %H:%M')
                    self.duration = self._calculate_duration(self.start, self.stop)
                    self.unit_amount = default_unit_amount
            else:
                self.duration = self._calculate_duration(self.start, self.stop)
                self.unit_amount = self.duration
            self.daystocreateshow = 0

    @api.onchange('unit_amount')
    def _onchange_unit_amount(self):
        _logger.debug('_onchange_unit_amount')
        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        if self.unit_amount and self.start:
            global default_start_time
            global default_end_time
            global default_duration
            global default_unit_amount
            global default_rolling_amount
            global default_time_roundup
            self._get_defaults()

            if self.unit_amount != default_unit_amount:     # do not change if defaults used (duration can be other than unit_amount
                self.unit_amount = self.rocker_round_up(self.unit_amount)
                self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=self.unit_amount)).strftime('%Y-%m-%d %H:%M')
                self.duration = self.rocker_round_up(self.unit_amount)

    @api.onchange('stop')
    def _onchange_stop(self):
        _logger.debug('_onchange_stop')
        if self.stop and self.start:
            if fields.Datetime.from_string(self.stop) < fields.Datetime.from_string(self.start):
                raise UserError(_('Stop before start!'))
            self.duration = self._calculate_duration(self.start,self.stop)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        # _logger.debug('_onchange_project_id')
        self.task_id = False

    def rocker_round_up(self, dt):
        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup
        self._get_defaults()
        if default_time_roundup > 0:
            _minutes = dt * 60
            _hours, _minutes = divmod(_minutes, 60)
            _approx = round(_minutes / default_time_roundup) * default_time_roundup
            _t = _hours + _approx / 60
            dt = _t
        return dt

    def to_UTC(self, dt):
        user = self.env.user
        if user.tz:
            tz = pytz.timezone(user.tz) or pytz.utc
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())
        else:
            tz = pytz.timezone('UTC')
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())

        return dt - offset.total_seconds() / 3600
    
    def button_done_wizard(self,context):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_wizard_done_task_action')
        action['context'] = {'default_task': self.id,
                            'default_ccpp': self.project_id.id,
                            'default_solution': self.task_id.id,
                            'default_strategy': self.task_strategy_id.id,
                            'open_wizard': True,
                            'context': context}
        return action
    
    def button_done(self):
        for obj in self:
            if not obj.checkin_date:
                obj.checkin_date = datetime.now()
            obj.task_strategy_id.sudo().task_last_situation_id = obj
            #obj.task_strategy_id.sudo().task_last_current_action = obj.current_action
            obj.task_strategy_id.parent_id.sudo().task_last_situation_solution_id = obj
            #obj.task_strategy_id.parent_id.sudo().task_last_current_action_solution = obj.current_action
            #obj.task_strategy_id.sudo().task_next_action = obj.next_action
            #obj.task_strategy_id.parent_id.sudo().task_next_action_solution = obj.next_action
            #obj.task_strategy_id.project_id.sudo().task_next_action = obj.next_action
            obj.task_strategy_id.project_id.sudo().task_last_update_id = obj
            obj.state = 'done'

    def button_to_open(self):
        for obj in self:
            obj.state = 'open'
            
    def button_cancel(self):
        for obj in self:
            obj.state = 'cancel'
            
    def update_situation(self):
        #action = self.env['ir.actions.act_window']._for_xml_id('ccpp.task_timesheet_update_all_action_form')
        #action['context'] = {'task_id': self.id, 'update_task': True, 'active_id': self.project_id.id}
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.action_ccpp_account_analytic_line_form')
        action['views'] = [(self.env.ref('ccpp.ccpp_account_analytic_line_form').id, 'form')]
        action['res_id'] = self.id
        action['context'] = {'default_checkin_date': datetime.now()}
        return action
    
    def open_current_situation(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.task_timesheet_update_all_action_tree')
        return action
    
    @api.model
    def get_employee_calendar(self,context={}):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id.id
    
    @api.model
    def retrieve_dashboard(self,context={}):
        
        result = {
            'today': 0,
            'this_week': 0,
            'this_month': 0,
            'all': 0,
        }
        
        today = date.today()

        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        
        today_start = str(today) + ' 00:00:00'
        today_stop = str(today) + ' 23:59:59'
        #today_start = datetime.strftime(pytz.utc.localize(datetime.strptime(today_start,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        #today_stop = datetime.strftime(pytz.utc.localize(datetime.strptime(today_stop,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        today_start = datetime.strptime(today_start, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
        today_stop = datetime.strptime(today_stop, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
        
        week_start = (today + relativedelta(weeks=-1,days=1,weekday=0)).strftime('%Y-%m-%d 00:00:00')
        week_stop = (today + relativedelta(weeks=1,weekday=0)).strftime('%Y-%m-%d 23:59:59')
        #week_start = datetime.strftime(pytz.utc.localize(datetime.strptime(week_start,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        #week_stop = datetime.strftime(pytz.utc.localize(datetime.strptime(week_stop,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        week_start = datetime.strptime(week_start, "%Y-%m-%d %H:%M:%S")- relativedelta(hours=7)
        week_stop = datetime.strptime(week_stop, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
        
        month_start = today.strftime('%Y-%m-01 00:00:00')
        month_stop = (today + relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')
        #week_start = datetime.strftime(pytz.utc.localize(datetime.strptime(week_start,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        #week_stop = datetime.strftime(pytz.utc.localize(datetime.strptime(week_stop,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
        month_start = datetime.strptime(month_start, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
        month_stop = datetime.strptime(month_stop, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
        
        task = self.env['account.analytic.line']
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        employee_ids = self.get_child_job(employee_id.job_id).mapped("employee_ids")
        company_ids = self._context.get('allowed_company_ids')
        
        if (self.env.user.has_group('ccpp.group_ccpp_backoffice_user') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_user')) and employee_id.job_lines:
            result['today'] = task.search_count([('stop', '>=', today_start),('stop', '<=', today_stop),('employee_id', '=', employee_ids.id),('company_id', 'in', company_ids)])
            result['this_week'] = task.search_count([('stop', '>=', week_start),('stop', '<=', week_stop),('employee_id', '=', employee_id.id),('company_id', 'in', company_ids)])
            result['this_month'] = task.search_count([('stop', '>=', month_start),('stop', '<', month_stop),('employee_id', '=', employee_id.id),('company_id', 'in', company_ids)])
            result['all'] = task.search_count([('employee_id', '=', employee_id.id),('company_id', 'in', company_ids)])
        elif self.env.user.has_group('ccpp.group_ccpp_backoffice_manager') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager'):
            result['today'] = task.search_count([('stop', '>=', today_start),('stop', '<=', today_stop),('employee_ids', 'in', employee_ids.ids),('company_id', 'in', company_ids)])
            result['this_week'] = task.search_count([('stop', '>=', week_start),('stop', '<=', week_stop),('employee_ids', 'in', employee_ids.ids),('company_id', 'in', company_ids)])
            result['this_month'] = task.search_count([('stop', '>=', month_start),('stop', '<', month_stop),('employee_ids', 'in', employee_ids.ids),('company_id', 'in', company_ids)])
            result['all'] = task.search_count([('employee_ids', 'in', employee_ids.ids),('company_id', 'in', company_ids)])
        elif self.env.user.has_group('ccpp.group_ccpp_backoffice_manager_all_department') or self.env.user.has_group('ccpp.group_ccpp_frontoffice_manager_all_department'):
            result['today'] = task.search_count([('stop', '>=', today_start),('stop', '<=', today_stop),('department_id', '=', employee_id.department_id.id),('company_id', 'in', company_ids)])
            result['this_week'] = task.search_count([('stop', '>=', week_start),('stop', '<=', week_stop),('department_id', '=', employee_id.department_id.id),('company_id', 'in', company_ids)])
            result['this_month'] = task.search_count([('stop', '>=', month_start),('stop', '<', month_stop),('department_id', '=', employee_id.department_id.id),('company_id', 'in', company_ids)])
            result['all'] = task.search_count([('department_id', '=', employee_id.department_id.id),('company_id', 'in', company_ids)])
        elif self.env.user.has_group('ccpp.group_ccpp_ceo'):
            result['today'] = task.search_count([('stop', '>=', today_start),('stop', '<=', today_stop),('company_id', 'in', company_ids)])
            result['this_week'] = task.search_count([('stop', '>=', week_start),('stop', '<=', week_stop),('company_id', 'in', company_ids)])
            result['this_month'] = task.search_count([('stop', '>=', month_start),('stop', '<', month_stop),('company_id', 'in', company_ids)])
            result['all'] = task.search_count([('company_id', 'in', company_ids)])
            
        return result
    
    def get_child_job(self,job_lines,job_ids=False):
        if not job_ids:
            job_ids = self.env['hr.job']
        for job_id in job_lines:
            job_ids |= job_id
            job_ids |= self.get_child_job(job_id.child_lines, job_ids)   
        return job_ids
    
    @api.depends('state')
    def _compute_state_color(self):
        for obj in self:         
            obj.state_color = STATE_COLOR[obj.state]
            
    @api.model
    def check_job_current(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return [employee_id.job_id.id]
            
    @api.model
    def get_employee(self,context):
        
        analytic_line = context
        analytic_line_id = self.env['account.analytic.line'].browse(analytic_line)
        
        date_now = datetime.now().strftime("%d %b %Y").upper()
        time_now = (datetime.now() + timedelta(hours=7)).strftime("%H:%M:%S")
        date_time_now = date_now + ', Time ' + time_now
        
        return {'employee': {'id': analytic_line_id.employee_id.id,
                             'name': analytic_line_id.employee_id.name
                },
                'analytic_line': {'analytic_line_id': analytic_line_id.id,
                                 'task': analytic_line_id.name,
                                 'customer': analytic_line_id.customer_id.name,
                                 'ccpp': analytic_line_id.project_id.name,
                                 'solution': analytic_line_id.task_id.name,
                                 'strategy': analytic_line_id.task_strategy_id.name,
                                 'ccpp_host': analytic_line_id.project_id.partner_contact_id.name,
                },
                'date': {'date_now': date_now,
                         'time_now': time_now,
                         'date_time_now': date_time_now,
                         }
                }
    
    @api.depends('latitude','longitude')
    def _compute_location(self):
        for obj in self:
            location_name = ""
            if obj.latitude and obj.longitude:
                location = self.get_location_name(obj.latitude,obj.longitude)
                location_name = location.get('location_name',"")
            obj.location = location_name
    
    @api.depends('latitude','longitude')
    def _compute_distance(self):
        for obj in self:
            diff = 0
            key_max_14_06_23 = "AIzaSyDoQOI2TsaFcuPFuCi0ZBlucEl3gpN7Cc4"
            # gmaps = googlemaps.Client(key="AIzaSyD3nsr3IPMf1VheJjOyujfcDArTtQli0YM")
            gmaps = googlemaps.Client(key=key_max_14_06_23)
            geocode_result = gmaps.geocode(obj.customer_id.name)
            if obj.latitude and obj.longitude and geocode_result:
                
                geometry = geocode_result[0].get('geometry')
                customer_location = geometry.get('location')
                customer_latitude = customer_location.get('lat') 
                customer_longitude = customer_location.get('lng')
                
                # r = 3958.8 Radius of the Earth in miles
                r = 6371 # Radius of the Earth in km
                rlat1 = obj.latitude * math.pi / 180 # Convert degrees to radians
                rlat2 = customer_latitude * math.pi / 180 # Convert degrees to radians
                difflat = rlat2-rlat1 #  Radian difference (latitudes)
                difflon = (customer_longitude - obj.longitude) * (math.pi / 180) #Radian difference (longitudes)

                diff = 2 * r * math.asin(math.sqrt(math.sin(difflat/2)*math.sin(difflat/2)+math.cos(rlat1)*math.cos(rlat2)*math.sin(difflon/2)*math.sin(difflon/2)))
                #diff = math.acos(math.sin(obj.latitude)*math.sin(customer_latitude)+math.cos(obj.latitude)*math.cos(customer_latitude)*math.cos(customer_longitude-obj.longitude)) * r
                
                obj.is_diff_distance = True
            else:
                obj.is_diff_distance = False

            obj.diff_distance = diff
    
    @api.model
    def get_location_name(self,latitude,longitude):
        location_name = ""
        
        key_max_old = "AIzaSyBGMY2ya5VHQ8_2GqA31xfKhpfFGOUQGwg" # key max
        key_max = "AIzaSyAMnFrYwsSAIirLacIcdCG9zELKSckgOis"
        key_max_14_06_23 = "AIzaSyDoQOI2TsaFcuPFuCi0ZBlucEl3gpN7Cc4"
        # gmaps = googlemaps.Client(key="AIzaSyD3nsr3IPMf1VheJjOyujfcDArTtQli0YM") # key P'Bank
        gmaps = googlemaps.Client(key=key_max_14_06_23) # key P'Bank
        # gmaps = googlemaps.Client(key=key) # key P'Bank
        # Geocoding an address
        # geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

        # Look up an address with reverse geocoding
        reverse_geocode_result = gmaps.reverse_geocode((latitude, longitude))
        if reverse_geocode_result:
            try:
                location_name = reverse_geocode_result[0]['formatted_address']
            except:
                location_name = ""
                
        
        return {'location_name': location_name}
        
        # key = "AIzaSyBGMY2ya5VHQ8_2GqA31xfKhpfFGOUQGwg"
        # url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%skey=%s"%(latitude,longitude,key)
        # params = {"key": "AIzaSyBGMY2ya5VHQ8_2GqA31xfKhpfFGOUQGwg"}
        # response = requests.post(url)
        # if response.ok:
        #     location = response.json()["location"]
        #     latitude = location["lat"]
        #     longitude = location["lng"]
        #     accuracy = response.json()["accuracy"]
        
    @api.model
    def update_check_in(self,context):
        
        obj=self.browse(context[0])
        if not context[1] or not context[2]:
            raise UserError("Not found location !!. Please check network or refresh browser")
        
        # if 'need_done_strategy' in context[5]:
            # obj.task_strategy_id.button_done()
        print("max1"*100)
        print(context[5])
        need_done_strategy = False
        if 'need_done_strategy' in context[5]:
            print("max"*100)
            need_done_strategy = True
            # context[5] = ''
            # return obj.button_done_wizard(context)
        
        checkin_date = datetime.now()
        obj.write({'latitude': context[1],
                   'longitude': context[2],
                   'current_action': context[3],
                   'next_action': context[4],
                   'checkin_date': checkin_date,
                   
        })

        current_year = str(datetime.now().year)
        purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',obj.customer_id.id),
                                                                        ('year_selection','=',current_year),
                                                                        ('sale_person_id','=',obj.employee_id.id)
                                                                        ]) 
        order_line_list = []
        borrow_line_list = []
        for history_line_id in purchase_history_id.winmed_lines:
            val = {'phlid' : history_line_id.id,
                   'product': history_line_id.product_id.name,
                   'uom': history_line_id.uom_id.name,
                   
            }
                   
            order_line_list.append(val)
            borrow_line_list.append(val)
            
        is_purchase_history = False
        if purchase_history_id:
            is_purchase_history = True
        else:
            obj.state = 'done'
        
        print("max2"*100)
        
        return {'purchase_history': is_purchase_history,
                'order_lines': order_line_list,
                'borrow_lines': borrow_line_list,
                'need_done_strategy': need_done_strategy,
                }
        
    @api.model
    def done(self,analytic_line):
        obj = self.browse(analytic_line)
        current_year = str(datetime.now().year)
        purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',obj.customer_id.id),
                                                                        ('year_selection','=',current_year),
                                                                        ('sale_person_id','=',obj.employee_id.id)
                                                                ])

        for purchase_history_line_id in purchase_history_id.winmed_lines:
            detail_line = self.env['ccpp.purchase.history.detail.line'].search([('task_id','=',analytic_line),('history_line_id','=',purchase_history_line_id.id)])
            date_today = date.today()
            if not detail_line:
                vals = {'history_line_id': purchase_history_line_id.id,
                    'date': date_today,
                    'task_id': obj.id,
                    'borrow_qty': 0,
                    'order_borrow_qty': 0,
                    'order_qty': 0,
                    'remain_qty': 0,
                    }
                detail_line.create(vals)
        obj.state = 'done'

    @api.model
    def done_strategy(self,analytic_line):
        obj = self.browse(analytic_line)  
        obj.task_strategy_id.button_done()
        return True
    
    @api.model
    def cancel_task(self,analytic_line):
        obj = self.browse(analytic_line)  
        obj.button_cancel()
        return True
                
    @api.model
    def skip(self,analytic_line):
        obj = self.browse(analytic_line)
        current_year = str(datetime.now().year)
        purchase_history_id = self.env['ccpp.purchase.history'].search([('customer_id','=',obj.customer_id.id),
                                                                        ('year_selection','=',current_year),
                                                                        ('sale_persone_id','=',obj.employee_id.id)
                                                                ])

        for purchase_history_line_id in purchase_history_id.winmed_lines:
            detail_line = self.env['ccpp.purchase.history.detail.line'].search([('task_id','=',analytic_line),('history_line_id','=',purchase_history_line_id.id)])
            date_today = date.today()
            if not detail_line:
                vals = {'history_line_id': purchase_history_line_id.id,
                    'date': date_today,
                    'task_id': obj.id,
                    'borrow_qty': 0,
                    'order_borrow_qty': 0,
                    'order_qty': 0,
                    'remain_qty': 0,
                    }
                detail_line.create(vals)
            else:
                detail_line.write({
                    'borrow_qty': 0,
                    'order_borrow_qty': 0,
                    'order_qty': 0,
                    'remain_qty': 0,
                })
        
        obj.state = 'done'
                
            
            
    
    @api.model
    def input_value(self, purchase_line, value, type, task):
        purchase_line_id = self.env['ccpp.purchase.history.line'].browse(int(purchase_line))
        detail_line = self.env['ccpp.purchase.history.detail.line'].search([('history_line_id','=',int(purchase_line)),('task_id','=',int(task))])
        order = 0
        remain = 0
        borrow = 0
        order_borrow = 0
        
        if 'order[1]' in type:
            order = value
        elif 'remain[2]' in type:
            remain = value
        elif 'borrow[3]' in type:
            borrow = value
        elif 'order_borrow[4]' in type:
            order_borrow = value

        if detail_line and order:
            detail_line.write({'order_qty': order})
        elif detail_line and remain:
            detail_line.write({'remain_qty': remain})
        elif detail_line and order_borrow:
            detail_line.write({'order_borrow_qty': order_borrow})
        elif detail_line and borrow:
            detail_line.write({'borrow_qty': borrow})
            
        date_today = date.today()
        if not detail_line:
            vals = {'history_line_id': purchase_line_id.id,
                    'date': date_today,
                    'task_id': task,
                    'borrow_qty': borrow,
                    'order_borrow_qty': order_borrow,
                    'order_qty': order,
                    'remain_qty': remain,
                    }
            detail_line.create(vals)
            
        
        
        
        
        
    
class AccountAnalyticLineLog(models.Model):
    _name = "account.analytic.line.log"
    _order = "sequence"
    
    analytic_line_id = fields.Many2one("account.analytic.line", index=True, ondelete='cascade', readonly=True, required=True)
    sequence = fields.Integer(string="No.")
    name_from = fields.Char(string="From Task")
    name_to = fields.Char(string="To Task")
    priority_id_from = fields.Many2one("ccpp.priority", string="From Priority")
    priority_id_to = fields.Many2one("ccpp.priority", string="To Priority")
    customer_id_from = fields.Many2one("res.partner", string="From Customer")
    customer_id_to = fields.Many2one("res.partner", string="To Customer")
    start_from = fields.Datetime(string="From From")
    start_to = fields.Datetime(string="To From")
    stop_from = fields.Datetime(string="From To")
    stop_to = fields.Datetime(string="To To")
    project_id_from = fields.Many2one("project.project", string="From CCPP")
    project_id_to = fields.Many2one("project.project", string="To CCPP")
    task_id_from = fields.Many2one("project.task", string="From Solution")
    task_id_to = fields.Many2one("project.task", string="To Solution")
    task_strategy_id_from = fields.Many2one("project.task", string="From Strategy")
    task_strategy_id_to = fields.Many2one("project.task", string="To Strategy")
    user_id = fields.Many2one("res.users", string="User",default=lambda self: self.env.user)
    log_text = fields.Text(string="Text")
    date = fields.Datetime(string="Date")
