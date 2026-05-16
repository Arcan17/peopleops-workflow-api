import django_filters
from .models import Employee, EmployeeStatus, ContractType


class EmployeeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=EmployeeStatus.choices)
    contract_type = django_filters.ChoiceFilter(choices=ContractType.choices)
    department = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Employee
        fields = ["status", "contract_type", "department"]
