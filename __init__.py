# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .leave import *

def register():
    Pool.register(
        LeaveType,
        LeavePeriod,
        Leave,
        Entitlement,
        LeavePayment,
        Employee,
        LeaveSummary,
        module='employee_leave', type_='model')
