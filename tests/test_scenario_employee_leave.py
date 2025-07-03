import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from proteus import Model
from trytond.exceptions import UserWarning
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules, set_user


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        today = datetime.date.today()

        # Install employee_leave
        activate_modules('employee_leave')

        # Create company
        _ = create_company()
        company = get_company()

        # Create employee
        Party = Model.get('party.party')
        party = Party(name='Employee')
        party.save()
        Employee = Model.get('company.employee')
        employee = Employee()
        employee.party = party
        employee.company = company
        employee.save()
        employee2 = Employee()
        employee2.party = party
        employee2.company = company
        employee2.save()

        # Create leave user
        User = Model.get('res.user')
        Group = Model.get('res.group')
        leave_user = User()
        leave_user.name = 'Employee Leave'
        leave_user.login = 'leave'
        leave_group, = Group.find([('name', '=', 'Employee Leave')])
        leave_user.groups.append(leave_group)
        leave_user.employees.append(employee)
        leave_user.employee = employee
        leave_user.save()

        # Create leave admin user
        Lang = Model.get('ir.lang')
        english, = Lang.find([('code', '=', 'en')])
        leave_admin_user = User()
        leave_admin_user.name = 'Leave Admin'
        leave_admin_user.login = 'leave_admin'
        leave_admin_group, = Group.find([
            ('name', '=', 'Employee Leave Administration'),
        ])
        leave_admin_user.groups.append(leave_admin_group)
        leave_admin_user.groups.append(Group(leave_group.id))
        leave_admin_user.language = english
        leave_admin_user.save()
        set_user(leave_admin_user)

        # Create leave period
        Period = Model.get('employee.leave.period')
        period = Period(name='%s' % today.year)
        period.start = datetime.date(today.year, 1, 1)
        period.end = datetime.date(today.year, 12, 31)
        period.save()

        # Create leave types
        Type = Model.get('employee.leave.type')
        holidays = Type(name='Holidays')
        holidays.save()
        other = Type(name='Other')
        other.save()

        # Create entitlements
        Entitlement = Model.get('employee.leave.entitlement')
        entitlement = Entitlement()
        entitlement.employee = employee
        entitlement.period = period
        entitlement.type = holidays
        entitlement.hours = Decimal(184)
        entitlement.save()

        # Create payments
        Payment = Model.get('employee.leave.payment')
        payment = Payment()
        payment.employee = employee
        payment.period = period
        payment.type = holidays
        payment.date = today
        payment.hours = Decimal(4)
        payment.save()

        # Create leaves
        set_user(leave_user)
        Leave = Model.get('employee.leave')
        first_leave = Leave()
        self.assertEqual(first_leave.request_date, today)
        self.assertEqual(first_leave.employee, employee)
        first_leave.period = period
        first_leave.type = holidays
        self.assertEqual(first_leave.request_date, today)
        first_leave.hours = Decimal(24)
        first_leave.start = today
        first_leave.end = today + relativedelta(days=2)
        self.assertEqual(first_leave.state, 'pending')
        first_leave.save()
        second_leave = Leave()
        second_leave.period = period
        second_leave.type = holidays
        second_leave.hours = Decimal(16)
        second_leave.start = today
        second_leave.end = today + relativedelta(days=1)
        second_leave.save()
        third_leave = Leave()
        third_leave.employee = employee
        third_leave.period = period
        third_leave.type = holidays
        third_leave.request_date = today + relativedelta(days=-1)
        third_leave.start = today
        third_leave.end = today
        third_leave.hours = Decimal(8)
        third_leave.save()

        # Approve and done leaves
        set_user(leave_admin_user)
        second_leave.click('approve')
        third_leave.click('approve')
        third_leave.click('done')

        # Check summary
        employee.reload()
        summary_by_type = {s.type.id: s for s in employee.leave_summary}
        self.assertEqual(len(summary_by_type), 2)
        holiday_summary = summary_by_type[holidays.id]
        self.assertEqual(holiday_summary.id,
                         (employee.id * 100 + period.id * 10 + holidays.id))
        self.assertEqual(holiday_summary.type.name, 'Holidays')
        self.assertEqual(holiday_summary.hours, Decimal('184.0'))
        self.assertEqual(holiday_summary.paid, Decimal('4.0'))
        self.assertEqual(holiday_summary.done, Decimal('8.0'))
        self.assertEqual(holiday_summary.scheduled, Decimal('16.0'))
        self.assertEqual(holiday_summary.pending_approval, Decimal('24.0'))
        self.assertEqual(holiday_summary.available, Decimal('156.0'))
        other_summary = summary_by_type[other.id]
        self.assertEqual(other_summary.type.name, 'Other')
        self.assertEqual(other_summary.hours, None)
        self.assertEqual(other_summary.paid, None)
        self.assertEqual(other_summary.done, None)
        self.assertEqual(other_summary.scheduled, None)
        self.assertEqual(other_summary.pending_approval, None)
        self.assertEqual(other_summary.available, None)

        # Leave of 4 hours per week during 30 weeks (120 hours in 210 days)
        little_long_leave = Leave()
        little_long_leave.employee = employee
        little_long_leave.period = period
        little_long_leave.type = holidays
        little_long_leave.start = today + relativedelta(days=30)
        little_long_leave.end = today + relativedelta(days=240)
        little_long_leave.hours = Decimal(120)
        little_long_leave.save()
        little_long_leave.click('approve')

        # Check new available hours of holidays
        employee.reload()
        summary_by_type = {s.type.id: s for s in employee.leave_summary}
        self.assertEqual(summary_by_type[holidays.id].available,
                         Decimal('36.0'))

        # Ask for more leaves than available
        unavailable_leave = Leave()
        unavailable_leave.employee = employee
        unavailable_leave.period = period
        unavailable_leave.type = holidays
        unavailable_leave.start = datetime.date(2015, 8, 1)
        unavailable_leave.end = datetime.date(2015, 8, 5)
        unavailable_leave.hours = Decimal(40)
        unavailable_leave.save()

        with self.assertRaises(UserWarning):
            unavailable_leave.click('approve')

        employee2_leave = Leave()
        employee2_leave.employee = employee2
        employee2_leave.period = period
        employee2_leave.type = holidays
        employee2_leave.start = datetime.date(2015, 8, 1)
        employee2_leave.end = datetime.date(2015, 8, 5)
        employee2_leave.hours = Decimal(40)
        employee2_leave.save()

        set_user(leave_user)

        self.assertEqual(len(Leave.find([])), 6)
        self.assertEqual(len(Leave.find([('mine', '=', True)])), 5)
        self.assertEqual(len(Leave.find([('mine', '=', False)])), 1)
        self.assertEqual(len(Leave.find([('mine', '!=', True)])), 1)
        self.assertEqual(len(Leave.find([('mine', '!=', False)])), 5)
