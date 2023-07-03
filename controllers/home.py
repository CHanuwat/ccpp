# # Part of Odoo. See LICENSE file for full copyright and licensing details.

# import json
# import logging


# import odoo
# import odoo.modules.registry
# from odoo import http
# from odoo.exceptions import AccessError
# from odoo.http import request
# from odoo.service import security
# from odoo.tools import ustr
# from odoo.tools.translate import _
# from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url, is_user_internal
# from odoo.addons.website.controllers.main import Website

# _logger = logging.getLogger(__name__)


# # Shared parameters for all login/signup flows
# SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
#                           'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
#                           'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
# LOGIN_SUCCESSFUL_PARAMS = set()


# class Home(Website):

#     @http.route('/', type='http', auth="none")
#     def index(self, s_action=None, db=None, **kw):
#         print("Max"*200)
#         print(request.session.uid)
#         if request.session.uid and not is_user_internal(request.session.uid):
#             return request.redirect_query('/web/login_successful', query=request.params)
#         return request.redirect_query('/web', query=request.params)
    
#     @http.route('/web', type='http', auth="none")
#     def web_client(self, s_action=None, **kw):

#         # Ensure we have both a database and a user
#         ensure_db()
#         print("1"*100)
#         if not request.session.uid:
#             print("2"*100)
#             return request.redirect('/web/login', 303)
#         if kw.get('redirect'):
#             print("3"*100)
#             return request.redirect(kw.get('redirect'), 303)
#         if not security.check_session(request.session, request.env):
#             print("4"*100)
#             raise http.SessionExpiredException("Session expired")
#         if not is_user_internal(request.session.uid):
#             print("5"*100)
#             return request.redirect('/web/login_successful', 303)

#         # Side-effect, refresh the session lifetime
#         request.session.touch()

#         # Restore the user on the environment, it was lost due to auth="none"
#         request.update_env(user=request.session.uid)
#         try:
#             print("6"*100)
#             context = request.env['ir.http'].webclient_rendering_context()
#             response = request.render('web.webclient_bootstrap', qcontext=context)
#             response.headers['X-Frame-Options'] = 'DENY'
#             #response.headers['X-Frame-Options'] = 'DENY'
#             return response
#         except AccessError:
#             return request.redirect('/web/login?error=access')
        

from odoo import http
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.utils import is_user_internal

import logging
import werkzeug
from werkzeug.urls import url_encode

from odoo import http, tools, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import ensure_db, Home, SIGN_UP_REQUEST_PARAMS, LOGIN_SUCCESSFUL_PARAMS
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request
import re

_logger = logging.getLogger(__name__)

class Home(WebHome):
    
    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()
        if qcontext.get('password',False):
            password = qcontext.get('password')
            get_param = request.env['ir.config_parameter'].sudo().get_param
            config_strength = get_param('user_password_strength.is_strength')
            config_digit = get_param('user_password_strength.is_digit')
            config_upper = get_param('user_password_strength.is_upper')
            config_lower = get_param('user_password_strength.is_lower')
            config_special_symbol = get_param('user_password_strength.is_special_symbol')

            # calculating the length
            length_error = len(password) < 8
            if length_error and config_strength:
                qcontext['error'] = "Password need 8 character or more"

            # searching for digits
            digit_error = re.search(r"\d", password) is None
            if digit_error and config_digit:
                qcontext['error'] = "Password must have 1 digit"
        
            # searching for uppercase
            uppercase_error = re.search(r"[A-Z]", password) is None
            if uppercase_error and config_upper:
                qcontext['error'] = "Password must have 1 character uppercase [A-Z]"

            # searching for lowercase
            lowercase_error = re.search(r"[a-z]", password) is None
            if lowercase_error and config_lower:
                qcontext['error'] = "Password must have 1 character lowercase [a-z]"

            # searching for symbols
            symbol_error = re.search("[~!@#$%^&*]", password) is None
            if symbol_error and config_special_symbol:
                sym = "[~!@#$%^&*]"
                qcontext['error'] = "Password must have 1 symbol %s"%sym

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _("Password reset instructions sent to your email")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search([('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode({'login': user.login, 'redirect': '/web'}))
        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response