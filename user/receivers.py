from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from company.models import Company
from company.signals import change_company_fields
from exchange.models import RecyclablesApplication, EquipmentApplication, RecyclablesDeal, EquipmentDeal
from exchange.signals import create_ready_for_shipment_contract, create_supply_contract, update_supply_contract, \
    update_ready_for_shipment_contract, create_equipment_application, update_equipment_application, \
    delete_supply_contract, delete_ready_for_shipment_contract, delete_equipment_application, create_equipment_deal, \
    update_equipment_deal, create_application_deal, update_application_deal, create_supply_contract_by_form, \
    update_supply_contract_by_form
from user.models import UserActions, UserActionsChoices, ModelActionsChoice



@receiver(user_logged_in)
def concurrent_logins(sender, user, **kwargs):
    for ses in Session.objects.all():
        data = ses.get_decoded()
        print(f'FFFFFFFFFFFFFFFFFFFFFFFFFFF - {data.get("_auth_user_hash", None)}')
    print("User is Logged IN")

# ОБРАБОТКА СИГНАЛОВ ОТ КОМПАНИЙ

@receiver(change_company_fields, sender=Company)
def change_company_fields_handler(sender, instance, user, **kwargs):
    company_fields = kwargs["kwargs"]
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.UPDATE,
        action_model=ModelActionsChoice.COMPANY,
        model_id=instance.id,
        updated_fields=company_fields if len(company_fields) > 0 else [f'company_name - {instance.name}',
                                                                       f'company_id - {instance.id}',
                                                                       'explains - через карточку компании']
    )
    user_actions.save()


# ОБРАБОТКА СИГНАЛОВ ОТ ЗАЯВОК НА ВТОРСЫРЬЁ

@receiver(create_supply_contract, sender=RecyclablesApplication)
def create_supply_contract_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
        model_id=instance.id,
        # ДОБАВИЛ ДЛЯ ЗАЯВОК ИЗ КАРТОЧЕК, ЧТОБЫ БЫЛО ПОНЯТНО ЧТО ЭТО ОБНОВЛЕНИЕ КАРТОЧЕК,
        # Т.К. ОНИ ВСЕГДА СОЗДАЮТ НОВЫЕ КОНТРАКТЫ В БД, А СТАРЫЕ ОБНАВЛЯЮТСЯ
        updated_fields=[f'company - {instance.company.name}', f'company_id - {instance.company.id}',
                        f'recyclables_id - {instance.recyclables.id}',
                        f'recyclables_name - {instance.recyclables.name}',
                        f'price - {instance.price}', f'volume - {instance.volume}', f'deal_type - {instance.deal_type}',
                                                     'explains - через карточку компании'] if kwargs else None
    )
    user_actions.save()


@receiver(create_supply_contract_by_form, sender=RecyclablesApplication)
def create_supply_contract_by_form_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
        model_id=instance.id,
        updated_fields=[f'company - {instance.company.name}', f'company_id - {instance.company.id}',
                        f'recyclables_id - {instance.recyclables.id}',
                        f'recyclables_name - {instance.recyclables.name}',
                        f'price - {instance.price}',
                        f'volume - {instance.volume}', f'deal_type - {instance.deal_type}'] if kwargs else None
    )
    user_actions.save()


@receiver(update_supply_contract, sender=RecyclablesApplication)
def update_supply_contract_handler(sender, instance, user, **kwargs):
    application = kwargs["kwargs"]
    if len(application) > 0:
        application.insert(0, f'company_name - {instance.company.name}')
        application.insert(0, f'company_id - {instance.company.id}')
        application.append('explains - через карточку компании')

        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.UPDATE,
            action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
            model_id=instance.id,
            updated_fields=application  # if len(application) > 0 else None
        )
        user_actions.save()


@receiver(update_supply_contract_by_form, sender=RecyclablesApplication)
def update_supply_contract_by_form_handler(sender, instance, user, **kwargs):
    application = kwargs["kwargs"]
    if len(application) > 0:
        application.prepend(f'company_name - {instance.company.name}')
        application.prepend(f'company_id - {instance.company.id}')
        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.UPDATE,
            action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
            model_id=instance.id,
            updated_fields=application  # if len(application) > 0 else None
        )
        user_actions.save()


@receiver(delete_supply_contract, sender=RecyclablesApplication)
def delete_supply_contract_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.DELETE,
        action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
        model_id=instance.id,
    )
    user_actions.save()


@receiver(create_ready_for_shipment_contract, sender=RecyclablesApplication)
def create_ready_for_shipment_contract_handler(sender, instance, user, **kwargs):
    # application = kwargs["kwargs"]
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.READY_FOR_SHIPMENT_APPLICATION,
        model_id=instance.id,
        updated_fields=[f'company - {instance.company.name}', f'company_id - {instance.company.id}',
                        f'recyclables_id - {instance.recyclables.id}',
                        f'recyclables_name - {instance.recyclables.name}',
                        f'price - {instance.price}',
                        f'full_weigth - {instance.full_weigth}', f'deal_type - {instance.deal_type}'] if kwargs else None
    )
    user_actions.save()


@receiver(update_ready_for_shipment_contract, sender=RecyclablesApplication)
def update_ready_for_shipment_contract_handler(sender, instance, user, **kwargs):
    application = kwargs["kwargs"]
    if len(application) > 0:
        application.prepend(f'company_name - {instance.company.name}')
        application.prepend(f'company_id - {instance.company.id}')
        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.DELETE,
            action_model=ModelActionsChoice.READY_FOR_SHIPMENT_APPLICATION,
            model_id=instance.id,
            updated_fields=application  # if len(application) > 0 else None
        )
        user_actions.save()


@receiver(delete_ready_for_shipment_contract, sender=RecyclablesApplication)
def delete_ready_for_shipment_contract_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.DELETE,
        action_model=ModelActionsChoice.SUPPLY_CONTRACT_APPLICATION,
        model_id=instance.id,
    )
    user_actions.save()


@receiver(create_equipment_application, sender=EquipmentApplication)
def create_equipment_application_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.EQUIPMENT_APPLICATION,
        model_id=instance.id,
        updated_fields=[f'company - {instance.company.name}', f'company_id - {instance.company.id}',
                        f'equipment_id - {instance.equipment.id}',
                        f'equipment_name - {instance.equipment.name}',
                        f'price - {instance.price}', f'deal_type - {instance.deal_type}'] if kwargs else None
    )
    user_actions.save()


# ЗАЯВКИ ПО ОБОРУДОВАНИЮ
@receiver(update_equipment_application, sender=EquipmentApplication)
def update_equipment_application_handler(sender, instance, user, **kwargs):
    application = kwargs["kwargs"]
    if len(application) > 0:
        application.prepend(f'company_name - {instance.company.name}')
        application.prepend(f'company_id - {instance.company.id}')
        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.UPDATE,
            action_model=ModelActionsChoice.EQUIPMENT_APPLICATION,
            model_id=instance.id,
            updated_fields=application  # if len(application) > 0 else None
        )
        user_actions.save()


@receiver(delete_equipment_application, sender=EquipmentApplication)
def delete_equipment_application_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.DELETE,
        action_model=ModelActionsChoice.EQUIPMENT_APPLICATION,
        model_id=instance.id,
    )
    user_actions.save()


# СДЕЛКИ С СЫРЬЁМ
@receiver(create_application_deal, sender=RecyclablesDeal)
def create_application_deal_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.RECYCLABLES_DEAL,
        model_id=instance.id,
        updated_fields=[f'company - {instance.company.name}', f'company_id - {instance.company.id}',
                        f'equipment_id - {instance.equipment.id}',
                        f'equipment_name - {instance.equipment.name}',
                        f'price - {instance.price}', f'deal_type - {instance.deal_type}'] if kwargs else None
    )
    user_actions.save()


@receiver(update_application_deal, sender=RecyclablesDeal)
def update_application_deal_handler(sender, instance, user, **kwargs):
    deal = kwargs["kwargs"]
    if len(deal) > 0:
        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.UPDATE,
            action_model=ModelActionsChoice.RECYCLABLES_DEAL,
            model_id=instance.id,
            updated_fields=deal if len(deal) > 0 else None
        )
        user_actions.save()


# СДЕЛКИ С ОБОРУДОВАНИЕМ
@receiver(create_equipment_deal, sender=EquipmentDeal)
def create_equipment_deal_handler(sender, instance, user, **kwargs):
    user_actions = UserActions.objects.create(
        user=user,
        action=UserActionsChoices.CREATE,
        action_model=ModelActionsChoice.EQUIPMENT_DEAL,
        model_id=instance.id,
        updated_fields=[f'deal_weight - {instance.weight}']
    )
    user_actions.save()


@receiver(update_equipment_deal, sender=EquipmentDeal)
def update_equipment_deal_handler(sender, instance, user, **kwargs):
    deal = kwargs["kwargs"]
    if len(deal) > 0:
        user_actions = UserActions.objects.create(
            user=user,
            action=UserActionsChoices.UPDATE,
            action_model=ModelActionsChoice.EQUIPMENT_DEAL,
            model_id=instance.id,
            updated_fields=deal if len(deal) > 0 else None
        )
        user_actions.save()
