from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

STATUS_COLOR = {
    'over': 20,
    'similar': 3,
    'less': 23,
    'to_define': 0,
}

class CCPPPurchaseHistory(models.Model):
    _name = "ccpp.purchase.history"
    _inherit = ['mail.thread']
    _order = "name"
    
    """def _get_default_date_from(self):
        if datetime.today().month in range(1,3):
            date_from = datetime.today().replace(day=1,month=1)
        if datetime.today().month in range(4,6):
            date_from = datetime.today().replace(day=1,month=4)
        if datetime.today().month in range(7,9):
            date_from = datetime.today().replace(day=1,month=7)
        if datetime.today().month in range(10,12):
            date_from = datetime.today().replace(day=1,month=9)
        return date_from """
    
    """def _get_default_date_to(self):
        if datetime.today().month in range(1,3):
            date_to = datetime.today().replace(day=31,month=3)
        if datetime.today().month in range(4,6):
            date_to = datetime.today().replace(day=30,month=6)
        if datetime.today().month in range(7,9):
            date_to = datetime.today().replace(day=30,month=9)
        if datetime.today().month in range(10,12):
            date_to = datetime.today().replace(day=31,month=12)
        return date_to """

    @api.model
    def default_get(self,fields):
        res = super().default_get(fields)
        if 'sale_person_id' in fields:
            sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            if not sale_person_id:
                raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
            res['sale_person_id'] = sale_person_id.id
        if 'year_selection' in fields:
            current_year = datetime.today().year
            res['year_selection'] = str(current_year)
        #if 'month' in fields:
        #    current_period = datetime.today().month
        #    res['month'] = str(current_period)
        return res
    
    def _get_default_job(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        #if not employee_id:
        #    print(self.env.user.name)
        #    raise UserError("Not recognize the Employee. Please Configure User to Employee to get the job")
        return employee_id.job_id
        
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    #year = fields.Char(string="Year")
    month = fields.Selection(selection=[
        ('1', 'JAN'),
        ('2', 'FEB'),
        ('3', 'MAR'),
        ('4', 'APR'),
        ('5', 'MAY'),
        ('6', 'JUN'),
        ('7', 'JUL'),
        ('8', 'AUG'),
        ('9', 'SEP'),
        ('10', 'OCT'),
        ('11', 'NOV'),
        ('12', 'DEC'),
    ], string="Month") 
    year_selection = fields.Selection(selection=[
        ('2003', '2003'),
        ('2004', '2004'),
        ('2005', '2005'),
        ('2006', '2006'),
        ('2007', '2007'),
        ('2008', '2008'),
        ('2009', '2009'),
        ('2010', '2010'),
        ('2011', '2011'),
        ('2012', '2012'),
        ('2013', '2013'),
        ('2014', '2014'),
        ('2015', '2015'),
        ('2016', '2016'),
        ('2017', '2017'),
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022'),
        ('2023', '2023'),
        ('2024', '2024'),
        ('2025', '2025'),
        ('2026', '2026'),
        ('2027', '2027'),
        ('2028', '2028'),
        ('2029', '2029'),
        ('2030', '2030'),
        ('2031', '2031'),
        ('2032', '2032'),
        ('2033', '2033'),
        ('2034', '2034'),
        ('2035', '2035'),
        ('2036', '2036'),
        ('2037', '2037'),
        ('2038', '2038'),
        ('2039', '2039'),
        ('2040', '2040'),
        ('2041', '2041'),
        ('2042', '2042'),
        ('2043', '2043'),
        ('2044', '2044'),
        ('2045', '2045'),
        ('2046', '2046'),
        ('2047', '2047'),
        ('2048', '2048'),
        ('2049', '2049'),
        ('2050', '2050'),
        ('2051', '2051'),
        ('2052', '2052'),
        ('2053', '2053'),
        ('2054', '2054'),
        ('2055', '2055'),
        ('2056', '2056'),
        ('2057', '2057'),
        ('2058', '2058'),
        ('2059', '2059'),
        ('2060', '2060'),
        ('2061', '2061'),
        ('2062', '2062'),
        ('2063', '2063'),
        ('2064', '2064'),
        ('2065', '2065'),
        ('2066', '2066'),
        ('2067', '2067'),
        ('2068', '2068'),
        ('2069', '2069'),
        ('2070', '2070'),
        ('2071', '2071'),
        ('2072', '2072'),
        ('2073', '2073'),
    ], required=True, string="Year")
    customer_id = fields.Many2one("res.partner", string="Customer", required=True)
    potential_type = fields.Selection(selection=[
        ('company', 'Company'),
        ('competitor', 'Competitors'),
        ('to_define', 'Undefine')
    ], default='to_define', string="Potential Type", compute='_compute_potential_type') 
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    key_user_id = fields.Many2one("res.partner", string="Key User")
    domain_job_position_ids = fields.Many2many("res.partner.position", string="Domain Job Position", compute="_compute_domain_job_position_ids")
    domain_key_user_ids = fields.Many2many("res.partner", string="Domain Key User", compute="_compute_domain_key_user_ids")
    product_id = fields.Many2one("product.product", string="Product")
    unit_price = fields.Float(string="Unit Price")
    order_qty = fields.Float(string="Ordered Qty")
    use_qty = fields.Float(string="Used Qty")
    total_price = fields.Float(string="Total Price", compute="_compute_total")
    total_qty = fields.Float(string="Total Ordered Qty", compute="_compute_total")
    total_use_qty = fields.Float(string="Total Used Qty", compute="_compute_total")
    note = fields.Text("Competitors' Sales Strategy")
    sale_person_id = fields.Many2one("hr.employee", string="Sales Person", required=True)
    job_id = fields.Many2one("hr.job", string="Job Position", default=_get_default_job, required=True, track_visibility="onchange")
    domain_job_ids = fields.Many2many("hr.job", string="Domain Job", compute="_compute_domain_job_ids")
    department_id = fields.Many2one("hr.department", string="Deparment", related="sale_person_id.department_id")
    division_id = fields.Many2one("hr.department", string="Division", related="sale_person_id.division_id")
    user_id = fields.Many2one(related="sale_person_id.user_id", string="Sales User", store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    company_partner_id = fields.Many2one("res.partner", string="Company Partner", related="company_id.partner_id")
    winmed_lines = fields.One2many("ccpp.purchase.history.line", "history_id", string="Winmed Purchase History Lines", domain=[('potential_type','=','company')])
    competitor_lines = fields.One2many("ccpp.purchase.history.line", "history_id", string="Competitor Purchase History Lines", domain=[('potential_type','=','competitor')] )
    
    @api.depends("sale_person_id")
    def _compute_domain_job_ids(self):
        for obj in self:
            job_ids = self.env['hr.job']
            if obj.sale_person_id:
                for job_id in obj.sale_person_id.job_lines:
                    job_ids |= job_id
            obj.domain_job_ids = job_ids.ids
    
    @api.depends("winmed_lines", "winmed_lines.unit_price", "winmed_lines.order_qty", "winmed_lines.use_qty")
    def _compute_total(self):
        for obj in self:
            total_price = 0
            total_qty = 0
            total_use_qty = 0
            for winmed_line in obj.winmed_lines:
                total_price += winmed_line.order_qty * winmed_line.unit_price
                total_qty += winmed_line.order_qty
                total_use_qty += winmed_line.use_qty
           # for competitor_line in obj.competitor_lines:
            obj.total_price = total_price
            obj.total_qty = total_qty
            obj.total_use_qty = total_use_qty

    @api.depends("year_selection", "customer_id")
    def _compute_name(self):
        for obj in self:
            name = "New"
            if obj.year_selection and obj.customer_id:
                name = obj.year_selection + ' - ' + obj.customer_id.name
            obj.name = name

    @api.depends("vendor_id")
    def _compute_domain_job_position_ids(self):
        for obj in self:
            job_position_ids = self.env['res.partner.position']
            if obj.vendor_id:
                for child_id in obj.vendor_id.child_ids:
                    job_position_ids |= child_id.job_position_id
            obj.domain_job_position_ids = job_position_ids.ids
            
    @api.depends("customer_id")
    def _compute_domain_key_user_ids(self):
        for obj in self:
            key_user_ids = self.env['res.partner']
            if obj.customer_id:
                for child_id in obj.customer_id.child_ids:
                    key_user_ids |= child_id
            obj.domain_key_user_ids = key_user_ids.ids
    
    @api.depends('vendor_id','company_id')
    def _compute_potential_type(self):
        for obj in self:
            if obj.vendor_id:
                if obj.vendor_id == obj.company_id.partner_id:
                    obj.potential_type = 'company'
                else:
                    obj.potential_type = 'competitor'
            else:
                obj.potential_type = 'to_define'
     
    @api.constrains('year_selection','customer_id')
    def constrains_year_selection_period(self):
        for obj in self:
            if obj.year_selection and obj.customer_id:
                check_duplicate = self.env['ccpp.purchase.history'].search([('id','!=',obj.id),
                                                                            ('customer_id','=',obj.customer_id.id),
                                                                            ('year_selection','=',obj.year_selection),
                                                                            ('sale_person_id','=',obj.sale_person_id.id),
                                                                            ])
                if check_duplicate:
                    raise UserError("Customer %s already have Purchase History in year %s"%(obj.customer_id.name,obj.year_selection))

    def action_purchase_history_user(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        history_ids = self.env['ccpp.purchase.history'].search([
                                                                ('job_id', '=', employee_id.job_id.id),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action

    def action_purchase_history_manager(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        job_ids = self.get_child_job(employee_id.job_lines)
        history_ids = self.env['ccpp.purchase.history'].search([
                                                                ('job_id', 'in', job_ids.ids),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def action_purchase_history_manager_all_department(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        history_ids = self.env['ccpp.purchase.history'].search([
                                                                ('department_id', '=', employee_id.department_id.id),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def action_purchase_history_ceo(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        history_ids = self.env['ccpp.purchase.history'].search([
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def get_child_job(self,job_lines,job_ids=False):
        if not job_ids:
            job_ids = self.env['hr.job']
        for job_id in job_lines:
            job_ids |= job_id
            job_ids |= self.get_child_job(job_id.child_lines, job_ids)   
        return job_ids
            
class CCPPPurchaseHistoryLine(models.Model):
    _name = "ccpp.purchase.history.line"
    
    def _get_default_type(self):
        if self._context.get('potential_type'):
            print("Max"*50)
            if self._context.get('potential_type') == 'company':
                return 'company'
            elif self._context.get('potential_type') == 'competitor':
                return 'competitor'
    
    def _get_default_vendor(self):
        if self._context.get('potential_type'):
            if self._context.get('potential_type') == 'company':
                return self.env.user.company_id.partner_id
    
    history_id = fields.Many2one("ccpp.purchase.history", index=True, ondelete='cascade', readonly=True)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    asset_id = fields.Many2one("asset", string="Asset")
    unit_price = fields.Float(string="Unit Price")
    uom_id = fields.Many2one("uom.uom", string="UoM")
    borrow_qty = fields.Float(string="Borrow Balance Qty", compute="_compute_qty")
    order_qty = fields.Float(string="Ordered Qty",compute="_compute_qty")
    use_qty = fields.Float(string="Used Qty", compute="_compute_qty")
    remain_qty = fields.Float(string="Remain Qty", compute="_compute_qty")
    vendor_id = fields.Many2one("res.partner", string="Vendor", default=_get_default_vendor)
    customer_id = fields.Many2one(related="history_id.customer_id", store=True)
    year_selection = fields.Selection(related="history_id.year_selection", store=True)
    sale_person_id = fields.Many2one(related="history_id.sale_person_id", store=True)
    job_id = fields.Many2one(related="history_id.job_id", store=True)
    key_user_id = fields.Many2one("res.partner", string="Key User")
    domain_key_user_ids = fields.Many2many("res.partner", string="Domain Key User", compute="_compute_domain_key_user_ids")
    potential_type = fields.Selection(selection=[
        ('company', 'Company'),
        ('competitor', 'Competitors'),
    ], default=_get_default_type, string="Potential Type")
    note = fields.Text("Sales Strategy")
    company_id = fields.Many2one(related="history_id.company_id", store=True)
    detail_lines = fields.One2many("ccpp.purchase.history.detail.line", "history_line_id", string="Competitor Purchase History Detail Lines")

    @api.depends("detail_lines","detail_lines.borrow_qty","detail_lines.order_borrow_qty","detail_lines.order_qty","detail_lines.remain_qty")
    def _compute_qty(self):
        for obj in self:
            borrow = obj.detail_lines.mapped('borrow_qty')
            borrow_qty = sum(borrow) or 0
            order_borrow = obj.detail_lines.mapped('order_borrow_qty')
            order_borrow_qty = sum(order_borrow) or 0
            order = obj.detail_lines.mapped('order_qty')
            order_qty = sum(order) or 0
            remain_line = self.env['ccpp.purchase.history.detail.line'].search([('history_line_id','=',obj.id)], order="date desc, id desc", limit=1)

            obj.borrow_qty = borrow_qty - order_borrow_qty
            obj.order_qty = order_qty + order_borrow_qty
            obj.use_qty = order_qty + borrow_qty - ((remain_line.remain_qty or 0) + (remain_line.order_qty or 0) + (remain_line.borrow_qty or 0))
            obj.remain_qty = (remain_line.remain_qty or 0) + (remain_line.order_qty or 0) + (remain_line.borrow_qty or 0)

    @api.model_create_multi
    def create(self, vals_list):
        #for vals in vals_list:
        #    print(self._context)
        #    if self._context.get('is_create_history'):
        #        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action_form')
        #        return action
            
        res = super(CCPPPurchaseHistoryLine, self).create(vals_list)
        
        return res
    
    def unlink(self):
        if self.detail_lines: 
            raise UserError("ไม่สามารถลรายการที่มีการอัพเดทข้อมูลมาแล้วได้")
        res = super().unlink()
    
    @api.depends("customer_id")
    def _compute_domain_key_user_ids(self):
        for obj in self:
            key_user_ids = self.env['res.partner']
            if obj.customer_id:
                for child_id in obj.customer_id.child_ids:
                    key_user_ids |= child_id
            obj.domain_key_user_ids = key_user_ids.ids
            
    def action_open_history_form(self):
        for obj in self:
            action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_action_form')
            action['res_id'] = obj.history_id.id
            return action
        
    @api.onchange("product_id")
    def onchange_product(self):
        for obj in self:
            uom_id = self.env['uom.uom']
            if obj.product_id:
                uom_id = obj.product_id.uom_id
            obj.uom_id = uom_id
    
    def action_open_detail(self):
        for obj in self:
            action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_detail_line_action')
            detail_ids = self.env['ccpp.purchase.history.detail.line'].search([('history_line_id','=',obj.id)])
            action['domain'] = [('id','in',detail_ids.ids)]
            return action
    
    
class CCPPPurchaseHistoryDetailLine(models.Model):
    _name = "ccpp.purchase.history.detail.line"
    
    history_line_id = fields.Many2one("ccpp.purchase.history.line", index=True, ondelete='cascade')#, readonly=True
    product_id = fields.Many2one(related="history_line_id.product_id", store=True)
    asset_id = fields.Many2one(related="history_line_id.asset_id", store=True)
    unit_price = fields.Float(related="history_line_id.unit_price")
    uom_id = fields.Many2one(related="history_line_id.uom_id")
    date = fields.Date(string="Date")
    borrow_qty = fields.Float(string="Borrow Qty")
    order_borrow_qty = fields.Float(string="Ordered (Borrow) Qty")
    order_qty = fields.Float(string="Ordered (Normal) Qty")
    remain_qty = fields.Float(string="Remaining Qty") 
    vendor_id = fields.Many2one(related="history_line_id.vendor_id")
    customer_id = fields.Many2one(related="history_line_id.customer_id", store=True)
    year_selection = fields.Selection(related="history_line_id.year_selection", store=True)
    sale_person_id = fields.Many2one(related="history_line_id.sale_person_id")
    job_id = fields.Many2one(related="history_line_id.job_id", store=True)
    key_user_id = fields.Many2one(related="history_line_id.key_user_id")
    potential_type = fields.Selection(related="history_line_id.potential_type")
    company_id = fields.Many2one(related="history_line_id.company_id")
    task_id = fields.Many2one("account.analytic.line", string="Task")
    
    
    def action_purchase_history_detail_line_user(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_detail_line_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        history_ids = self.env['ccpp.purchase.history.detail.line'].search([
                                                                ('job_id', '=', employee_id.job_id.id),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        print("Max"*100)
        print(history_ids)
        action['domain'] = [('id','in',history_ids.ids)]
        return action

    def action_purchase_history_detail_line_manager(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_detail_line_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        job_ids = self.get_child_job(employee_id.job_lines)
        history_ids = self.env['ccpp.purchase.history.detail.line'].search([
                                                                ('job_id', 'in', job_ids.ids),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def action_purchase_history_detail_line_manager_all_department(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_detail_line_action')
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        history_ids = self.env['ccpp.purchase.history.detail.line'].search([
                                                                ('department_id', '=', employee_id.department_id.id),
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def action_purchase_history_detail_line_ceo(self):
        self = self.sudo()
        company_ids = self._context.get('allowed_company_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_purchase_history_detail_line_action')
        history_ids = self.env['ccpp.purchase.history.detail.line'].search([
                                                                ('company_id', 'in', company_ids),
                                                                ])
        action['domain'] = [('id','in',history_ids.ids)]
        return action
    
    def get_child_job(self,job_lines,job_ids=False):
        if not job_ids:
            job_ids = self.env['hr.job']
        for job_id in job_lines:
            job_ids |= job_id
            job_ids |= self.get_child_job(job_id.child_lines, job_ids)   
        return job_ids


    
    