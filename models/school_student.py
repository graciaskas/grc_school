# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Student(models.Model):
    _name = "school.student"
    _description = "Student"

    name = fields.Char("Student name")
