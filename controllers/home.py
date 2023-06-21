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
#         if not request.session.uid:
#             return request.redirect('/web/login', 303)
#         if kw.get('redirect'):
#             return request.redirect(kw.get('redirect'), 303)
#         if not security.check_session(request.session, request.env):
#             raise http.SessionExpiredException("Session expired")
#         if not is_user_internal(request.session.uid):
#             return request.redirect('/web/login_successful', 303)

#         # Side-effect, refresh the session lifetime
#         request.session.touch()

#         # Restore the user on the environment, it was lost due to auth="none"
#         request.update_env(user=request.session.uid)
#         try:
#             context = request.env['ir.http'].webclient_rendering_context()
#             response = request.render('web.webclient_bootstrap', qcontext=context)
#             response.headers['X-Frame-Options'] = 'DENY'
#             #response.headers['X-Frame-Options'] = 'DENY'
#             return response
#         except AccessError:
#             return request.redirect('/web/login?error=access')