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
            if not website_id:
                # Don't crash is session website got deleted
                request.session.pop('force_website_id')
            else:
                return website_id
        website_id = self.env.context.get('website_id')
        if website_id:
            return self.browse(website_id)

        if not request and not fallback:
            return self.browse(False)

        # The format of `httprequest.host` is `domain:port`
        domain_name = request and request.httprequest.host or ''

        website_id = self._get_current_website_id(domain_name, fallback=fallback)
        
        return self.browse(website_id)
