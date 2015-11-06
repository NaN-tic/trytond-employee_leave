# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.aggregate import Max, Sum
from sql import Column
from decimal import Decimal

from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Id
from trytond.transaction import Transaction

__all__ = ['Type', 'Period', 'Leave', 'Entitlement', 'Payment',
    'Employee', 'EmployeeSummary']
__metaclass__ = PoolMeta


class Type(ModelSQL, ModelView):
    'Employee Leave Type'
    __name__ = 'employee.leave.type'
    name = fields.Char('Name', required=True)


class Period(ModelSQL, ModelView):
    'Employee Leave Period'
    __name__ = 'employee.leave.period'
    name = fields.Char('Name', required=True)
    start = fields.Date('Start', required=True)
    end = fields.Date('End', required=True, domain=[
            ('end', '>=', Eval('start')),
            ], depends=['start'])

_STATES = {
    'readonly': Eval('state') != 'pending',
    }
_DEPENDS = ['state']


class Leave(Workflow, ModelSQL, ModelView):
    'Employee Leave'
    __name__ = 'employee.leave'
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        states=_STATES, depends=_DEPENDS)
    period = fields.Many2One('employee.leave.period', 'Period', required=True,
        states=_STATES, depends=_DEPENDS)
    type = fields.Many2One('employee.leave.type', 'Type', required=True,
        states=_STATES, depends=_DEPENDS)
    request_date = fields.Date('Request Date', required=True, states=_STATES,
        depends=_DEPENDS)
    start = fields.Date('Start', required=True, states=_STATES,
        depends=_DEPENDS)
    end = fields.Date('End', required=True, domain=[
            ('end', '>=', Eval('start')),
            ], states=_STATES, depends=_DEPENDS + ['start'])
    hours = fields.Numeric('Hours', required=True, states=_STATES,
        depends=_DEPENDS)
    comment = fields.Text('Comment', states=_STATES, depends=_DEPENDS)
    state = fields.Selection([
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
            ('done', 'Done'),
            ], 'State', required=True, readonly=True)

    @classmethod
    def __setup__(cls):
        super(Leave, cls).__setup__()
        cls._error_messages.update({
                'exceeds_entitelments': (
                    'The leave "%(leave)s" exceeds the available hours '
                    '(%(hours)sh) for employee "%(employee)s" and entitlement '
                    'type "%(type)s" on period "%(period)s".')
                })
        cls._transitions |= set((
                ('pending', 'approved'),
                ('pending', 'cancelled'),
                ('pending', 'rejected'),
                ('approved', 'done'),
                ('approved', 'rejected'),
                ('approved', 'cancelled'),
                ('rejected', 'cancelled'),
                ('cancelled', 'pending'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state').in_(['cancelled', 'done']),
                    'icon': 'tryton-cancel',
                    },
                'pending': {
                    'invisible': Eval('state') != 'cancelled',
                    'icon': 'tryton-clear',
                    },
                'approve': {
                    'invisible': Eval('state') != 'pending',
                    'icon': 'tryton-go-next',
                    'readonly': ~Eval('groups', []).contains(
                        Id('employee_leave', 'group_employee_leave_admin')),
                    },
                'reject': {
                    'invisible': ~Eval('state').in_(['pending', 'approved']),
                    'icon': 'tryton-undo',
                    'readonly': ~Eval('groups', []).contains(
                        Id('employee_leave', 'group_employee_leave_admin')),
                    },
                'done': {
                    'invisible': Eval('state') != 'approved',
                    'icon': 'tryton-ok',
                    },
                })

    def get_rec_name(self, name):
        pool = Pool()
        User = pool.get('res.user')

        user = User(Transaction().user)
        if user.language and user.language.date:
            start_str = self.start.strftime(user.language.date)
        else:
            start_str = self.start.strftime('%Y-%m-%d')
        return '%s, %s, %s' % (self.type.rec_name, start_str, self.hours)

    @staticmethod
    def default_employee():
        pool = Pool()
        User = pool.get('res.user')

        if Transaction().context.get('employee'):
            return Transaction().context['employee']
        else:
            user = User(Transaction().user)
            if user.employee:
                return user.employee.id

    @staticmethod
    def default_request_date():
        pool = Pool()
        Date = pool.get('ir.date')
        return Date.today()

    @staticmethod
    def default_state():
        return 'pending'

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, leaves):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('pending')
    def pending(cls, leaves):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('approved')
    def approve(cls, leaves):
        for leave in leaves:
            leave.check_entitlements()

    def check_entitlements(self):
        '''
        Checks that the hours does not exceed the current available hours for
        this leave type.
        '''
        pool = Pool()
        EmployeeSummary = pool.get('employee.leave.summary')
        summaries = EmployeeSummary.search([
                ('employee', '=', self.employee.id),
                ('type', '=', self.type.id),
                ('period', '=', self.period.id),
                ])
        if not summaries:
            return
        if self.hours > summaries[0].available:
            self.raise_user_warning('leave_exceds_%d' % self.id,
                'exceeds_entitelments', {
                    'leave': self.rec_name,
                    'hours': summaries[0].available,
                    'employee': self.employee.rec_name,
                    'type': self.type.rec_name,
                    'period': self.period.rec_name,
                    })

    @classmethod
    @ModelView.button
    @Workflow.transition('rejected')
    def reject(cls, leaves):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, leaves):
        pass

    @classmethod
    def get_leaves(cls, employee, period_start, period_end, type_=None,
            states=None):
        domain = [
            ('employee', '=', employee.id),
            ('start', '<=', period_end),
            ('end', '>=', period_start),
            ]
        if type_:
            domain.append(('type', '=', type_.id))
        if states is not None:
            domain.append(('state', 'in', states))
        else:
            domain.append(('state', '=', 'done'))
        return cls.search(domain)

    @classmethod
    def get_leave_hours(cls, employee, period_start, period_end, type_=None,
            states=None):
        'Finds the number of hours that fit inside a period'
        count = Decimal('0.0')
        for leave in cls.get_leaves(employee, period_start, period_end,
                type_=type_, states=states):
            count += leave.compute_leave_hours(period_start, period_end)
        return count

    def compute_leave_hours(self, period_start, period_end):
        'Computes leave hours for a leave in a period'
        days = (self.end - self.start).days + 1
        hours_per_day = self.hours / Decimal(days)
        s = max(self.start, period_start)
        e = min(self.end, period_end)
        days = (e - s).days + 1
        return hours_per_day * days


class Entitlement(ModelSQL, ModelView):
    'Employee Leave Entitlement'
    __name__ = 'employee.leave.entitlement'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    hours = fields.Numeric('Hours', required=True)
    date = fields.Date('Date',
        help="The date when this entitlement has been deserved.")
    comment = fields.Text('Comment')


class Payment(ModelSQL, ModelView):
    'Employee Leave Payment'
    __name__ = 'employee.leave.payment'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    hours = fields.Numeric('Hours', required=True)
    date = fields.Date('Date', required=True,
        help="The date this payment is granted.")
    comment = fields.Text('Comment')
    # TODO: Link to supplier invoice or account move


class Employee:
    __name__ = 'company.employee'
    # This is to report current situation of available leaves on the employee
    # form
    leave_summary = fields.One2Many('employee.leave.summary',
        'employee', 'Leave Summary')


# It should be possible to have several Entitlements per employee & type &
# period. This way, entitlements can be used when the user is rewarded with
# more holidays instead of paying them more when working more hours.
class EmployeeSummary(ModelSQL, ModelView):
    'Employee Leave Summary'
    __name__ = 'employee.leave.summary'
    employee = fields.Many2One('company.employee', 'Employee')
    type = fields.Many2One('employee.leave.type', 'Type')
    period = fields.Many2One('employee.leave.period', 'Period')
    hours = fields.Numeric('Hours', digits=(16, 2))
    pending_approval = fields.Numeric('Pending Approval')
    scheduled = fields.Numeric('Scheduled')
    done = fields.Numeric('Done')
    paid = fields.Numeric('Paid')
    available = fields.Function(fields.Numeric('Available'), 'get_available')

    def get_available(self, name):
        if self.hours is None:
            return
        return ((self.hours or Decimal('0.0'))
            - (self.scheduled or Decimal('0.0'))
            - (self.done or Decimal('0.0'))
            - (self.paid or Decimal('0.0')))

    @classmethod
    def table_query(cls):
        # To calculate these amounts it should be done like:
        # days = entitlements - leaves - leave payments
        pool = Pool()
        Type = pool.get('employee.leave.type')
        Leave = pool.get('employee.leave')
        LeavePayment = pool.get('employee.leave.payment')
        LeavePeriod = pool.get('employee.leave.period')
        Entitlement = pool.get('employee.leave.entitlement')
        Employee = pool.get('company.employee')

        leave = Leave.__table__()
        payment = LeavePayment.__table__()
        period = LeavePeriod.__table__()
        type_ = Type.__table__()
        entitlement = Entitlement.__table__()
        employee = Employee.__table__()

        # Had to add stupid conditions as otherwise the query fails
        table = employee.join(type_, condition=(type_.id >= 0)).join(period,
            condition=(period.id >= 0))
        entitlements = entitlement.select(
            entitlement.employee,
            entitlement.period,
            entitlement.type,
            Sum(entitlement.hours).as_('hours'),
            group_by=(
                entitlement.employee, entitlement.period, entitlement.type
                ))
        table = table.join(entitlements, 'LEFT', condition=(
                (entitlements.employee == employee.id)
                & (entitlements.period == period.id)
                & (entitlements.type == type_.id)
                ))

        fields = {}
        for field_name, state in (
                ('pending_approval', 'pending'),
                ('scheduled', 'approved'),
                ('done', 'done')
                ):
            leaves = leave.select(
                leave.employee,
                leave.period,
                leave.type,
                Sum(leave.hours).as_('hours'),
                where=(
                    leave.state == state
                    ),
                group_by=(
                    leave.employee, leave.period, leave.type
                    ))
            table = table.join(leaves, 'LEFT', condition=(
                    (leaves.employee == employee.id)
                    & (leaves.period == period.id)
                    & (leaves.type == type_.id)
                    ))
            fields[field_name] = Column(leaves, 'hours')

        payments = payment.select(
            payment.employee,
            payment.period,
            payment.type,
            Sum(payment.hours).as_('hours'),
            group_by=(
                payment.employee, payment.period, payment.type
                ))
        table = table.join(payments, 'LEFT', condition=(
                (payments.employee == employee.id)
                & (payments.period == period.id)
                & (payments.type == type_.id)
                ))

        cursor = Transaction().cursor
        cursor.execute(*type_.select(Max(type_.id)))
        max_type_id = cursor.fetchone()
        if max_type_id and max_type_id[0]:
            period_id_padding = 10 ** len(str(max_type_id[0]))
        else:
            period_id_padding = 10

        cursor.execute(*period.select(Max(period.id)))
        max_period_id = cursor.fetchone()
        if max_period_id and max_period_id[0]:
            employee_id_padding = period_id_padding * (
                10 ** len(str(max_period_id[0])))
        else:
            employee_id_padding = period_id_padding * 10

        query = table.select(
            (employee.id * employee_id_padding
                + period.id * period_id_padding
                + type_.id).as_('id'),
            employee.create_uid.as_('create_uid'),
            employee.write_uid.as_('write_uid'),
            employee.create_date.as_('create_date'),
            employee.write_date.as_('write_date'),
            employee.id.as_('employee'),
            type_.id.as_('type'),
            period.id.as_('period'),
            entitlements.hours.cast(cls.hours.sql_type().base).as_('hours'),
            fields['pending_approval'].cast(
                cls.pending_approval.sql_type().base).as_('pending_approval'),
            fields['scheduled'].cast(
                cls.scheduled.sql_type().base).as_('scheduled'),
            fields['done'].cast(cls.done.sql_type().base).as_('done'),
            payments.hours.cast(cls.paid.sql_type().base).as_('paid'),
            )
        return query
