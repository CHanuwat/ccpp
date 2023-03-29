from odoo import fields, models
from datetime import datetime, timedelta

class Sequence(models.Model):
    _inherit="ir.sequence"

    type_range = fields.Selection([
        ('year','Year'),
        ('month','Month')
        ],string="Type Date Range")

    def _next(self, sequence_date=None):
        """ Returns the next number in the preferred sequence in all the ones given in self."""
        if not self.use_date_range:
            return self._next_do()
        # date mode
        dt = sequence_date or self._context.get('ir_sequence_date', fields.Date.today())
        seq_date = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
        if not seq_date:
            seq_date = self._create_date_range_seq(dt)
        print(" ======== sequence_date : ",sequence_date)
        
        if sequence_date:
            ## case : have time
            if " " in str(sequence_date): 
                list_sd = str(sequence_date).split(" ")
                sequence_date = list_sd[0]
                return seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()
            else:
                return seq_date.with_context(ir_sequence_date=sequence_date)._next()
        else:
            return seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()
        
    def _create_date_range_seq(self, date):
        if self.type_range:
            if self.type_range == "year":
                year = fields.Date.from_string(date).strftime('%Y')
                date_from = '{}-01-01'.format(year)
                date_to = '{}-12-31'.format(year)
            elif self.type_range == "month":
                year = int(fields.Date.from_string(date).strftime('%Y'))
                month = int(fields.Date.from_string(date).strftime('%m'))
                ## first date
                first_date = datetime(year, month, 1)
                date_from = first_date.strftime("%Y-%m-%d")

                ## last date
                if month == 12:
                    last_date = datetime(year, month, 31)
                else:
                    last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
                date_to = last_date.strftime("%Y-%m-%d")
        else:
            year = fields.Date.from_string(date).strftime('%Y')
            date_from = '{}-01-01'.format(year)
            date_to = '{}-12-31'.format(year)

        date_range = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '>=', date), ('date_from', '<=', date_to)], order='date_from desc', limit=1)
        if date_range:
            date_to = date_range.date_from + timedelta(days=-1)
        date_range = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_to', '>=', date_from), ('date_to', '<=', date)], order='date_to desc', limit=1)
        if date_range:
            date_from = date_range.date_to + timedelta(days=1)
        seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'sequence_id': self.id,
        })
        return seq_date_range