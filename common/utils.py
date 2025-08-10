import json
import sys

from _decimal import Decimal

from django.conf import settings
from django.http import HttpRequest
from django.template import RequestContext
from rest_framework.settings import api_settings


def str2bool(v: str) -> bool:
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "0"):
        return False
    raise ValueError("Unexpected boolean string")


def print_sql(sql, ret=False):
    """Print formatted sql (for debug)"""
    try:
        import sqlparse
    except ImportError:
        sqlparse = None

    try:
        import pygments.formatters
        import pygments.lexers
    except ImportError:
        pygments = None

    raw_sql = str(sql)

    if sqlparse:
        raw_sql = sqlparse.format(
            raw_sql, reindent_aligned=True, truncate_strings=500
        )

    if pygments:
        raw_sql = pygments.highlight(
            raw_sql,
            pygments.lexers.get_lexer_by_name("sql"),
            pygments.formatters.TerminalFormatter(),
        )

    if not ret:
        print(raw_sql)
        return True

    return raw_sql


"""
Current request
"""


def get_current_request():
    """
    Get the current request using introspection.

    Be careful when getting request.user because you can get a recursion
    if this code will be used in User manager. You need override ModelBackend.get_user:
        def get_user(self, user_id):
            user = UserModel.custom_manager.get(pk=user_id)

    custom_manager - manager without calling get_current_request()
    """
    request = None
    frame = sys._getframe(1)  # sys._getframe(0).f_back

    while frame:
        # check the instance of each funtion argument
        for arg in frame.f_code.co_varnames[: frame.f_code.co_argcount]:
            request = frame.f_locals[arg]

            if isinstance(request, HttpRequest):
                break

            # from template tag
            if isinstance(request, RequestContext):
                request = request.request
                break
        else:
            frame = frame.f_back
            continue

        break

    return request if isinstance(request, HttpRequest) else None


def get_current_user():
    """
    Get current user from request.

    Don't forget to check if you want to get an authorized user:
        if user and user.is_authenticated:
            ...
    """
    request = get_current_request()
    return getattr(request, "user", None)


def get_current_user_id():
    """Get current user id"""
    user = get_current_user()
    return user.pk if user and user.is_authenticated else None


# возвращает условий поиска в виде списка строк
def get_search_terms_from_request(request):
    """
    Search terms are set by a ?search=... query parameter,
    and may be comma and/or whitespace delimited.
    """
    search_param = api_settings.SEARCH_PARAM
    params = request.query_params.get(search_param, "")
    params = params.replace("\x00", "")  # strip null characters
    params = params.replace(",", " ")
    return params.split()


# Группирует queryset на основе какого-либо поля
def get_grouped_qs(qs, field):
    """
    Groups queryset by field

    :param qs: a queryset to be grouped
    :param field: str: grouping field
    :return: grouped dict, f.e.: {"group_1": [obj11, obj12,..], "group_2": [obj21, obj22,...]}
    """
    group_map = {}

    for obj in qs:
        f = getattr(obj, field)
        if f in group_map:
            group_map[f].append(obj)
        else:
            group_map[f] = [obj]

    return group_map


def get_nds_tax() -> int:
    return settings.NDS_VALUE


def get_nds_amount(amount):
    nds = get_nds_tax()
    divider = 100 + nds
    return amount / divider * nds


def subtract_percentage(amount, percent):
    return amount - (amount / 100 * percent)


def generate_random_sequence(length: int = 8):
    """
    Генерация последовательности заданной длины
    """
    import string, random

    characters = string.ascii_uppercase + string.digits
    pin = "".join(random.choice(characters) for i in range(length))

    return pin


def equals_in_company_and_request(company, **kwargs):
    lst = []
    if kwargs.get("name") and kwargs.get("name")[0] != company.name:
        lst.append({"name": kwargs.get("name")[0]})
    if kwargs.get("inn") and kwargs.get("inn")[0] != company.inn:
        lst.append(f'inn - {kwargs.get("inn")[0]}')
    if kwargs.get("address") and kwargs.get("address")[0] != company.address:
        lst.append(f'address - {kwargs.get("address")[0]}')
    if not company.latitude and kwargs.get("latitude"):
        lst.append(f'latitude - {kwargs.get("latitude")[0]}')
    if kwargs.get("latitude") and company.latitude and float(kwargs.get("latitude")[0]) != float(company.latitude):
        lst.append(f'latitude - {kwargs.get("latitude")[0]}')
    if not company.longitude and kwargs.get("longitude"):
        lst.append(f'longitude - {kwargs.get("longitude")[0]}')
    if kwargs.get("longitude") and company.longitude and float(kwargs.get("longitude")[0]) != float(company.longitude):
        lst.append(f'longitude - {kwargs.get("longitude")[0]}')
    if kwargs.get("description") and kwargs.get("description")[0] != company.description:
        lst.append(f'description - {kwargs.get("description")[0]}')
    if kwargs.get("with_nds") and str(kwargs.get("with_nds")[0]).lower() != str(company.with_nds).lower():
        lst.append(f'with_nds - {kwargs.get("with_nds")[0]}')
    if kwargs.get("bic") and kwargs.get("bic")[0] != company.bic:
        lst.append(f'bic - {kwargs.get("bic")[0]}')
    if kwargs.get("payment_account") and kwargs.get("payment_account")[0] != company.payment_account:
        lst.append(f'payment_account - {kwargs.get("payment_account")[0]}')
    if kwargs.get("correction_account") and kwargs.get("correction_account")[0] != company.correction_account:
        lst.append(f'correction_account - {kwargs.get("correction_account")[0]}')
    if kwargs.get("bank_name") and kwargs.get("bank_name")[0] != company.bank_name:
        lst.append(f'bank_name - {kwargs.get("bank_name")[0]}')
    if kwargs.get("head_full_name") and company.head_full_name is not None and kwargs.get("head_full_name")[
        0] != company.head_full_name:
        lst.append(f'head_full_name - {kwargs.get("head_full_name")[0]}')
    if kwargs.get("phone") and kwargs.get("phone")[0] != company.phone:
        lst.append(f'phone - {kwargs.get("phone")[0]}')
    if kwargs.get("city") and (company.city is None or int(kwargs.get("city")[0]) != int(company.city.id)):
        lst.append(f'city - {kwargs.get("city")[0]}')
    if kwargs.get("email") and kwargs.get("email")[0] != company.email:
        lst.append(f'email - {kwargs.get("email")[0]}')
    if not company.manager and kwargs.get("manager"):
        lst.append(f'manager - {kwargs.get("manager")[0]}')
    if kwargs.get("manager") and company.manager and int(kwargs.get("manager")[0]) != int(company.manager.id):
        lst.append(f'manager - {kwargs.get("manager")[0]}')
    return lst


def equals_application_and_request(application, **kwargs):
    lst = []
    if kwargs.get("is_deleted") and str(kwargs.get("is_deleted")).lower() != str(application.is_deleted).lower():
        lst.append(f'is_deleted - {kwargs.get("is_deleted")}')
    if kwargs.get("address") and kwargs.get("address") != application.address:
        lst.append(f'address - {kwargs.get("address")}')
    if kwargs.get("latitude") and str(kwargs.get("latitude")) != str(application.latitude):
        lst.append(f'latitude - {kwargs.get("latitude")}')
    if kwargs.get("longitude") and str(kwargs.get("longitude")) != str(application.longitude):
        lst.append(f'longitude - {kwargs.get("longitude")}')
    if kwargs.get("with_nds") and str(kwargs.get("with_nds")).lower() != str(application.with_nds).lower():
        lst.append(f'with_nds - {kwargs.get("with_nds")}')
    if kwargs.get("deal_type") and int(kwargs.get("deal_type")) != int(application.deal_type):
        lst.append(f'deal_type - {kwargs.get("deal_type")}')
    if kwargs.get("bale_count") and int(kwargs.get("bale_count")) != int(application.bale_count):
        lst.append(f'bale_count - {kwargs.get("bale_count")}')
    if kwargs.get("bale_weight") and int(kwargs.get("bale_weight")) != int(application.bale_weight):
        lst.append(f'bale_weight - {kwargs.get("bale_weight")}')
    if kwargs.get("volume") and int(kwargs.get("volume")) != int(application.volume):
        lst.append(f'volume - {kwargs.get("volume")}')
    if kwargs.get("price") and float(kwargs.get("price")) != float(application.price):
        lst.append(f'price - {kwargs.get("price")}')
    if kwargs.get("lot_size") and int(kwargs.get("lot_size")) != int(application.lot_size):
        lst.append(f'lot_size - {kwargs.get("lot_size")}')
    if kwargs.get("city") and int(kwargs.get("city")) != int(application.city.id):
        lst.append(f'city - {kwargs.get("city")}')
    if kwargs.get("company") and int(kwargs.get("company").id) != int(application.company.id):
        lst.append(f'company - {kwargs.get("company")}')
    if kwargs.get("recyclables") and int(kwargs.get("recyclables").id) != int(application.recyclables.id):
        lst.append(f'recyclables - {kwargs.get("recyclables")}')
    if kwargs.get("status") and int(kwargs.get("status")) != int(application.status):
        lst.append(f'status - {kwargs.get("status")}')
    if kwargs.get("moisture") and int(kwargs.get("moisture")) != int(application.moisture):
        lst.append(f'moisture - {kwargs.get("moisture")}')
    if kwargs.get("weediness") and int(kwargs.get("weediness")) != int(application.weediness):
        lst.append(f'weediness - {kwargs.get("weediness")}')
    if kwargs.get("full_weigth") and int(kwargs.get("full_weigth")) != int(application.full_weigth):
        lst.append(f'full_weigth - {kwargs.get("full_weigth")}')
    if kwargs.get("application_recyclable_status") and int(kwargs.get("application_recyclable_status")) != int(
            application.application_recyclable_status):
        lst.append(f'application_recyclable_status - {kwargs.get("application_recyclable_status")}')
    # ДЛЯ ОБОРУДОВАНИЯ
    if kwargs.get("was_in_use") and str(kwargs.get("was_in_use")).lower() != str(application.was_in_use).lower():
        lst.append(f'was_in_use - {kwargs.get("was_in_use")}')
    if kwargs.get("sale_by_parts") and str(kwargs.get("sale_by_parts")).lower() != str(
            application.sale_by_parts).lower():
        lst.append(f'sale_by_parts - {kwargs.get("sale_by_parts")}')
    if kwargs.get("equipment") and str(kwargs.get("equipment")) != str(application.equipment.id):
        lst.append(f'equipment - {kwargs.get("equipment")}')
    if kwargs.get("category") and int(kwargs.get("category")) != int(application.category.id):
        lst.append(f'category - {kwargs.get("category")}')

    if kwargs.get("manufacture_date") and str(kwargs.get("manufacture_date")).lower() != str(
            application.manufacture_date).lower():
        lst.append(f'manufacture_date - {kwargs.get("manufacture_date")}')

    return lst


def equals_deal_and_request(deal, **kwargs):
    lst = []
    if kwargs.get("is_deleted") and str(kwargs.get("is_deleted")).lower() != str(deal.is_deleted).lower():
        lst.append(f'is_deleted - {kwargs.get("is_deleted")}')
    if kwargs.get("with_nds") and str(kwargs.get("with_nds")).lower() != str(deal.with_nds).lower():
        lst.append(f'with_nds - {kwargs.get("with_nds")}')
    if kwargs.get("price") and float(kwargs.get("price")) != float(deal.price):
        lst.append(f'price - {kwargs.get("price")}')
    if kwargs.get("status") and int(kwargs.get("status")) != int(deal.status):
        lst.append(f'status - {kwargs.get("status")}')
    if kwargs.get("moisture") and int(kwargs.get("moisture")) != int(deal.moisture):
        lst.append(f'moisture - {kwargs.get("moisture")}')
    if kwargs.get("weediness") and int(kwargs.get("weediness")) != int(deal.weediness):
        lst.append(f'weediness - {kwargs.get("weediness")}')
    if kwargs.get("payment_term") and int(kwargs.get("payment_term")) != int(deal.payment_term):
        lst.append(f'payment_term - {kwargs.get("payment_term")}')
    if kwargs.get("other_payment_term") and str(kwargs.get("other_payment_term")) != str(deal.other_payment_term):
        lst.append(f'other_payment_term - {kwargs.get("other_payment_term")}')
    if kwargs.get("loaded_weight") and str(kwargs.get("loaded_weight")) != str(deal.loaded_weight):
        lst.append(f'loaded_weight - {kwargs.get("loaded_weight")}')
    if kwargs.get("accepted_weight") and str(kwargs.get("accepted_weight")) != str(deal.accepted_weight):
        lst.append(f'accepted_weight - {kwargs.get("accepted_weight")}')

    print(f'SHIPPING_DATE - {str(kwargs.get("shipping_date")).split("T")[0]} - {str(deal.shipping_date).split(" ")[0]}')
    if kwargs.get("shipping_date") and str(kwargs.get("shipping_date")).split("T")[0] != str(
            deal.shipping_date).split(" ")[0]:
        lst.append(f'shipping_date - {kwargs.get("shipping_date").split("T")[0]}')

    if kwargs.get("who_delivers") and int(kwargs.get("who_delivers")) != int(deal.who_delivers):
        lst.append(f'who_delivers - {kwargs.get("who_delivers")}')
    if kwargs.get("buyer_pays_shipping") and str(kwargs.get("buyer_pays_shipping")).lower() != str(
            deal.buyer_pays_shipping).lower():
        lst.append(f'buyer_pays_shipping - {kwargs.get("buyer_pays_shipping")}')
    if kwargs.get("shipping_address") and kwargs.get("shipping_address") != deal.shipping_address:
        lst.append(f'shipping_address - {kwargs.get("shipping_address")}')
    if kwargs.get("shipping_latitude") and float(kwargs.get("shipping_latitude")) != float(deal.shipping_latitude):
        lst.append(f'shipping_latitude - {kwargs.get("shipping_latitude")}')
    if kwargs.get("shipping_longitude") and float(kwargs.get("shipping_longitude")) != float(deal.shipping_longitude):
        lst.append(f'shipping_longitude - {kwargs.get("shipping_longitude")}')
    if kwargs.get("application") and int(kwargs.get("application")) != int(deal.application.id):
        lst.append(f'application - {kwargs.get("application")}')
    if kwargs.get("buyer_company") and int(kwargs.get("buyer_company")) != int(deal.buyer_company.id):
        lst.append(f'buyer_company - {kwargs.get("buyer_company")}')
    if kwargs.get("delivery_city") and int(kwargs.get("delivery_city")) != int(deal.delivery_city.id):
        lst.append(f'delivery_city - {kwargs.get("delivery_city")}')
    if kwargs.get("shipping_city") and int(kwargs.get("shipping_city")) != int(deal.shipping_city.id):
        lst.append(f'shipping_city - {kwargs.get("shipping_city")}')
    if kwargs.get("supplier_company") and int(kwargs.get("supplier_company")) != int(deal.supplier_company.id):
        lst.append(f'supplier_company - {kwargs.get("supplier_company")}')
    if kwargs.get("delivery_date") and str(kwargs.get("delivery_date")) != str(deal.delivery_date):
        lst.append(f'delivery_date - {kwargs.get("delivery_date")}')
    if kwargs.get("chat") and int(kwargs.get("chat")) != int(deal.chat.id):
        lst.append(f'chat - {kwargs.get("chat")}')
    if kwargs.get("deal_number") and str(kwargs.get("deal_number")) != str(deal.deal_number):
        lst.append(f'deal_number - {kwargs.get("deal_number")}')
    if kwargs.get("loading_hours") and str(kwargs.get("loading_hours")) != str(deal.loading_hours):
        lst.append(f'loading_hours - {kwargs.get("loading_hours")}')
    if kwargs.get("created_by") and int(kwargs.get("created_by")) != int(deal.created_by.id):
        lst.append(f'created_by - {kwargs.get("created_by")}')

    # ДЛЯ СДЕЛОК ПО ОБОРУДОВАНИЮ
    if kwargs.get("count") and int(kwargs.get("count")) != int(deal.count):
        lst.append(f'count - {kwargs.get("count")}')
    if kwargs.get("delivery_latitude") and float(kwargs.get("delivery_latitude")) != float(deal.delivery_latitude):
        lst.append(f'delivery_latitude - {kwargs.get("delivery_latitude")}')
    if kwargs.get("delivery_longitude") and float(kwargs.get("delivery_longitude")) != float(deal.delivery_longitude):
        lst.append(f'delivery_longitude - {kwargs.get("delivery_longitude")}')

    print(f'WEIGHT - {str(kwargs.get("weight"))} - {str(deal.weight)}')
    if kwargs.get("weight") and str(kwargs.get("weight")) != str(deal.weight):
        lst.append(f'weight - {kwargs.get("weight")}')
    return lst


class DecimalEncoder(json.JSONEncoder):
    """
    Because default encoder can't encode Decimal, we should use custom encoder to do it.
    Used code from: https://stackoverflow.com/a/52319674
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


MONTH_MAPPING = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}
