# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .leave import *


def register():
    Pool.register(
        Type,
        Period,
        Leave,
        Entitlement,
        Payment,
        Employee,
        EmployeeSummary,
        module='employee_leave', type_='model')
