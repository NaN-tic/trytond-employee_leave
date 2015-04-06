from trytond.model import ModelSQL, ModelView, fields

__all__ = ['LeaveType', 'Leave', 'LeavePeriod', 'Entitlement', 'Employee']


class LeaveType(ModelSQL, ModelView):
    __name__ = 'employee.leave.type'
    name = fields.Char('Name', required=True)
    # exclude_from reports = fields.Boolean('Exclude from reports', help='Used
    # for maternity leave and others which are not required.')


class Leave(ModelSQL, ModelView):
    __name__ = 'employee.leave'

    date = fields.Date('Date')
    hours = fields.Numeric('Hours')
    days = fields.Numeric('Days')
    #request = fields.Many2One('employee.leave.request', 'Request')
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    start = fields.DateTime('Start')
    end = fields.DateTime('End')
    comment = fields.Text('Comment')
    status = fields.Selection([
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
            ('done', 'Done'),
            ], 'State', required=True)

    # When the user is trying to approve a leave, the system should warn
    # the user if the employee exceeds it's entitlements for this leave type
    # on the current period.

    @staticmethod
    def default_status():
        return 'pending'


class LeavePeriod(ModelSQL, ModelView):
    __name__ = 'employee.leave.period'
    start = fields.Date('Start')
    end = fields.Date('End')


# TODO: WorkWeek


class Entitlement(ModelSQL, ModelView):
    __name__ = 'employee.leave.entitlement'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    days = fields.Numeric('Days', required=True)
    pending_approval = fields.Function(fields.Numeric('Pending Approval'))
    scheduled = fields.Function(fields.Numeric('Scheduled'))
    done = fields.Function(fields.Numeric('Done'))
    available = fields.Function(fields.Numeric('Pending Approval'))


class Employee:
    __name__ = 'company.employee'
    # This is to report current situation of available leaves on the employee
    # form
    leave_status = fields.One2Many('employee.leave.employe_period_type',
        'employee', 'Leave Status')


# It should be possible to have several Entitlements per employee & type &
# period. This way, entitlements can be used when the user is rewarded with more
# holidays instead of paying them more when working more hours.
class EmployeePeriodType(ModelSQL):
    __name__ = 'employee.leave.employe_period_type'

    #Should be based on a table query.


class EmployeeEntitlement(ModelSQL, ModelView):
    __name__ = 'company.employee-employee.leave.eentitlement'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    entitlement = fields.Many2One('employee.leave.entitlement', 'Entitlement',
        required=True)
    #type = fields.Function(fields.Many2One('employee.leave.type', 'Type'),
        #'get_entitlement_fields', searcher='search_entitlement_fields')
    #period = fields.Function(fields.Many2One('employee.leave.period', 'Period'),
        #'get_entitlement_fields', searcher='search_entitlement_fields')
    #days = fields.Function(fields.Numeric('Days'), 'get_entitlement_fields',
        #searcher='search_entitlement_fields')
    #pending_approval = fields.Function(fields.Numeric('Pending Approval'))
    #scheduled = fields.Function(fields.Numeric('Scheduled'))
    #done = fields.Function(fields.Numeric('Done'))
    #available = fields.Function(fields.Numeric('Pending Approval'))
#
    #@classmethod
    #def get_entitlement_fields(cls, records, names):
#
    #@classmethod
    #def search_entitlement_fields(cls):


#class LeaveRequest(ModelSQL, ModelView):
    #__name__ = 'employee.leave.request'
    #type = fields.Many2One('employee.leave.type', 'Type', required=True)
    #employee = fields.Many2One('company.employee', 'Employee', required=True)
    #date_applied = fields.Date('Date Applied', required=True)
    #comment = fields.Text('Comment')


#CREATE TABLE ohrm_leave (id INT AUTO_INCREMENT, date DATE, length_hours DECIMAL(6, 2), length_days DECIMAL(4, 2), status SMALLINT, comments TEXT, leave_request_id INT UNSIGNED NOT NULL, leave_type_id INT UNSIGNED NOT NULL, emp_number INT NOT NULL, start_time TIME, end_time TIME, duration_type INT, PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_adjustment (id INT AUTO_INCREMENT, emp_number BIGINT, no_of_days DECIMAL(6, 2) NOT NULL, leave_type_id INT UNSIGNED NOT NULL, from_date DATETIME NOT NULL, to_date DATETIME, credited_date DATETIME, note VARCHAR(255), adjustment_type INT DEFAULT '0' NOT NULL, deleted TINYINT DEFAULT '0' NOT NULL, created_by_id BIGINT, created_by_name VARCHAR(255), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_comment (id INT AUTO_INCREMENT, leave_id INT UNSIGNED NOT NULL, created datetime, created_by_name VARCHAR(255) NOT NULL, created_by_id BIGINT, created_by_emp_number INT, comments VARCHAR(255), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_entitlement (id INT AUTO_INCREMENT, emp_number BIGINT, no_of_days DECIMAL(6, 2) NOT NULL, days_used DECIMAL(4, 2), leave_type_id INT UNSIGNED NOT NULL, from_date DATETIME NOT NULL, to_date DATETIME, credited_date DATETIME, note VARCHAR(255), entitlement_type INT NOT NULL, deleted TINYINT DEFAULT '0' NOT NULL, created_by_id BIGINT, created_by_name VARCHAR(255), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_entitlement_adjustment (id INT AUTO_INCREMENT, adjustment_id INT, entitlement_id INT UNSIGNED, length_days DECIMAL(4, 2), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_entitlement_type (id INT AUTO_INCREMENT, name VARCHAR(50) NOT NULL, is_editable TINYINT DEFAULT '0' NOT NULL, PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_leave_entitlement (id INT AUTO_INCREMENT, leave_id INT, entitlement_id INT UNSIGNED, length_days DECIMAL(4, 2), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_period_history (id INT AUTO_INCREMENT, leave_period_start_month BIGINT, leave_period_start_day BIGINT, created_at DATE, PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_request (id INT UNSIGNED AUTO_INCREMENT, leave_type_id INT UNSIGNED NOT NULL, date_applied DATE NOT NULL, emp_number INT NOT NULL, comments TEXT, PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_request_comment (id INT AUTO_INCREMENT, leave_request_id INT UNSIGNED NOT NULL, created datetime, created_by_name VARCHAR(255) NOT NULL, created_by_id BIGINT, created_by_emp_number INT, comments VARCHAR(255), PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_status (id INT AUTO_INCREMENT, status SMALLINT, name VARCHAR(100) NOT NULL, PRIMARY KEY(id)) ENGINE = INNODB;
#CREATE TABLE ohrm_leave_type (id INT UNSIGNED AUTO_INCREMENT, name VARCHAR(50) NOT NULL, exclude_in_reports_if_no_entitlement TINYINT(1), deleted TINYINT DEFAULT '0' NOT NULL, operational_country_id INT UNSIGNED, PRIMARY KEY(id)) ENGINE = INNODB;
