from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PcComponent:
    """Base class for PC components"""
    name: str
    price: float
    url: str = ""
    rating: float = 0.0
    image_url: str = ""
    component_type: str = ""


@dataclass
class Cpu(PcComponent):
    """CPU component"""
    cores: int = 0
    frequency: float = 0.0
    component_type: str = "cpu"


@dataclass
class Gpu(PcComponent):
    """GPU component"""
    vram: int = 0
    component_type: str = "gpu"


@dataclass
class Ram(PcComponent):
    """RAM component"""
    capacity: int = 0  # in GB
    type: str = ""  # DDR4, DDR5, etc.
    component_type: str = "ram"


@dataclass
class Storage(PcComponent):
    """Storage component"""
    capacity: int = 0  # in GB
    type: str = ""  # SSD, HDD, etc.
    component_type: str = "storage"


@dataclass
class Motherboard(PcComponent):
    """Motherboard component"""
    socket: str = ""
    form_factor: str = ""
    component_type: str = "motherboard"


@dataclass
class PowerSupply(PcComponent):
    """Power supply component"""
    wattage: int = 0
    component_type: str = "power_supply"


@dataclass
class Case(PcComponent):
    """PC case component"""
    form_factor: str = ""
    component_type: str = "case"


@dataclass
class PcBuild:
    """Complete PC build with components"""
    budget_usd: int
    budget_rub: int
    purpose: str
    cpu: Optional[Cpu] = None
    gpu: Optional[Gpu] = None
    ram: Optional[Ram] = None
    storage: Optional[Storage] = None
    motherboard: Optional[Motherboard] = None
    power_supply: Optional[PowerSupply] = None
    case: Optional[Case] = None
    
    @property
    def total_price_rub(self) -> float:
        """Calculate total price in RUB"""
        components = [self.cpu, self.gpu, self.ram, self.storage, 
                     self.motherboard, self.power_supply, self.case]
        return sum(comp.price for comp in components if comp is not None)
    
    @property
    def total_price_usd(self) -> float:
        """Calculate total price in USD"""
        return round(self.total_price_rub / 75, 2)  # Using fixed conversion rate
    
    def get_components_dict(self) -> Dict[str, Optional[PcComponent]]:
        """Get dictionary of components for easier iteration"""
        return {
            "cpu": self.cpu,
            "gpu": self.gpu,
            "ram": self.ram,
            "storage": self.storage,
            "motherboard": self.motherboard,
            "power_supply": self.power_supply,
            "case": self.case
        }


@dataclass
class ComponentRecommendation:
    """Recommendation for a specific component type"""
    component_type: str
    budget_usd: int
    purpose: str
    recommendations: List[PcComponent] = field(default_factory=list)