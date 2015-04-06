from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from sql.aggregate import Sum
from sql import Column, Literal
from decimal import Decimal

__all__ = ['LeaveType', 'Leave', 'LeavePeriod', 'Entitlement', 'LeavePayment',
    'Employee', 'LeaveSummary']
__metaclass__ = PoolMeta


class LeaveType(ModelSQL, ModelView):
    'Employee Leave Type'
    __name__ = 'employee.leave.type'
    name = fields.Char('Name', required=True)


class LeavePeriod(ModelSQL, ModelView):
    'Employee Leave Period'
    __name__ = 'employee.leave.period'
    name = fields.Char('Name', required=True)
    start = fields.Date('Start', required=True)
    end = fields.Date('End', required=True)


class Leave(ModelSQL, ModelView, Workflow):
    'Employee Leave'
    __name__ = 'employee.leave'

    employee = fields.Many2One('company.employee', 'Employee', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    date = fields.Date('Date', required=True)
    hours = fields.Numeric('Hours', required=True)
    start = fields.Date('Start', required=True)
    end = fields.Date('End', required=True)
    comment = fields.Text('Comment')
    state = fields.Selection([
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
            ('done', 'Done'),
            ], 'State', required=True)

    # TODO: Missing workflow

    # TODO: When the user is trying to approve a leave, the system should warn
    # the user if the employee exceeds it's entitlements for this leave type
    # on the current period.

    @staticmethod
    def default_state():
        return 'pending'

    @staticmethod
    def get_leave_hours(employee, type_, start, end):
        # Search on 'employee.leave' and find the number of hours that fit
        # inside this payslip
        Leave = Pool().get('employee.leave')
        domain = [
            ('state', '=', 'done'),
            ('start', '<=', end),
            ('end', '>=', start),
            ]
        if employee:
            domain.append(('employee', '=', employee.id))
        if type_:
            domain.append(('type', '=', type_.id))
        leaves = Leave.search(domain)
        count = Decimal('0.0')
        for leave in leaves:
            days = (leave.end - leave.start).days + 1
            hours_per_day  = leave.hours / Decimal(days)
            s = max(leave.start, start)
            e = min(leave.end, end)
            days = (e - s).days + 1
            count += hours_per_day * days
        return count

class Entitlement(ModelSQL, ModelView):
    'Employee Entitlement'
    __name__ = 'employee.leave.entitlement'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    hours = fields.Numeric('Hours', required=True)
    date = fields.Date('Date')
    comment = fields.Text('Comment')


class LeavePayment(ModelSQL, ModelView):
    'Employee Leave Payment'
    __name__ = 'employee.leave.payment'
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('employee.leave.type', 'Type', required=True)
    period = fields.Many2One('employee.leave.period', 'Period', required=True)
    hours = fields.Numeric('Hours', required=True)
    date = fields.Date('Date', required=True)
    comment = fields.Text('Comment')
    # TODO: Link to supplier invoice or account move


class Employee:
    __name__ = 'company.employee'
    # This is to report current situation of available leaves on the employee
    # form
    leave_status = fields.One2Many('employee.leave.summary',
        'employee', 'Leave Summary')


# It should be possible to have several Entitlements per employee & type &
# period. This way, entitlements can be used when the user is rewarded with more
# holidays instead of paying them more when working more hours.
class LeaveSummary(ModelSQL, ModelView):
    'Employee Leave Summary'
    __name__ = 'employee.leave.summary'
    employee = fields.Many2One('company.employee', 'Employee')
    type = fields.Many2One('employee.leave.type', 'Type')
    period = fields.Many2One('employee.leave.period', 'Period')
    hours = fields.Numeric('Hours')
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

        query = table.select(
            (employee.id * 100000 + period.id * 1000 + type_.id).as_('id'),
            employee.create_uid.as_('create_uid'),
            employee.write_uid.as_('write_uid'),
            employee.create_date.as_('create_date'),
            employee.write_date.as_('write_date'),
            employee.id.as_('employee'),
            type_.id.as_('type'),
            period.id.as_('period'),
            entitlements.hours.as_('hours'),
            fields['pending_approval'].as_('pending_approval'),
            fields['scheduled'].as_('scheduled'),
            fields['done'].as_('done'),
            payments.hours.as_('paid'),
            )
        return query
