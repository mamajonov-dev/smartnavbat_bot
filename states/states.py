from aiogram.dispatcher.filters.state import State, StatesGroup


class AddServiceState(StatesGroup):
    name = State()
    company = State()

class AddCompanyState(StatesGroup):
    name = State()
    service = State()
    work_time = State()
    location = State()
    telegram_id = State()
    confirm = State()



class AddClientState(StatesGroup):
    service = State()
    company = State()
    work_time = State()
    name = State()
    username = State()
    location = State()
    telegram_id = State()
    confirm = State()

class EditTimeState(StatesGroup):
    start = State()
    end = State()


class BookingInfoState(StatesGroup):
    service = State()
    company = State()
    location = State()
    staff = State()
    time = State()
    name = State()
    phone = State()
    extra_phone = State()
    confirm_slot = State()
    barber = State()
    day = State()

class SubscriptionState(StatesGroup):
    service = State()
    staff = State()
    time = State()

class LocationState(StatesGroup):
    location = State()

class SearchBarber(StatesGroup):
    waiting_for_name = State()

class EditCompanyState(StatesGroup):
    user_id = State()
    change = State()
    name = State()
    active = State()
    location = State()
    phone = State()
    telegram_id = State()
    region = State()
    district = State()
class EditStaffState(StatesGroup):
    user_id = State()
    change = State()
    name = State()
    active = State()
    location = State()
    phone = State()
    telegram_id = State()
    region = State()
    district = State()

class AddRegionState(StatesGroup):
    name = State()

class AddDistrictState(StatesGroup):
    region = State()
    name = State()



