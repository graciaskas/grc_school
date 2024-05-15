# -*- coding: utf-8 -*-
from odoo import fields, models, api


class Faculty(models.Model):
    _name = 'school.faculty'
    _description = 'School faculty'

    name = fields.Char(string='Faculty name',required=True)
