from email.policy import default
from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date, timezone
import pytz
import json
from pprint import pprint
from random import randint

class ApproveActivityType(models.Model):
    _name = "approve.activity.type"
    _inherit = ['mail.thread']

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Name")
    code = fields.Char("Code")
    color = fields.Integer(string="Color")
    count_doc = fields.Integer(string="Count Document", compute="_compute_count_doc",store=False)
    icon_variant =  fields.Image("Icon Variant Image", max_width=1920, max_height=1920)
    icon = fields.Image("Icon Image", compute='_compute_image', inverse='_set_image')
    icon_binary = fields.Binary("Icon", attachment=True,copy=False)
    info = fields.Text("Info")
    #background_color = fields.Char("Background Color", default="#ffffff")

    def _compute_image(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.icon = record.icon_variant

    def _set_image(self):
        return self._set_template_field('icon', 'icon_variant')
    
    def _set_template_field(self, template_field, variant_field):
        for record in self:
            if (
                # We are trying to remove a field from the variant even though it is already
                # not set on the variant, remove it from the template instead.
                (not record[template_field] and not record[variant_field])
                # We are trying to add a field to the variant, but the template field is
                # not set, write on the template instead.
                #or (record[template_field] and not record.product_tmpl_id[template_field])
                # There is only one variant, always write on the template.
            ):
                record[variant_field] = False
                #record.product_tmpl_id[template_field] = record[template_field]
            else:
                record[variant_field] = record[template_field]
    
    def _compute_count_doc(self):
        for obj in self:
            count_doc = 0
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            activity_ids = self.env['mail.activity'].search([('job_id','=',employee_id.job_id.id),('approve_activity_type_id','=',obj.id)])
            count_doc = len(activity_ids)
            obj.count_doc = count_doc
        
    def action_get_doc(self):
        for obj in self:
            action = True
            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
            activity_ids = self.env['mail.activity'].search([('job_id','=',employee_id.job_id.id),('approve_activity_type_id','=',obj.id)])
            record_ids = activity_ids.mapped('res_id')
            if obj.code == 'ccpp':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_ccpp_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            elif obj.code == 'solution':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_solution_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            elif obj.code == 'strategy':
                action = self.env['ir.actions.act_window']._for_xml_id('ccpp.ccpp_strategy_approve_dashboard_action')
                action['domain'] = [('id', 'in', record_ids)]
            return action
    
    def unlink(self):
        #raise UserError("ระบบไม่สามารถลบ Appove Activity Type ได้")
        res = super().unlink()