from rest_framework.pagination import PageNumberPagination


class DefaultPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size' # allow frontend to override (e.g., 12, 24, 48)
    max_page_size = 100
