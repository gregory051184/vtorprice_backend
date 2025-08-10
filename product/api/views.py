import http
import json

import phonenumbers
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from pydantic import ValidationError
from rest_framework import filters, generics, viewsets
from django.db import models
from rest_framework.permissions import AllowAny

from rest_framework.decorators import action
from common.views import BaseQuerySetMixin
from company.models import Company, City, Region
from company.services.company_data.get_data import get_companies
from exchange.models import RecyclablesApplication, DealType
from product.api.serializers import (
    RecyclablesSerializer,
    RecyclablesCategorySerializer,
    EquipmentCategorySerializer,
    EquipmentSerializer, CreateEquipmentSerializer, TwoLastSupplyContractsList,
)
from product.models import (
    Recyclables,
    RecyclablesCategory,
    EquipmentCategory,
    Equipment,
    RecyclingCode,
)

from exchange.utils import (
    validate_period,
    get_truncation_class,
    get_lower_date_bound,
)

from rest_framework.response import Response

from user.models import User


class RecyclablesCategoryViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = RecyclablesCategory.objects.root_nodes().prefetch_related(
        "recyclables"
    )
    serializer_class = RecyclablesCategorySerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"

    @action(methods=["GET"], detail=False)
    def two_last_supply_contracts_prices(self, request, *args, **kwargs):
        query = self.get_queryset()
        serializer = TwoLastSupplyContractsList(query, many=True)
        return Response(serializer.data)


class RecyclablesFilterSet(FilterSet):
    class Meta:
        model = Recyclables
        fields = {
            "category": ["exact"],
            "category__parent": ["exact"],
            "applications__city": ["exact"],
            "applications__urgency_type": ["exact"],
        }


# ДОБАВИЛ
class ApplicationsRecyclablesFilterSet(FilterSet):
    class Meta:
        model = Recyclables
        fields = {
            "category": ["exact"],
            "category__parent": ["exact"],
            "applications__city": ["exact"],
            "applications__urgency_type": ["exact"]
        }


class RecyclablesViewSet(viewsets.ModelViewSet):
    queryset = Recyclables.objects.all()
    serializer_class = RecyclablesSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"
    pagination_class = None

    # filterset_class = RecyclablesFilterSet

    @property
    def filterset_class(self):
        if self.action == "generate_offers":
            return RecyclablesFilterSet
        return RecyclablesFilterSet

    def get_queryset(self):
        if self.action == "generate_offers":
            # return Recyclables.objects.recyclables_generate_offers()
            return Recyclables.objects.recyclables_app_generate_offers()
        return self.queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if self.filterset_class:
            return self.filterset_class(self.request.GET, queryset=queryset).qs
        return queryset

    @action(methods=["get"], detail=False)
    def generate_offers(self, request):
        recyclables = self.filter_queryset(self.get_queryset())

        recyclables_for_buying = recyclables.filter(applications__deal_type=DealType.BUY)

        period = validate_period(request.query_params.get("period", "all"))
        serializer_context = self.get_serializer_context()
        serializer_context["lower_date_bound"] = get_lower_date_bound(period)

        category = request.query_params.get("category")
        serializer_context["category"] = category
        serializer = RecyclablesSerializer(recyclables, many=True, context=serializer_context)

        response = []
        # Добавил
        for i in range(len(recyclables)):
            serializer.data[i]['buyer'] = False
            for j in range(len(recyclables_for_buying)):
                if recyclables[i].id == recyclables_for_buying[j].id:
                    serializer.data[i]['buyer'] = True
        # ______________________________________________
        for i in range(len(serializer.data)):
            # serializer.data[i]['companies_count'] = int(recyclables[i].companies_count)
            serializer.data[i]['companies_buy_app_count'] = int(recyclables[i].companies_buy_app_count)
            # if int(recyclables[i].companies_buy_app_count) > 0:
            #    serializer.data[i]['companies_buy_app_count'] = int(recyclables[i].companies_buy_app_count) - 1
            # else:
            #    serializer.data[i]['companies_buy_app_count'] = 0
            response.append(serializer.data[i])
        return Response(response)


class EquipmentCategoryViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = EquipmentCategory.objects.root_nodes().prefetch_related(
        "equipments"
    )
    serializer_class = EquipmentCategorySerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"

    @action(methods=["GET"], detail=False)
    def find_companies_by_phone(self, request):
        lst = []
        phones = list(set(lst))
        exist_companies = []
        for phone in phones:
            company = Company.objects.filter(phone=phone)
            if len(company) > 0:
                exist_companies.append(f'ИНН {company[0].inn} - {company[0].phone}')
        print(f'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF - {len(phones)}')
        return Response(status=http.HTTPStatus.NO_CONTENT)

    @action(methods=["GET"], detail=False)
    def post_companies_to_db(self, request):
        companies = []
        users_count = 0
        companies_count = 0
        with open('product/api/data.json', 'r', encoding='utf-8') as file:
            formated_file = json.load(file)
            errors = []
            for i in formated_file:
                try:
                    query = get_companies(i["inn"])
                except ValidationError:
                    errors.append(f'{i["name"]} - {i["inn"]}')
                company = Company.objects.filter(inn=i["inn"])
                if not len(company) > 0:
                    phone = phonenumbers.format_number(phonenumbers.parse(i['phone'], "RU"),
                                                       phonenumbers.PhoneNumberFormat.NATIONAL).replace("(",
                                                                                                        "").replace(
                        ")", "").replace("-", "").replace(" ", "")
                    contact_name = i['contact_person'].lower().title() if i['contact_person'] != 'нет имени' else \
                        i['contact_person']

                    if phone and len(phone) == 11 and len(query) > 0:
                        region_name = query[0].address.split(',')[1]
                        current_region = Region.objects.get_or_create(name=region_name)
                        city = City.objects.get(id=query[0].city.id)
                        city.region = current_region[0]
                        user = User.objects.get(id=int(i['manager']))
                        current_company = Company.objects.create(
                            name=query[0].name,
                            inn=i['inn'],
                            email=i['email'],
                            phone=phone,  # if hasattr(i, 'phone') else "",
                            head_full_name=i['head_full_name'].lower().title(),
                            latitude=query[0].latitude,
                            longitude=query[0].longitude,
                            address=query[0].address,
                            city=query[0].city,
                            # with_nds=True if i['with_nds'] == 1 else False,
                            # description=i['description'],
                            bank_name=i['bank_name'],
                            bic=i['bic'],
                            correction_account=i['correction_account'],
                            payment_account=i['payment_account'],
                            manager=user
                        )
                        current_company.save()
                        companies_count += 1
                        if contact_name != 'нет имени':  # len(
                            # i['contact_person'].split(" ")[0]) > 0 and len(i['contact_person'].split(" ")[1]) > 0:
                            owner = User.objects.create_user(
                                phone=phone,  # '+7' + i['phone'][1:],
                                first_name=contact_name.split(" ")[0],
                                last_name=contact_name.split(" ")[2] if len(contact_name.split(" ")) > 3 else "",
                                middle_name=contact_name.split(" ")[1] if len(contact_name.split(" ")) > 2 else "",
                                company=current_company,
                                role=5
                            )
                            owner.save()
                            current_company.owner = owner
                            current_company.save()
                        else:
                            owner = User.objects.create_user(
                                phone=phone,
                                first_name='нет имени',
                                last_name='нет фамилии',
                                middle_name='нет отчества',
                                company=current_company,
                                role=5
                            )
                            owner.save()
                            current_company.owner = owner
                            current_company.save()
                            users_count += 1
                        if company:
                            companies.append(company.inn)

        print(f'COMPANIES_CREATED_INN - {companies}')
        print(f'USERS_CREATED - {users_count}')
        print(f'COMPANIES_CREATED - {companies_count}')
        print(f'COMPANIES_FAILED -{errors}')
        return Response(status=http.HTTPStatus.NO_CONTENT)

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    # _______________________________________________________________
    # companies = []
    # users_count = 0
    # companies_count = 0
    # with open('product/api/data.json', 'r', encoding='utf-8') as file:
    #     formated_file = json.load(file)
    #     errors = []
    #     for i in formated_file:
    #         try:
    #             query = get_companies(i["inn"])  # i["inn"])
    #         except ValidationError:
    #             errors.append(f'{i["name"]} - {i["inn"]}')
    #         company = Company.objects.filter(inn=i["inn"])
    #         if not len(company) > 0:
    #             phone = phonenumbers.format_number(phonenumbers.parse(i['phone'], "RU"),
    #                                                phonenumbers.PhoneNumberFormat.NATIONAL).replace("(",
    #                                                                                                 "").replace(
    #                 ")", "").replace("-", "").replace(" ", "")
    #             contact_name = i['contact_person'].lower().title() if i['contact_person'] != 'нет имени' else \
    #                 i['contact_person']
    #
    #             if phone and len(phone) == 11:
    #                 region_name = query[0].address.split(',')[1]
    #                 current_region = Region.objects.get_or_create(name=region_name)
    #                 city = City.objects.get(id=query[0].city.id)
    #                 city.region = current_region[0]
    #                 user = User.objects.get(id=int(i['manager']))
    #                 current_company = Company.objects.create(
    #                     name=query[0].name,
    #                     inn=i['inn'],
    #                     email=i['email'],
    #                     phone=phone,  # if hasattr(i, 'phone') else "",
    #                     head_full_name=i['head_full_name'].lower().title(),
    #                     latitude=query[0].latitude,
    #                     longitude=query[0].longitude,
    #                     address=query[0].address,
    #                     city=query[0].city,
    #                     #with_nds=True if i['with_nds'] == 1 else False,
    #                     #description=i['description'],
    #                     bank_name=i['bank_name'],
    #                     bic=i['bic'],
    #                     correction_account=i['correction_account'],
    #                     payment_account=i['payment_account'],
    #                     manager=user
    #                 )
    #                 current_company.save()
    #                 companies_count += 1
    #                 if contact_name != 'нет имени':  # len(
    #                     # i['contact_person'].split(" ")[0]) > 0 and len(i['contact_person'].split(" ")[1]) > 0:
    #                     owner = User.objects.create_user(
    #                         phone=phone,  # '+7' + i['phone'][1:],
    #                         first_name=contact_name.split(" ")[0],
    #                         last_name=contact_name.split(" ")[2] if len(
    #                             contact_name.split(" ")) > 2 else "",
    #                         middle_name=contact_name.split(" ")[1] if len(
    #                             contact_name.split(" ")) > 1 else "",
    #                         company=current_company,
    #                         role=5
    #                     )
    #                     owner.save()
    #                     current_company.owner = owner
    #                     current_company.save()
    #                 else:
    #                     owner = User.objects.create_user(
    #                         phone=phone,
    #                         first_name='нет имени',
    #                         last_name='нет фамилии',
    #                         middle_name='нет отчества',
    #                         company=current_company,
    #                         role=5
    #                     )
    #                     owner.save()
    #                     current_company.owner = owner
    #                     current_company.save()
    #                     users_count += 1
    #                 if company:
    #                     companies.append(company.inn)
    #
    # print(f'COMPANIES_CREATED_INN - {companies}')
    # print(f'USERS_CREATED - {users_count}')
    # print(f'COMPANIES_CREATED - {companies_count}')
    # print(f'COMPANIES_FAILED -{errors}')
    # ____________________________________________________
    #
    #     return self.get_paginated_response(serializer.data)
    #
    # serializer = self.get_serializer(queryset, many=True)
    # return Response(serializer.data)

    @action(methods=["POST"], detail=False)
    def equipment(self, request):
        serializer = CreateEquipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"


class RecyclingCodeViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = RecyclingCode.objects.all()
    # serializer_class = RecyclingCodeSerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name", "gost_name")
    ordering_fields = "__all__"
