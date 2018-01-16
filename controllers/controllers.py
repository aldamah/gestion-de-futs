# -*- coding: utf-8 -*-
from odoo import http

# class GestionDeFuts(http.Controller):
#     @http.route('/gestion_de_futs/gestion_de_futs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gestion_de_futs/gestion_de_futs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gestion_de_futs.listing', {
#             'root': '/gestion_de_futs/gestion_de_futs',
#             'objects': http.request.env['gestion_de_futs.gestion_de_futs'].search([]),
#         })

#     @http.route('/gestion_de_futs/gestion_de_futs/objects/<model("gestion_de_futs.gestion_de_futs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gestion_de_futs.object', {
#             'object': obj
#         })