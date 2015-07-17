========================
Employee Leaves Scenario
========================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date(2015, 7, 17)  # make it previsible

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account::

    >>> Module = Model.get('ir.module.module')
    >>> modules = Module.find([
    ...         ('name', '=', 'employee_leave'),
    ...         ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find()

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

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

    >>> leave_user = User()
    >>> leave_user.name = 'Employee Leave'
    >>> leave_user.login = 'leave'
    >>> leave_user.main_company = company
    >>> leave_group, = Group.find([('name', '=', 'Employee Leave')])
    >>> leave_user.groups.append(leave_group)
    >>> leave_user.employees.append(employee)
    >>> leave_user.employee = employee
    >>> leave_user.save()
    >>> config._context = User.get_preferences(True, config.context)

Create leave admin user::

    >>> Lang = Model.get('ir.lang')
    >>> english, = Lang.find([('code', '=', 'en_US')])
    >>> leave_admin_user = User()
    >>> leave_admin_user.name = 'Leave Admin'
    >>> leave_admin_user.login = 'leave_admin'
    >>> leave_admin_user.main_company = company
    >>> leave_admin_group, = Group.find([
    ...     ('name', '=', 'Employee Leave Administration')])
    >>> leave_admin_user.groups.append(leave_admin_group)
    >>> leave_admin_user.language = english
    >>> leave_admin_user.save()
    >>> config.user = leave_admin_user.id

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

    >>> config.user = leave_user.id
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

    >>> config.user = leave_admin_user.id
    >>> config._context = User.get_preferences(True, config.context)
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
    u'Holidays'
    >>> holiday_summary.hours
    Decimal('184')
    >>> holiday_summary.paid
    Decimal('4')
    >>> holiday_summary.done
    Decimal('8')
    >>> holiday_summary.scheduled
    Decimal('16')
    >>> holiday_summary.pending_approval
    Decimal('24')
    >>> holiday_summary.available
    Decimal('156')

    >>> other_summary = summary_by_type[other.id]
    >>> other_summary.type.name
    u'Other'
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
    >>> summary_by_type[holidays.id].available
    Decimal('36')

Ask for more leaves than available::

    >>> unavailable_leave = Leave()
    >>> unavailable_leave.employee = employee
    >>> unavailable_leave.period = period
    >>> unavailable_leave.type = holidays
    >>> unavailable_leave.start = datetime.date(2015, 8, 1)
    >>> unavailable_leave.end = datetime.date(2015, 8, 5)
    >>> unavailable_leave.hours = Decimal(40)
    >>> unavailable_leave.save()
    >>> unavailable_leave.click('approve')
    Traceback (most recent call last):
        ...
    UserWarning: ('UserWarning', ('leave_exceds_5', u'The leave "Holidays, 08/01/2015, 40" exceeds the available hours (36h) for employee "Employee" and entitlement type "Holidays" on period "2015".', ''))

