# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import employee
from . import leave


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationStateColor,
        employee.Employee,
        leave.Type,
        leave.Period,
        leave.Leave,
        leave.LeaveCalendarContext,
        leave.Entitlement,
        leave.Payment,
        leave.Employee,
        leave.EmployeeSummary,
        module='employee_leave', type_='model')
