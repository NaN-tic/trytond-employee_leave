========================
Employee Leaves Scenario
========================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import Model
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()

Install employee_leave::

    >>> config = activate_modules('employee_leave')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create employee::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> Employee = Model.get('company.employee')
    >>> employee = Employee()
    >>> employee.party = party
    >>> employee.company = company
    >>> employee.save()

Create leave user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> leave_user = User()
    >>> leave_user.name = 'Employee Leave'
    >>> leave_user.login = 'leave'
    >>> leave_user.main_company = company
    >>> leave_group, = Group.find([('name', '=', 'Employee Leave')])
    >>> leave_user.groups.append(leave_group)
    >>> leave_user.employees.append(employee)
    >>> leave_user.employee = employee
    >>> leave_user.save()

Create leave admin user::

    >>> Lang = Model.get('ir.lang')
    >>> english, = Lang.find([('code', '=', 'en')])
    >>> leave_admin_user = User()
    >>> leave_admin_user.name = 'Leave Admin'
    >>> leave_admin_user.login = 'leave_admin'
    >>> leave_admin_user.main_company = company
    >>> leave_admin_group, = Group.find([
    ...     ('name', '=', 'Employee Leave Administration')])
    >>> leave_admin_user.groups.append(leave_admin_group)
    >>> leave_admin_user.language = english
    >>> leave_admin_user.save()
    >>> set_user(leave_admin_user)

Create leave period::

    >>> Period = Model.get('employee.leave.period')
    >>> period = Period(name='%s' % today.year)
    >>> period.start = datetime.date(today.year, 1, 1)
    >>> period.end = datetime.date(today.year, 12, 31)
    >>> period.save()

Create leave types::

    >>> Type = Model.get('employee.leave.type')
    >>> holidays = Type(name='Holidays')
    >>> holidays.save()

    >>> other = Type(name='Other')
    >>> other.save()

Create entitlements::

    >>> Entitlement = Model.get('employee.leave.entitlement')
    >>> entitlement = Entitlement()
    >>> entitlement.employee = employee
    >>> entitlement.period = period
    >>> entitlement.type = holidays
    >>> entitlement.hours = Decimal(184)
    >>> entitlement.save()

Create payments::

    >>> Payment = Model.get('employee.leave.payment')
    >>> payment = Payment()
    >>> payment.employee = employee
    >>> payment.period = period
    >>> payment.type = holidays
    >>> payment.date = today
    >>> payment.hours = Decimal(4)
    >>> payment.save()

Create leaves::

    >>> set_user(leave_user)
    >>> Leave = Model.get('employee.leave')
    >>> first_leave = Leave()
    >>> first_leave.request_date == today
    True
    >>> first_leave.employee == employee
    True
    >>> first_leave.period = period
    >>> first_leave.type = holidays
    >>> first_leave.request_date == today
    True
    >>> first_leave.hours = Decimal(24)
    >>> first_leave.start = today
    >>> first_leave.end = today + relativedelta(days=2)
    >>> first_leave.state
    'pending'
    >>> first_leave.save()

    >>> second_leave = Leave()
    >>> second_leave.period = period
    >>> second_leave.type = holidays
    >>> second_leave.hours = Decimal(16)
    >>> second_leave.start = today
    >>> second_leave.end = today + relativedelta(days=1)
    >>> second_leave.save()

    >>> third_leave = Leave()
    >>> third_leave.employee = employee
    >>> third_leave.period = period
    >>> third_leave.type = holidays
    >>> third_leave.request_date = today + relativedelta(days=-1)
    >>> third_leave.start = today
    >>> third_leave.end = today
    >>> third_leave.hours = Decimal(8)
    >>> third_leave.save()

Approve and done leaves::

    >>> set_user(leave_admin_user)
    >>> second_leave.click('approve')
    >>> third_leave.click('approve')
    >>> third_leave.click('done')

Check summary::

    >>> employee.reload()
    >>> summary_by_type = {s.type.id: s for s in employee.leave_summary}
    >>> len(summary_by_type)
    2
    >>> holiday_summary = summary_by_type[holidays.id]
    >>> holiday_summary.id == (employee.id * 100 + period.id * 10 + holidays.id)
    True
    >>> holiday_summary.type.name
    'Holidays'
    >>> holiday_summary.hours == Decimal('184.0')
    True
    >>> holiday_summary.paid == Decimal('4.0')
    True
    >>> holiday_summary.done == Decimal('8.0')
    True
    >>> holiday_summary.scheduled == Decimal('16.0')
    True
    >>> holiday_summary.pending_approval == Decimal('24.0')
    True
    >>> holiday_summary.available == Decimal('156.0')
    True
    >>> other_summary = summary_by_type[other.id]
    >>> other_summary.type.name
    'Other'
    >>> other_summary.hours is None
    True
    >>> other_summary.paid is None
    True
    >>> other_summary.done is None
    True
    >>> other_summary.scheduled is None
    True
    >>> other_summary.pending_approval is None
    True
    >>> other_summary.available is None
    True

Leave of 4 hours per week during 30 weeks (120 hours in 210 days)::

    >>> little_long_leave = Leave()
    >>> little_long_leave.employee = employee
    >>> little_long_leave.period = period
    >>> little_long_leave.type = holidays
    >>> little_long_leave.start = today + relativedelta(days=30)
    >>> little_long_leave.end = today + relativedelta(days=240)
    >>> little_long_leave.hours = Decimal(120)
    >>> little_long_leave.save()
    >>> little_long_leave.click('approve')

Check new available hours of holidays::

    >>> employee.reload()
    >>> summary_by_type = {s.type.id: s for s in employee.leave_summary}
    >>> summary_by_type[holidays.id].available == Decimal('36.0')
    True

Ask for more leaves than available::

    >>> unavailable_leave = Leave()
    >>> unavailable_leave.employee = employee
    >>> unavailable_leave.period = period
    >>> unavailable_leave.type = holidays
    >>> unavailable_leave.start = datetime.date(2015, 8, 1)
    >>> unavailable_leave.end = datetime.date(2015, 8, 5)
    >>> unavailable_leave.hours = Decimal(40)
    >>> unavailable_leave.save()
    >>> unavailable_leave.click('approve')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    UserWarning: ('UserWarning', ('leave_exceds_5', 'The leave "Holidays, 08/01/2015, 40" exceeds the available hours (36h) for employee "Employee" and entitlement type "Holidays" on period "2016".', ''))
