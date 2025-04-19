from aiogram.fsm.state import State, StatesGroup

class PcAssemblerFSM(StatesGroup): 
    price = State()
    goals = State()