# See LICENSE file for full copyright and licensing details.

# import time
import calendar
import re

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _

EM = r"[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"


def emailvalidation(email):
    """Check valid email."""
    if email:
        email_regex = re.compile(EM)
        if not email_regex.match(email):
            raise ValidationError(
                _(
                    """This seems not to be valid email.
Please enter email in correct format !"""
                )
            )


class AcademicYear(models.Model):
    """Defines an academic year."""

    _name = "school.academic_year"
    _description = "Academic Year"
    _order = "sequence"

    sequence = fields.Integer(
        "Sequence",
        required=True,
        help="Sequence order you want to see this year.",
    )
    name = fields.Char("Name", required=True, help="Name of academic year")
    code = fields.Char("Code", required=True, help="Code of academic year")
    date_start = fields.Date(
        "Start Date", required=True, help="Starting date of academic year"
    )
    date_stop = fields.Date("End Date", required=True, help="Ending of academic year")
    month_ids = fields.One2many(
        "academic.month", "year_id", "Months", help="Related Academic months"
    )
    grade_id = fields.Many2one("grade.master", "Grade", help="Grade")
    current = fields.Boolean("Current", help="Set Active Current Year")
    description = fields.Text("Description", help="Description")

    @api.model
    def next_year(self, sequence):
        """This method assign sequence to years"""
        year_rec = self.search([("sequence", ">", sequence)], order="id", limit=1)
        if year_rec:
            return year_rec.id or False

    def name_get(self):
        """Method to display name and code"""
        return [(rec.id, " [" + rec.code + "]" + rec.name) for rec in self]

    def generate_academicmonth(self):
        """Generate academic months."""
        interval = 1
        month_obj = self.env["school.academic_month"]
        for rec in self:
            start_date = rec.date_start
            while start_date < rec.date_stop:
                end_date = start_date + relativedelta(months=interval, days=-1)
                if end_date > rec.date_stop:
                    end_date = rec.date_stop
                month_obj.create(
                    {
                        "name": start_date.strftime("%B"),
                        "code": start_date.strftime("%m/%Y"),
                        "date_start": start_date,
                        "date_stop": end_date,
                        "year_id": rec.id,
                    }
                )
                start_date = start_date + relativedelta(months=interval)

    @api.constrains("date_start", "date_stop")
    def _check_academic_year(self):
        """Method to check start date should be greater than end date
        also check that dates are not overlapped with existing academic
        year"""
        new_start_date = self.date_start
        new_stop_date = self.date_stop
        delta = new_stop_date - new_start_date
        if delta.days > 365 and not calendar.isleap(new_start_date.year):
            raise ValidationError(_("The duration of the academic year is invalid."))
        if self.date_stop and self.date_start and self.date_stop < self.date_start:
            raise ValidationError(
                _(
                    "The start date of the academic year should be less than "
                    "end date."
                )
            )
        for old_ac in self.search([("id", "not in", self.ids)]):
            # Check start date should be less than stop date
            if (
                old_ac.date_start <= self.date_start <= old_ac.date_stop
                or old_ac.date_start <= self.date_stop <= old_ac.date_stop
            ):
                raise ValidationError(
                    _("Error! You cannot define overlapping academic years.")
                )

    @api.constrains("current")
    def check_current_year(self):
        """Constraint on active current year"""
        current_year_rec = self.search_count([("current", "=", True)])
        if current_year_rec >= 2:
            raise ValidationError(_("Error! You cannot set two current year active!"))


class AcademicMonth(models.Model):
    """Defining a month of an academic year."""

    _name = "academic.month"
    _description = "Academic Month"
    _order = "date_start"

    name = fields.Char("Name", required=True, help="Name")
    code = fields.Char("Code", required=True, help="Code")
    date_start = fields.Date("Start of Period", required=True, help="Start date")
    date_stop = fields.Date("End of Period", required=True, help="End Date")
    year_id = fields.Many2one(
        "academic.year",
        "Academic Year",
        required=True,
        help="Related academic year ",
    )
    description = fields.Text("Description", help="Description")

    _sql_constraints = [
        (
            "month_unique",
            "unique(date_start, date_stop, year_id)",
            "Academic Month should be unique!",
        )
    ]

    @api.constrains("year_id", "date_start", "date_stop")
    def _check_year_limit(self):
        """Method to check year limit"""
        if self.year_id and self.date_start and self.date_stop:
            if (
                self.year_id.date_stop < self.date_stop
                or self.year_id.date_stop < self.date_start
                or self.year_id.date_start > self.date_start
                or self.year_id.date_start > self.date_stop
            ):
                raise ValidationError(
                    _(
                        "Some of the months periods overlap or is not in the "
                        "academic year!"
                    )
                )

    @api.constrains("date_start", "date_stop")
    def check_months(self):
        """Method to check duration of date"""
        if self.date_stop and self.date_start and self.date_stop < self.date_start:
            raise ValidationError(
                _("End of Period date should be greater than Start of " "Periods Date!")
            )
        # Check start date should be less than stop date."""
        exist_month_rec = self.search([("id", "not in", self.ids)])
        for old_month in exist_month_rec:
            if (
                old_month.date_start <= self.date_start <= old_month.date_stop
                or old_month.date_start <= self.date_stop <= old_month.date_stop
            ):
                raise ValidationError(_("Error! You cannot define overlapping months!"))


class StandardMedium(models.Model):
    """Defining a medium(ENGLISH, HINDI, GUJARATI) related to standard"""

    _name = "standard.medium"
    _description = "Standard Medium"
    _order = "sequence"

    sequence = fields.Integer("Sequence", required=True, help="Sequence of the record")
    name = fields.Char("Name", required=True, help="Medium of the standard")
    code = fields.Char("Code", required=True, help="Medium code")
    description = fields.Text("Description", help="Description")


class StandardDivision(models.Model):
    """Defining a division(A, B, C) related to standard"""

    _name = "standard.division"
    _description = "Standard Division"
    _order = "sequence"

    sequence = fields.Integer("Sequence", required=True, help="Sequence of the record")
    name = fields.Char("Name", required=True, help="Division of the standard")
    code = fields.Char("Code", required=True, help="Standard code")
    description = fields.Text("Description", help="Description")


class StandardStandard(models.Model):
    """Defining Standard Information."""

    _name = "standard.standard"
    _description = "Standard Information"
    _order = "sequence"

    sequence = fields.Integer("Sequence", required=True, help="Sequence of the record")
    name = fields.Char("Name", required=True, help="Standard name")
    code = fields.Char("Code", required=True, help="Code of standard")
    description = fields.Text("Description", help="Description")

    @api.model
    def next_standard(self, sequence):
        """This method check sequence of standard"""
        stand_rec = self.search([("sequence", ">", sequence)], order="id", limit=1)
        return stand_rec and stand_rec.id or False


class SchoolStandard(models.Model):
    """Defining a standard related to school."""

    _name = "school.standard"
    _description = "School Standards"
    _rec_name = "standard_id"

    @api.depends("standard_id", "school_id", "division_id", "medium_id", "school_id")
    def _compute_student(self):
        """Compute student of done state"""
        student_obj = self.env["student.student"]
        for rec in self:
            rec.student_ids = student_obj.search(
                [
                    ("standard_id", "=", rec.id),
                    ("school_id", "=", rec.school_id.id),
                    ("division_id", "=", rec.division_id.id),
                    ("medium_id", "=", rec.medium_id.id),
                    ("state", "=", "done"),
                ]
            )

    @api.depends("subject_ids")
    def _compute_subject(self):
        """Method to compute subjects."""
        for rec in self:
            rec.total_no_subjects = len(rec.subject_ids)

    @api.depends("student_ids")
    def _compute_total_student(self):
        """Method to compute total student."""
        for rec in self:
            rec.total_students = len(rec.student_ids)

    @api.depends("capacity", "total_students")
    def _compute_remain_seats(self):
        """Method to compute remaining seats."""
        for rec in self:
            rec.remaining_seats = rec.capacity - rec.total_students

    school_id = fields.Many2one(
        "school.school",
        "School",
        required=True,
        help="School of the following standard",
    )
    standard_id = fields.Many2one(
        "standard.standard", "Standard", required=True, help="Standard"
    )
    division_id = fields.Many2one(
        "standard.division",
        "Division",
        required=True,
        help="Standard division",
    )
    medium_id = fields.Many2one(
        "standard.medium",
        "Medium",
        required=True,
        help="Medium of the standard",
    )
    subject_ids = fields.Many2many(
        "subject.subject",
        "subject_standards_rel",
        "subject_id",
        "standard_id",
        "Subject",
        help="Subjects of the standard",
    )
    user_id = fields.Many2one(
        "school.teacher", "Class Teacher", help="Teacher of the standard"
    )
    student_ids = fields.One2many(
        "student.student",
        "standard_id",
        "Student In Class",
        compute="_compute_student",
        store=True,
        help="Students which are in this standard",
    )
    color = fields.Integer("Color Index", help="Index of color")
    cmp_id = fields.Many2one(
        "res.company",
        "Company Name",
        related="school_id.company_id",
        store=True,
        help="Company_id of the school",
    )
    syllabus_ids = fields.One2many(
        "subject.syllabus",
        "standard_id",
        "Syllabus",
        help="Syllabus of the following standard",
    )
    total_no_subjects = fields.Integer(
        "Total No of Subject",
        compute="_compute_subject",
        help="Total subjects in the standard",
    )
    name = fields.Char("Name", help="Standard name")
    capacity = fields.Integer("Total Seats", help="Standard capacity")
    total_students = fields.Integer(
        "Total Students",
        compute="_compute_total_student",
        store=True,
        help="Total students of the standard",
    )
    remaining_seats = fields.Integer(
        "Available Seats",
        compute="_compute_remain_seats",
        store=True,
        help="Remaining seats of the standard",
    )
    class_room_id = fields.Many2one(
        "class.room", "Room Number", help="Class room of the standard"
    )

    @api.onchange("standard_id", "division_id")
    def onchange_combine(self):
        """Onchange to assign name respective of it's standard and division"""
        self.name = str(self.standard_id.name) + "-" + str(self.division_id.name)

    @api.constrains("standard_id", "division_id")
    def check_standard_unique(self):
        """Method to check unique standard."""
        if self.env["school.standard"].search(
            [
                ("standard_id", "=", self.standard_id.id),
                ("division_id", "=", self.division_id.id),
                ("school_id", "=", self.school_id.id),
                ("id", "not in", self.ids),
            ]
        ):
            raise ValidationError(_("Division and class should be unique!"))

    def unlink(self):
        """Method to check unique standard."""
        for rec in self:
            if rec.student_ids or rec.subject_ids or rec.syllabus_ids:
                raise ValidationError(
                    _(
                        "You cannot delete as it has reference with student, "
                        "subject or syllabus!"
                    )
                )
        return super(SchoolStandard, self).unlink()

    @api.constrains("capacity")
    def check_seats(self):
        """Method to check seats."""
        if self.capacity <= 0:
            raise ValidationError(_("Total seats should be greater than 0!"))

    def name_get(self):
        """Method to display standard and division"""
        return [
            (rec.id, rec.standard_id.name + "[" + rec.division_id.name + "]")
            for rec in self
        ]


class SchoolSchool(models.Model):
    """Defining School Information"""

    _name = "school.school"
    _description = "School Information"
    _rec_name = "com_name"

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if self.env["school.school"].search(
                [("code", "=", record.code), ("id", "!=", record.id)]
            ):
                raise ValidationError(_("School Code must be Unique"))

    @api.model
    def _lang_get(self):
        """Method to get language"""
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]

    company_id = fields.Many2one(
        "res.company",
        "Company",
        ondelete="cascade",
        required=True,
        delegate=True,
        help="Company_id of the school",
    )
    com_name = fields.Char(
        "School Name",
        related="company_id.name",
        store=True,
        help="School name",
    )
    code = fields.Char("Code", required=True, help="School code")
    standards = fields.One2many(
        "school.standard", "school_id", "Standards", help="School standard"
    )
    lang = fields.Selection(
        _lang_get,
        "Language",
        help="""If the selected language is loaded in the
                                system, all documents related to this partner
                                will be printed in this language.
                                If not, it will be English.""",
    )
    required_age = fields.Integer(
        "Student Admission Age Required",
        default=6,
        help="""Minimum required age for
                                  student admission""",
    )

    @api.model
    def create(self, vals):
        """Inherited create method to assign company_id to school"""
        res = super(SchoolSchool, self).create(vals)
        main_company = self.env.ref("base.main_company")
        res.company_id.parent_id = main_company.id
        return res


class SubjectSubject(models.Model):
    """Defining a subject"""

    _name = "subject.subject"
    _description = "Subjects"

    name = fields.Char("Name", required=True, help="Subject name")
    code = fields.Char("Code", required=True, help="Subject code")
    maximum_marks = fields.Integer(
        "Maximum marks", help="Maximum marks of the subject can get"
    )
    minimum_marks = fields.Integer(
        "Minimum marks",
        help="""Required minimum
                                                     marks of the subject""",
    )
    weightage = fields.Integer("WeightAge", help="Weightage of the subject")
    teacher_ids = fields.Many2many(
        "school.teacher",
        "subject_teacher_rel",
        "subject_id",
        "teacher_id",
        "Teachers",
        help="Teachers of the following subject",
    )
    standard_ids = fields.Many2many(
        "standard.standard",
        string="Standards",
        help="""Standards in which the
                                    following subject taught""",
    )
    standard_id = fields.Many2one(
        "standard.standard",
        "Class",
        help="""Class in which the following
                                  subject taught""",
    )
    is_practical = fields.Boolean(
        "Is Practical", help="Check this if subject is practical."
    )
    elective_id = fields.Many2one(
        "subject.elective",
        help="""Elective subject respective
                                  the following subject""",
    )
    student_ids = fields.Many2many(
        "student.student",
        "elective_subject_student_rel",
        "subject_id",
        "student_id",
        "Students",
        help="Students who choose this subject",
    )

    @api.constrains("maximum_marks", "minimum_marks")
    def check_marks(self):
        """Method to check marks."""
        if self.minimum_marks >= self.maximum_marks:
            raise ValidationError(
                _("Configure Maximum marks greater than minimum marks!")
            )

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        """Override method to get exam of subject selection."""
        if (
            self._context.get("is_from_subject_report")
            and self._context.get("active_model")
            and self._context.get("active_id")
        ):

            teacher_rec = self.env[self._context.get("active_model")].browse(
                self._context.get("active_id")
            )
            sub_ids = [sub_id.id for sub_id in teacher_rec.subject_id]
            args.append(("id", "in", sub_ids))
        return super(SubjectSubject, self)._search(
            args=args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
        )


class SubjectSyllabus(models.Model):
    """Defining a  syllabus"""

    _name = "subject.syllabus"
    _description = "Syllabus"
    _rec_name = "subject_id"

    standard_id = fields.Many2one(
        "school.standard", "Standard", help="Standard which had this subject"
    )
    subject_id = fields.Many2one("subject.subject", "Subject", help="Subject")
    syllabus_doc = fields.Binary(
        "Syllabus Doc", help="Attach syllabus related to Subject"
    )


class SubjectElective(models.Model):
    """Defining Subject Elective"""

    _name = "subject.elective"
    _description = "Elective Subject"

    name = fields.Char("Name", help="Elective subject name")
    subject_ids = fields.One2many(
        "subject.subject",
        "elective_id",
        "Elective Subjects",
        help="Subjects of the respective elective subject",
    )


class MotherTongue(models.Model):
    """Defining mother tongue."""

    _name = "mother.toungue"
    _description = "Mother Toungue"

    name = fields.Char("Mother Tongue", help="Language name")


class StudentAward(models.Model):
    """Defining student award."""

    _name = "student.award"
    _description = "Student Awards"

    award_list_id = fields.Many2one(
        "student.student",
        "Student",
        help="Students who about to get the award",
    )
    name = fields.Char("Award Name", help="Award name")
    description = fields.Char("Description", help="Description")


class AttendanceType(models.Model):
    """Defining attendance type."""

    _name = "attendance.type"
    _description = "School Type"

    name = fields.Char("Name", required=True, help="Attendance type name")
    code = fields.Char("Code", required=True, help="Attendance type code")


class StudentDocument(models.Model):
    """Defining Student document."""

    _name = "student.document"
    _description = "Student Document"
    _rec_name = "doc_type"

    doc_id = fields.Many2one(
        "student.student", "Student", help="Student of the following doc"
    )
    file_no = fields.Char(
        "File No",
        readonly="1",
        default=lambda obj: obj.env["ir.sequence"].next_by_code("student.document"),
        help="File no of the document",
    )
    submited_date = fields.Date("Submitted Date", help="Document submitted date")
    doc_type = fields.Many2one(
        "document.type", "Document Type", required=True, help="Document type"
    )
    file_name = fields.Char("File Name", help="File name")
    return_date = fields.Date("Return Date", help="Document return date")
    new_datas = fields.Binary("Attachments", help="Attachments of the document")


class DocumentType(models.Model):
    """Defining a Document Type(SSC,Leaving)"""

    _name = "document.type"
    _description = "Document Type"
    _rec_name = "doc_type"
    _order = "seq_no"

    seq_no = fields.Char(
        "Sequence",
        readonly=True,
        default=lambda self: _("New"),
        help="Sequence of the document",
    )
    doc_type = fields.Char("Document Type", required=True, help="Document type")

    @api.model
    def create(self, vals):
        if vals.get("seq_no", _("New")) == _("New"):
            vals["seq_no"] = self.env["ir.sequence"].next_by_code("document.type") or _(
                "New"
            )
        return super(DocumentType, self).create(vals)


class StudentDescription(models.Model):
    """Defining a Student Description"""

    _name = "student.description"
    _description = "Student Description"

    des_id = fields.Many2one(
        "student.student", "Student Ref.", help="Student record from students"
    )
    name = fields.Char("Name", help="Description name")
    description = fields.Char("Description", help="Student description")


class StudentDescipline(models.Model):
    """Definign student dscipline."""

    _name = "student.descipline"
    _description = "Student Discipline"

    student_id = fields.Many2one("student.student", "Student", help="Student")
    teacher_id = fields.Many2one(
        "school.teacher", "Teacher", help="Teacher who examine the student"
    )
    date = fields.Date("Date", help="Date")
    class_id = fields.Many2one("standard.standard", "Class", help="Class of student")
    note = fields.Text("Note", help="Discipline Note")
    action_taken = fields.Text("Action Taken", help="Action taken against discipline")


class StudentHistory(models.Model):
    """Defining Student History."""

    _name = "student.history"
    _description = "Student History"

    student_id = fields.Many2one("student.student", "Student", help="Related Student")
    academice_year_id = fields.Many2one(
        "academic.year", "Academic Year", help="Academice Year"
    )
    standard_id = fields.Many2one(
        "school.standard", "Standard", help="Standard of the following student"
    )
    percentage = fields.Float(
        "Percentage", readonly=True, help="Percentage of the student"
    )
    result = fields.Char("Result", readonly=True, help="Result of the student")


class StudentCertificate(models.Model):
    """Defining student certificate."""

    _name = "student.certificate"
    _description = "Student Certificate"

    student_id = fields.Many2one("student.student", "Student", help="Related student")
    description = fields.Char("Description", help="Description")
    certi = fields.Binary("Certificate", required=True, help="Student certificate")


class StudentReference(models.Model):
    """Defining a student reference information"""

    _name = "student.reference"
    _description = "Student Reference"

    reference_id = fields.Many2one(
        "student.student", "Student", help="Student reference"
    )
    name = fields.Char("First Name", required=True, help="Student name")
    middle = fields.Char("Middle Name", required=True, help="Student middle name")
    last = fields.Char("Surname", required=True, help="Student last name")
    designation = fields.Char("Designation", required=True, help="Student designation")
    phone = fields.Char("Phone", required=True, help="Student phone")
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        "Gender",
        help="Student gender",
    )


class StudentPreviousSchool(models.Model):
    """Defining a student previous school information"""

    _name = "student.previous.school"
    _description = "Student Previous School"

    previous_school_id = fields.Many2one(
        "student.student", "Student", help="Related student"
    )
    name = fields.Char("Name", required=True, help="Student previous school name")
    registration_no = fields.Char(
        "Registration No.", required=True, help="Student registration number"
    )
    admission_date = fields.Date("Admission Date", help="Student admission date")
    exit_date = fields.Date("Exit Date", help="Student previous school exit date")
    course_id = fields.Many2one(
        "standard.standard", "Course", required=True, help="Student gender"
    )
    add_sub = fields.One2many(
        "academic.subject", "add_sub_id", "Add Subjects", help="Student gender"
    )

    @api.constrains("admission_date", "exit_date")
    def check_date(self):
        new_dt = fields.Date.today()
        if (self.admission_date and self.admission_date >= new_dt) or (
            self.exit_date and self.exit_date >= new_dt
        ):
            raise ValidationError(
                _(
                    "Your admission date and exit date should be less than "
                    "current date!"
                )
            )
        if (self.admission_date and self.exit_date) and (
            self.admission_date > self.exit_date
        ):
            raise ValidationError(
                _("Admission date should be less than exit date in previous school!")
            )


class AcademicSubject(models.Model):
    """Defining a student previous school information"""

    _name = "academic.subject"
    _description = "Student Previous School"

    add_sub_id = fields.Many2one(
        "student.previous.school",
        "Add Subjects",
        invisible=True,
        help="Select student previous school",
    )
    name = fields.Char("Name", required=True, help="Enter previous school name")
    maximum_marks = fields.Integer("Maximum marks", help="Enter maximum mark")
    minimum_marks = fields.Integer("Minimum marks", help="Enter minimum marks")


class StudentFamilyContact(models.Model):
    """Defining a student emergency contact information"""

    _name = "student.family.contact"
    _description = "Student Family Contact"

    @api.depends("relation", "stu_name")
    def _compute_get_name(self):
        for rec in self:
            relative_name = rec.name
            if rec.stu_name:
                rec.relative_name = rec.stu_name.name
            rec.relative_name = relative_name

    family_contact_id = fields.Many2one(
        "student.student", "Student Ref.", help="Enter related student"
    )
    rel_name = fields.Selection(
        [
            ("exist", "Link to Existing Student"),
            ("new", "Create New Relative Name"),
        ],
        "Related Student",
        help="Select Name",
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        "User ID",
        ondelete="cascade",
        help="Enter related user of the student",
    )
    stu_name = fields.Many2one(
        "student.student",
        "Existing Student",
        help="Select Student From Existing List",
    )
    name = fields.Char("Relative Name", help="Enter relative name")
    relation = fields.Many2one(
        "student.relation.master",
        "Relation",
        required=True,
        help="Select student relation with member",
    )
    phone = fields.Char("Phone", required=True, help="Enter family member contact")
    email = fields.Char("E-Mail", help="Enter student email")
    relative_name = fields.Char(
        compute="_compute_get_name",
        string="Name",
        help="Enter student family member name",
    )


class StudentRelationMaster(models.Model):
    """Student Relation Information"""

    _name = "student.relation.master"
    _description = "Student Relation Master"

    name = fields.Char("Name", required=True, help="Enter Relation name")
    seq_no = fields.Integer("Sequence", help="Relation sequence")


class GradeMaster(models.Model):
    """Defining grade master."""

    _name = "grade.master"
    _description = "Grade Master"

    name = fields.Char("Grade", required=True, help="Grade name")
    grade_ids = fields.One2many(
        "grade.line",
        "grade_id",
        "Grade Lines",
        help="Grade which are consider in this.",
    )


class GradeLine(models.Model):
    """Defining grade line."""

    _name = "grade.line"
    _description = "Grades"
    _rec_name = "grade"

    from_mark = fields.Integer(
        "From Marks",
        required=True,
        help="The grade will starts from this marks.",
    )
    to_mark = fields.Integer(
        "To Marks", required=True, help="The grade will ends to this marks."
    )
    grade = fields.Char("Grade", required=True, help="Grade")
    sequence = fields.Integer("Sequence", help="Sequence order of the grade.")
    fail = fields.Boolean(
        "Fail",
        help="""If fail field is set to True,
    it will allow you to set the grade as fail.""",
    )
    grade_id = fields.Many2one("grade.master", "Grade Ref.", help="Related grade")
    name = fields.Char("Name", help="Grade name")

    @api.constrains("from_mark", "to_mark")
    def check_marks(self):
        """Method to check overlapping of Marks"""
        for rec in self:
            if rec.to_mark < rec.from_mark:
                raise ValidationError(_("To Marks should be greater than From Marks!"))
            for line in self.search(
                [("grade_id", "=", rec.grade_id.id), ("id", "!=", rec.id)]
            ):
                if (
                    line.from_mark <= rec.from_mark <= line.to_mark
                    or line.from_mark <= rec.to_mark <= line.to_mark
                ):
                    raise ValidationError(
                        _("Error! You cannot define overlapping Marks!")
                    )


class StudentNews(models.Model):
    """Defining studen news."""

    _name = "school.student_news"
    _description = "Student News"
    _rec_name = "subject"
    _order = "date asc"

    subject = fields.Char("Subject", required=True, help="Subject of the news.")
    description = fields.Text("Description", help="Description")
    date = fields.Datetime("Expiry Date", help="Expiry date of the news.")
    user_ids = fields.Many2many(
        "res.users",
        "user_news_rel",
        "id",
        "user_ids",
        "User News",
        help="Name to whom this news is related.",
    )
    color = fields.Integer("Color Index", default=0, help="Color index")

    @api.constrains("date")
    def checknews_dates(self):
        """Check news date."""
        new_date = fields.datetime.today()
        if self.date < new_date:
            raise ValidationError(_("Configure expiry date greater than current date!"))

    def news_update(self):
        """Method to send email to student for news update"""
        emp_obj = self.env["hr.employee"]
        obj_mail_server = self.env["ir.mail_server"]
        user = self.env.user
        # Check if out going mail configured
        mail_server_record = obj_mail_server.search([], limit=1)
        if not mail_server_record:
            raise UserError(
                _(
                    """User Email Configuration!
    "Outgoing mail server not specified!"""
                )
            )
        email_list = []
        # Check email is defined in student
        for news in self:
            if news.user_ids and news.date:
                email_list = [
                    news_user.email for news_user in news.user_ids if news_user.email
                ]
                if not email_list:
                    raise UserError(
                        _(
                            """User Email Configuration!,
Email not found in users!"""
                        )
                    )
            # Check email is defined in user created from employee
            else:
                for employee in emp_obj.search([]):
                    if employee.work_email:
                        email_list.append(employee.work_email)
                    elif employee.user_id and employee.user_id.email:
                        email_list.append(employee.user_id.email)
                if not email_list:
                    raise UserError(
                        _(
                            """
                                Email Configuration!,Email not defined!
                            """
                        )
                    )
            news_date = news.create_date
            # Add company name while sending email
            company = user.company_id.name or ""
            body = """Hi,<br/><br/>
                    This is a news update from <b>{}</b> posted at {}<br/>
                    <br/> {} <br/><br/>
                    Thank you.""".format(
                company,
                news_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                news.description or "",
            )
            smtp_user = mail_server_record.smtp_user or False
            # Check if mail of outgoing server configured
            if not smtp_user:
                raise UserError(
                    _(
                        """Email Configuration,
Kindly,Configure Outgoing Mail Server!"""
                    )
                )
            notification = "Notification for news update."
            # Configure email
            message = obj_mail_server.build_email(
                email_from=smtp_user,
                email_to=email_list,
                subject=notification,
                body=body,
                body_alternative=body,
                reply_to=smtp_user,
                subtype="html",
            )
            # Send Email configured above with help of send mail method
            obj_mail_server.send_email(
                message=message, mail_server_id=mail_server_record.id
            )
        return True


class StudentReminder(models.Model):
    """Defining student reminder."""

    _name = "school.student_reminder"
    _description = "Student Reminder"

    @api.model
    def check_user(self):
        """Method to get default value of logged in Student"""
        return self.env["student.student"].search([("user_id", "=", self._uid)]).id

    stu_id = fields.Many2one(
        "student.student",
        "Student Name",
        required=True,
        default=check_user,
        help="Relative student",
    )
    name = fields.Char("Title", help="Reminder name")
    date = fields.Date("Date", help="Reminder date")
    description = fields.Text("Description", help="Description of the reminder")
    color = fields.Integer("Color Index", default=0, help="Color index")

    @api.constrains("date")
    def check_date(self):
        """Method to check constraint of due date and assign date"""
        if self.date < fields.Date.today():
            raise ValidationError(
                _("Reminder date of must be greater or equal current date !")
            )


class StudentCast(models.Model):
    """Defining student cast."""

    _name = "school.student_cast"
    _description = "Student Cast"

    name = fields.Char("Name", required=True, help="Student cast")


class ClassRoom(models.Model):
    """Defining class room."""

    _name = "school.class_room"
    _description = "School Class Room"

    name = fields.Char("Name", help="Class room name")
    number = fields.Char("Room Number", help="Class room number")


class Report(models.Model):
    _inherit = "ir.actions.report"

    def render_template(self, template, values=None):
        student_id = self._context.get("student_id")
        if student_id:
            student_rec = self.env["student.student"].browse(student_id)
        if student_rec and student_rec.state == "draft":
            raise ValidationError(
                _("You cannot print report forstudent in unconfirm state!")
            )
        return super(Report, self).render_template(template, values)
