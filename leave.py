# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.aggregate import Max, Sum
from sql import Column
from decimal import Decimal

from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserWarning


__all__ = ['Type', 'Period', 'Leave', 'Entitlement', 'Payment',
    'Employee', 'EmployeeSummary', 'LeaveCalendarContext']

# Use Tryton's default color by default
_COLOR = '#ABD6E3'
_RGB = (67, 84, 90)


class RGB:
    def __init__(self, color=(0, 0, 0)):
        if isinstance(color, str):
            color = color.lstrip('#')
            try:
                self.value = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            except ValueError:
                self.value = _RGB
        else:
            self.value = color
        assert isinstance(self.value, tuple)
        assert len(self.value) == 3

    def hex(self):
        return '#%02x%02x%02x' % self.value

    def increase(self, inc):
        res = []
        for x in self.value:
            res.append(max(0, min(255, x + inc)))
        self.value = tuple(res)

    def increase_ratio(self, ratio):
        self.increase(int((255 - self.gray()) * ratio))

    def gray(self):
        return (self.value[0] + self.value[1] + self.value[2]) // 3


class Type(ModelSQL, ModelView):
    'Employee Leave Type'
    __name__ = 'employee.leave.type'
    name = fields.Char('Name', required=True)
    allow_right = fields.Boolean('Allow Right')

    @staticmethod
    def default_allow_right():
        return True


class Period(ModelSQL, ModelView):
    'Employee Leave Period'
    __name__ = 'employee.leave.period'
    name = fields.Char('Name', required=True)
    start = fields.Date('Start', required=True)
    end = fields.Date('End', required=True, domain=[
            ('end', '>=', Eval('start')),
            ])


_STATES = {
    'readonly': Eval('state') != 'pending',
    }
_DEPENDS = ['state']


class Leave(Workflow, ModelSQL, ModelView):
    'Employee Leave'
    __name__ = 'employee.leave'
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        domain=[('company', '=', Eval('context', {}).get('company', -1)),],
        states=_STATES)
    period = fields.Many2One('employee.leave.period', 'Period', required=True,
        states=_STATES)
    type = fields.Many2One('employee.leave.type', 'Type', required=True,
        states=_STATES)
    request_date = fields.Date('Request Date', required=True, states=_STATES)
    start = fields.Date('Start', required=True, states=_STATES)
    end = fields.Date('End', required=True, domain=[
            ('end', '>=', Eval('start')),
            ], states=_STATES)
    hours = fields.Numeric('Hours to consume', required=True, states=_STATES)
    comment = fields.Text('Comment', states=_STATES)
    summary = fields.Function(fields.Char('Summary'), 'get_summary')
    state = fields.Selection([
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
            ('done', 'Done'),
            ], 'State', required=True, readonly=True)
    calendar_color = fields.Function(fields.Char('Color'), 'get_calendar_color')
    calendar_background_color = fields.Function(fields.Char('Background Color'),
            'get_calendar_background_color')

    @classmethod
    def __setup__(cls):
        super(Leave, cls).__setup__()
        cls._order = [
            ('start', 'DESC'),
            ('id', 'DESC'),
            ]
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
                    'icon': 'tryton-forward',
                    },
                'reject': {
                    'invisible': ~Eval('state').in_(['pending', 'approved']),
                    'icon': 'tryton-undo',
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
        Warning = pool.get('res.user.warning')
        summaries = EmployeeSummary.search([
                ('employee', '=', self.employee.id),
                ('type', '=', self.type.id),
                ('period', '=', self.period.id),
                ])
        if not summaries:
            return
        key = 'leave_exceds_%d' % self.id
        if self.hours > (summaries[0].available or Decimal(0)) and Warning.check(key):
            raise UserWarning(key,
                gettext('employee_leave.exceeds_entitelments',
                    leave=self.rec_name,
                    hours=summaries[0].available,
                    employee=self.employee.rec_name,
                    type=self.type.rec_name,
                    period=self.period.rec_name))

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
        count = Decimal(0)
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

    def get_summary(self, name):
        return ' - '.join([self.type.rec_name, self.employee.rec_name])

    def get_calendar_color(self, name):
        rgb = RGB(self.calendar_background_color)
        if rgb.gray() > 128:
            return 'black'
        return 'white'

    def get_calendar_background_color(self, name):
        Config = Pool().get('employee.leave.configuration')

        config = Config(1)
        colors = dict((c.state, c.color) for c in config.colors)

        color = _COLOR
        context = Transaction().context
        if context.get('leave_color_type', False):
            color = colors.get(self.state, _COLOR)
        else:
            if self.employee and self.employee.leave_color:
                color = self.employee.leave_color

        rgb = RGB(color)
        rgb.increase_ratio(0.8)
        color = rgb.hex()
        return color


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


class Employee(metaclass=PoolMeta):
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
        return ((self.hours or Decimal(0))
            - (self.scheduled or Decimal(0))
            - (self.done or Decimal(0))
            - (self.paid or Decimal(0)))

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
        leave_type = Type.__table__()

        leave_types = leave_type.select(leave_type.id,
            where=leave_type.allow_right == True)

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
                & (entitlements.type.in_(leave_types))
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
                    (leave.state == state) & leave.type.in_(leave_types)
                    ),
                group_by=(
                    leave.employee, leave.period, leave.type
                    ))
            table = table.join(leaves, 'LEFT', condition=(
                    (leaves.employee == employee.id)
                    & (leaves.period == period.id)
                    & (leaves.type == type_.id)
                    & (leaves.type.in_(leave_types))
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

        cursor = Transaction().connection.cursor()
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
            where=(type_.id.in_(leave_types)))
        return query


class LeaveCalendarContext(ModelView):
    'Leave Calendar Context'
    __name__ = 'employee.leave.calendar.context'
    leave_color_type = fields.Boolean('Use Leave Color', help='If checked, '
        'uses the color of the state of the leave as event background.')

    @staticmethod
    def default_leave_color_type():
        return True
