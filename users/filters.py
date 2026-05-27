import django_filters
from .models import UserProfile

class UserProfileFilter(django_filters.FilterSet):
    # numeric ranges
    min_rate = django_filters.NumberFilter(field_name="hourly_rate", lookup_expr="gte")
    max_rate = django_filters.NumberFilter(field_name="hourly_rate", lookup_expr="lte")


    min_success = django_filters.NumberFilter(field_name="job_success", lookup_expr="gte")
    max_success = django_filters.NumberFilter(field_name="job_success", lookup_expr="lte")


    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")

    rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")

    # text-based
    location = django_filters.CharFilter(field_name="nationality", lookup_expr="icontains")

    # custom skills filter
    skills = django_filters.CharFilter(method='filter_by_skills')

    category = django_filters.CharFilter(method='filter_by_categories')

    def filter_by_categories(self, queryset, name, value):
        categories_list = [cat.strip() for cat in value.split(",")]
        return queryset.filter(category__slug__in=categories_list)

    def filter_by_skills(self, queryset, name, value):
        skills_list = [skill.strip() for skill in value.split(",")]
        for skill in skills_list:
            queryset = queryset.filter(skills__name__iexact=skill)
        return queryset.distinct()

    class Meta:
        model = UserProfile
        fields = ["location", "category", "min_rate", "max_rate", 
                  "min_success", "max_success", "min_rating", "skills"]

from rest_framework.filters import SearchFilter

class MultiTermSearchFilter(SearchFilter):
    def get_search_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        print("SEARCH PARAMS: ",params)
        return [term.strip() for term in params.split(',') if term.strip()]
