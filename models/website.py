import base64
import hashlib
import inspect
import json
import logging
import operator
import re
import requests

from collections import defaultdict
from functools import reduce
from lxml import etree, html
from psycopg2 import sql
from werkzeug import urls
from werkzeug.datastructures import OrderedMultiDict
from werkzeug.exceptions import NotFound
from markupsafe import Markup

from odoo import api, fields, models, tools, http, release, registry
from odoo.addons.http_routing.models.ir_http import RequestUID, slugify, url_for
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website.tools import similarity_score, text_from_html
from odoo.addons.portal.controllers.portal import pager
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request
from odoo.modules.module import get_resource_path, get_manifest
from odoo.osv.expression import AND, OR, FALSE_DOMAIN, get_unaccent_wrapper
from odoo.tools.translate import _
from odoo.tools import escape_psql, OrderedSet, pycompat

class Website(models.Model):
    _inherit = "website"
    
    @api.model
    def get_current_website(self, fallback=True):
        if request and request.session.get('force_website_id'):
            website_id = self.browse(request.session['force_website_id']).exists()
            print('1')
            if not website_id:
                # Don't crash is session website got deleted
                print('2')
                request.session.pop('force_website_id')
            else:
                print('3')
                return website_id
        website_id = self.env.context.get('website_id')
        if website_id:
            print('4')
            return self.browse(website_id)

        if not request and not fallback:
            print('5')
            return self.browse(False)

        print('6')
        # The format of `httprequest.host` is `domain:port`
        domain_name = request and request.httprequest.host or ''
        print(domain_name)

        website_id = self._get_current_website_id(domain_name, fallback=fallback)
        print(website_id)
        x = self.browse(website_id)
        print(x)
        
        return self.browse(website_id)
    
    def _trigram_enumerate_words(self, search_details, search, limit):
        """
        Browses through all words that need to be compared to the search term.
        It extracts all words of every field associated to models in the fields_per_model parameter.
        The search is restricted to a records having the non-zero pg_trgm.word_similarity() score.

        :param search_details: obtained from `_search_get_details()`
        :param search: search term to which words must be matched against
        :param limit: maximum number of records fetched per model to build the word list
        :return: yields words
        """
        match_pattern = r'[\w-]{%s,}' % min(4, len(search) - 3)
        similarity_threshold = 0.3
        lang = self.env.lang or 'en_US'
        for search_detail in search_details:
            model_name, fields = search_detail['model'], search_detail['search_fields']
            model = self.env[model_name]
            if search_detail.get('requires_sudo'):
                model = model.sudo()
            domain = search_detail['base_domain'].copy()
            fields = set(fields).intersection(model._fields)

            unaccent = get_unaccent_wrapper(self.env.cr)

            # Specific handling for fields being actually part of another model
            # through the `inherits` mechanism.
            # It gets the list of fields requested to search upon and that are
            # actually not part of the requested model itself but part of a
            # `inherits` model:
            #     {
            #       'name': {
            #           'table': 'ir_ui_view',
            #           'fname': 'view_id',
            #       },
            #       'url': {
            #           'table': 'ir_ui_view',
            #           'fname': 'view_id',
            #       },
            #       'another_field': {
            #           'table': 'another_table',
            #           'fname': 'record_id',
            #       },
            #     }
            inherits_fields = {
                inherits_model_fname: {
                    'table': self.env[inherits_model_name]._table,
                    'fname': inherits_field_name,
                }
                for inherits_model_name, inherits_field_name in model._inherits.items()
                for inherits_model_fname in self.env[inherits_model_name]._fields.keys()
                if inherits_model_fname in fields
            }
            similarities = []
            for field in fields:
                # Field might belong to another model (`inherits` mechanism)
                table = inherits_fields[field]['table'] if field in inherits_fields else model._table
                similarities.append(
                    sql.SQL("word_similarity({search}, {field})").format(
                        search=unaccent(sql.Placeholder('search')),
                        field=unaccent(sql.SQL("{table}.{field}").format(
                            table=sql.Identifier(table),
                            field=sql.Identifier(field)
                        )) if not model._fields[field].translate else
                        unaccent(sql.SQL("COALESCE({table}.{field}->>{lang}, {table}.{field}->>'en_US')").format(
                            table=sql.Identifier(table),
                            field=sql.Identifier(field),
                            lang=sql.Literal(lang)
                        )),
                    )
                )

            best_similarity = sql.SQL('GREATEST({similarities})').format(
                similarities=sql.SQL(', ').join(similarities)
            )

            from_clause = sql.SQL("FROM {table}").format(table=sql.Identifier(model._table))
            # Specific handling for fields being actually part of another model
            # through the `inherits` mechanism.
            for table_to_join in {
                field['table']: field['fname'] for field in inherits_fields.values()
            }.items():  # Removes duplicate inherits model
                from_clause = sql.SQL("""
                    {from_clause}
                    LEFT JOIN {inherits_table} ON {table}.{inherits_field} = {inherits_table}.id
                """).format(
                    from_clause=from_clause,
                    table=sql.Identifier(model._table),
                    inherits_table=sql.Identifier(table_to_join[0]),
                    inherits_field=sql.Identifier(table_to_join[1]),
                )
            query = sql.SQL("""
                SELECT {table}.id, {best_similarity} AS _best_similarity
                {from_clause}
                ORDER BY _best_similarity desc
                LIMIT 1000
            """).format(
                table=sql.Identifier(model._table),
                best_similarity=best_similarity,
                from_clause=from_clause,
            )
            self.env.cr.execute(query, {'search': search})
            ids = {row[0] for row in self.env.cr.fetchall() if row[1] and row[1] >= similarity_threshold}
            domain.append([('id', 'in', list(ids))])
            domain = AND(domain)
            records = model.search_read(domain, fields, limit=limit)
            print('YYY')
            print(records)
            for record in records:
                for field, value in record.items():
                    if isinstance(value, str):
                        value = value.lower()
                        yield from re.findall(match_pattern, value)

    def _basic_enumerate_words(self, search_details, search, limit):
        """
        Browses through all words that need to be compared to the search term.
        It extracts all words of every field associated to models in the fields_per_model parameter.

        :param search_details: obtained from `_search_get_details()`
        :param search: search term to which words must be matched against
        :param limit: maximum number of records fetched per model to build the word list
        :return: yields words
        """
        match_pattern = r'[\w-]{%s,}' % min(4, len(search) - 3)
        first = escape_psql(search[0])
        for search_detail in search_details:
            model_name, fields = search_detail['model'], search_detail['search_fields']
            model = self.env[model_name]
            if search_detail.get('requires_sudo'):
                model = model.sudo()
            domain = search_detail['base_domain'].copy()
            fields_domain = []
            fields = set(fields).intersection(model._fields)
            for field in fields:
                fields_domain.append([(field, '=ilike', '%s%%' % first)])
                fields_domain.append([(field, '=ilike', '%% %s%%' % first)])
                fields_domain.append([(field, '=ilike', '%%>%s%%' % first)])  # HTML
            domain.append(OR(fields_domain))
            domain = AND(domain)
            perf_limit = 1000
            records = model.search_read(domain, fields, limit=perf_limit)
            print('XXX')
            print(records)
            if len(records) == perf_limit:
                # Exact match might have been missed because the fetched
                # results are limited for performance reasons.
                exact_records, _ = model._search_fetch(search_detail, search, 1, None)
                if exact_records:
                    yield search
            for record in records:
                for field, value in record.items():
                    if isinstance(value, str):
                        value = value.lower()
                        if field == 'arch_db':
                            value = text_from_html(value)
                        for word in re.findall(match_pattern, value):
                            if word[0] == search[0]:
                                yield word.lower()