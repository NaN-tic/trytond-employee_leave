from trytond.model import fields
from trytond.pool import PoolMeta


class Employee(metaclass=PoolMeta):
    __name__ = 'company.employee'
    leave_color = fields.Char('Leave Color')
