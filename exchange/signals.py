from django.dispatch import Signal

recyclables_deal_status_changed = Signal()

equipment_deal_status_changed = Signal()

application_status_changed = Signal()

deal_completed = Signal()

create_supply_contract = Signal()

create_supply_contract_by_form = Signal()

update_supply_contract = Signal()

update_supply_contract_by_form = Signal()

delete_supply_contract = Signal()

create_ready_for_shipment_contract = Signal()

update_ready_for_shipment_contract = Signal()

delete_ready_for_shipment_contract = Signal()

create_equipment_application = Signal()

update_equipment_application = Signal()

delete_equipment_application = Signal()

create_application_deal = Signal()

update_application_deal = Signal()

create_equipment_deal = Signal()

update_equipment_deal = Signal()






