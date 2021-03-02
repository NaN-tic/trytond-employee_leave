# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond import backend
from trytond.model import ModelSingleton, ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)

__all__ = ['Configuration', 'ConfigurationStateColor']

def get_leave_states(field_name):
    @classmethod
    def func(cls):
        pool = Pool()
        Leave = pool.get('employee.leave')
        return Leave.fields_get([field_name])[field_name]['selection']
    return func


class Configuration(
        ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
    'Leave Configuration'
    __name__ = 'employee.leave.configuration'
    colors = fields.One2Many('employee.leave.configuration.state.color',
        'configuration', 'State Colors')


class ConfigurationStateColor(ModelSQL, ModelView):
    'Leave Configuration State Color'
    __name__ = 'employee.leave.configuration.state.color'
    configuration = fields.Many2One('employee.leave.configuration',
        'Configuration', required=True)
    get_leave_states = get_leave_states('state')
    state = fields.Selection('get_leave_states', 'State', required=True)
    color = fields.Char('Color', required=True, help='HTML color (hexadecimal)')
