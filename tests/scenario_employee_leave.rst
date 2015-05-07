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
    >>> today = datetime.date.today()

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

Create leave period::

    >>> Period = Model.get('employee.leave.period')
    >>> period = Period(name='%s' % today.year)
    >>> period.start = today + relativedelta(month=1, day=1)
    >>> period.end = today + relativedelta(month=12, day=31)
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

    >>> Leave = Model.get('employee.leave')
    >>> leave = Leave()
    >>> leave.employee = employee
    >>> leave.period = period
    >>> leave.type = holidays
    >>> leave.hours = Decimal(24)
    >>> leave.date = today
    >>> leave.start = today
    >>> leave.end = today + relativedelta(days=3)
    >>> leave.save()
    >>> leave = Leave()
    >>> leave.employee = employee
    >>> leave.period = period
    >>> leave.type = holidays
    >>> leave.hours = Decimal(16)
    >>> leave.date = today
    >>> leave.start = today
    >>> leave.end = today + relativedelta(days=2)
    >>> leave.state = 'approved'
    >>> leave.save()
    >>> leave = Leave()
    >>> leave.employee = employee
    >>> leave.period = period
    >>> leave.type = holidays
    >>> leave.date = today
    >>> leave.start = today
    >>> leave.end = today + relativedelta(days=1)
    >>> leave.hours = Decimal(8)
    >>> leave.state = 'done'
    >>> leave.save()

Check summary::

    >>> Summary = Model.get('employee.leave.summary')
    >>> holiday_summary, other_summary = Summary.find([])
    >>> holiday_summary.employee.rec_name
    u'Employee'
    >>> holiday_summary.type.name
    u'Holidays'
    >>> holiday_summary.hours == Decimal('184')
    True
    >>> holiday_summary.paid == Decimal('4')
    True
    >>> holiday_summary.done == Decimal('8')
    True
    >>> holiday_summary.scheduled == Decimal('16')
    True
    >>> holiday_summary.pending_approval == Decimal('24')
    True
    >>> holiday_summary.available == Decimal('156')
    True
    >>> other_summary.employee.rec_name
    u'Employee'
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
