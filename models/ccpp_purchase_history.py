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
        res = super(CCPPPurchaseHistory,self).default_get(fields)
        if 'sale_person_id' in fields:
            sale_person_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            if not sale_person_id:
                raise UserError("Not recognize the sales person. Please Configure User to Employee to get the sales person")
            res['sale_person_id'] = sale_person_id.id
        if 'year_selection' in fields:
            current_year = datetime.today().year
            res['year_selection'] = str(current_year)
        if 'month' in fields:
            current_period = datetime.today().month
            res['month'] = str(current_period)
        return res
        
    name = fields.Char(string="Name")
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
    ], required=True, string="Month") 
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
    ], default='to_define', required=True, string="Potential Type", compute='_compute_potential_type') 
    vendor_id = fields.Many2one("res.partner", string="Vendor", required=True)
    key_user_id = fields.Many2one("res.partner.position", string="Key User")
    domain_job_position_ids = fields.Many2many("res.partner.position", string="Domain Job Position", compute="_compute_domain_job_position_ids")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    unit_price = fields.Float(string="Unit Price")
    order_qty = fields.Float(string="Ordered Qty")
    use_qty = fields.Float(string="Used Qty")        
    note = fields.Text("Competitors' Sales Strategy")
    sale_person_id = fields.Many2one("hr.employee", string="Sales Person", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    company_partner_id = fields.Many2one("res.partner", string="Company Partner", related="company_id.partner_id")

    @api.depends("vendor_id")
    def _compute_domain_job_position_ids(self):
        for obj in self:
            job_position_ids = self.env['res.partner.position']
            if obj.vendor_id:
                for child_id in obj.vendor_id.child_ids:
                    job_position_ids |= child_id.job_position_id
            obj.domain_job_position_ids = job_position_ids.ids
    
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
            
    