# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.employee_leave.tests.test_employee_leave import suite
except ImportError:
    from .test_employee_leave import suite

__all__ = ['suite']
