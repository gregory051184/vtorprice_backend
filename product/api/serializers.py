from rest_framework import serializers

from common.serializers import (
    NonNullDynamicFieldsModelSerializer,
    BaseCreateSerializer,
)
from exchange.models import RecyclablesApplication
from product.models import (
    Recyclables,
    RecyclablesCategory,
    EquipmentCategory,
    Equipment,
)


class ShortRecyclablesCategorySerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = RecyclablesCategory


class ShortEquipmentCategorySerializer(NonNullDynamicFieldsModelSerializer):  # (ShortRecyclablesCategorySerializer):
    class Meta:
        model = EquipmentCategory


class RecyclablesSerializer(NonNullDynamicFieldsModelSerializer):
    category = ShortRecyclablesCategorySerializer()

    class Meta:
        model = Recyclables


class RecyclablesShortSerializerForMainFilter(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = Recyclables
        fields = ("id",)


class CreateRecyclablesSerializer(BaseCreateSerializer):
    class Meta:
        model = Recyclables

    def to_representation(self, instance):
        return RecyclablesSerializer(instance).data


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class RecyclablesCategorySerializer(NonNullDynamicFieldsModelSerializer):
    subcategories = RecursiveField(many=True)
    recyclables = RecyclablesSerializer(many=True, exclude=("category",))

    class Meta:
        model = RecyclablesCategory


class EquipmentCategorySerializer(NonNullDynamicFieldsModelSerializer):
    subcategories = RecursiveField(many=True)
    equipments = RecyclablesSerializer(many=True, exclude=("category",))

    class Meta:
        model = EquipmentCategory


class EquipmentSerializer(NonNullDynamicFieldsModelSerializer):
    category = ShortEquipmentCategorySerializer()

    class Meta:
        model = Equipment


class CreateEquipmentSerializer(BaseCreateSerializer):
    class Meta:
        model = Equipment

    def to_representation(self, instance):
        return EquipmentSerializer(instance).data


class TwoLastSupplyContractsList(NonNullDynamicFieldsModelSerializer):
    contracts = serializers.SerializerMethodField(read_only=True)
    purchase_contracts_volume_list = serializers.SerializerMethodField(read_only=True)
    sales_contracts_volume_list = serializers.SerializerMethodField(read_only=True)
    purchase_total_volume = serializers.SerializerMethodField(read_only=True)
    sales_total_volume = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RecyclablesCategory
        fields = (
            'id', 'name', 'contracts', 'purchase_total_volume', 'sales_total_volume', 'purchase_contracts_volume_list',
            'sales_contracts_volume_list')

    def get_purchase_contracts_volume_list(self, obj):
        lst = RecyclablesApplication.objects.filter(urgency_type=2, deal_type=1,
                                                    recyclables__category__id=obj.id)
        result = []
        if (len(lst) > 0):
            result = list(map(lambda app: {"volume": int(app.volume) / 1000,
                                           "region": app.city.region.id if app.city and app.city.region else 0,
                                           "district": app.city.region.district.id if app.city and app.city.region and app.city.region.district else 0},
                              lst))
            return result
        return result

    def get_sales_contracts_volume_list(self, obj):
        lst = RecyclablesApplication.objects.filter(urgency_type=2, deal_type=2,
                                                    recyclables__category__id=obj.id)
        result = []
        if (len(lst) > 0):
            result = list(map(lambda app: {"volume": int(app.volume) / 1000,
                                           "region": app.city.region.id if app.city and app.city.region else 0,
                                           "district": app.city.region.district.id if app.city and app.city.region and app.city.region.district else 0},
                              lst))
            return result
        return result

    def get_contracts(self, obj):
        lst = RecyclablesApplication.objects.filter(urgency_type=2, deal_type=1,
                                                    recyclables__category__id=obj.id).order_by("created_at")[0:2]
        result = list(map(lambda app: int(app.price), lst))
        prices_dict = {}
        if len(result) > 0:
            prices_dict["last_price"] = result[0]
            if (len(result) > 1):
                prices_dict["pre_last_price"] = result[1]
            if (len(result) == 1):
                prices_dict["pre_last_price"] = 0
        else:
            prices_dict["last_price"] = 0
            prices_dict["pre_last_price"] = 0
        return prices_dict

    def get_purchase_total_volume(self, obj):
        lst = RecyclablesApplication.objects.filter(urgency_type=2, deal_type=1, recyclables__category__id=obj.id)
        result = map(lambda app: int(app.volume) / 1000, lst)
        return sum(result)

    def get_sales_total_volume(self, obj):
        lst = RecyclablesApplication.objects.filter(urgency_type=2, deal_type=2, recyclables__category__id=obj.id)
        result = map(lambda app: int(app.volume) / 1000, lst)
        return sum(result)

# TODO: Add later
#
# class RecyclingCodeSerializer(NonNullDynamicFieldsModelSerializer):
#     recyclables = RecyclablesSerializer(many=True, exclude=("recycling_code",))
#
#     class Meta:
#         model = RecyclingCode
