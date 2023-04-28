# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging


import odoo
import odoo.modules.registry
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.service import security
from odoo.tools import ustr
from odoo.tools.translate import _
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url, is_user_internal
from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)


# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


class Home(Website):

    @http.route('/', type='http', auth="none")
    def index(self, s_action=None, db=None, **kw):
        print("Max"*200)
        print(request.session.uid)
        if request.session.uid and not is_user_internal(request.session.uid):
            return request.redirect_query('/web/login_successful', query=request.params)
        return request.redirect_query('/web', query=request.params)