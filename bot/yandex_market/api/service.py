from typing import Dict, List, Optional
import logging
from bot.yandex_market.api.client import YandexMarketApiClient
from bot.config_data import config_dict
from bot.yandex_market.domain.models.models import (
    PcComponent, Cpu, Gpu, Ram, Storage, Motherboard, PowerSupply, Case, PcBuild, ComponentRecommendation
)

logger = logging.getLogger(__name__)

class PcAssemblerService:
    """Service for assembling PC configurations using Yandex Market data"""
    
    def __init__(self, api_client: Optional[YandexMarketApiClient] = None):
        """
        Initialize PC Assembler Service
        
        Args:
            api_client (YandexMarketApiClient, optional): Yandex Market API client
        """
        self.api_client = api_client or YandexMarketApiClient(
            api_key=config_dict["yandex_market_api_key"],
            oauth_token=config_dict["yandex_market_oauth_token"]
        )
    
    async def create_pc_build(self, budget: int, purpose: str) -> PcBuild:
        """
        Create a PC build based on budget and purpose
        
        Args:
            budget (int): Budget in USD
            purpose (str): Purpose of the PC
            
        Returns:
            PcBuild: PC build configuration
        """
        # Convert USD to RUB for Yandex Market (example conversion rate)
        budget_rub = budget * 75  # Using a fixed conversion rate for example
        
        try:
            pc_build = await self.api_client.generate_pc_build(budget_rub, purpose)
            return pc_build
            
        except Exception as e:
            logger.error(f"Error creating PC build: {str(e)}")
            raise
    
    async def get_component_recommendations(self, component_type: str, budget: int, purpose: str) -> ComponentRecommendation:
        """
        Get component recommendations for a specific component type
        
        Args:
            component_type (str): Type of component (e.g., "cpu", "gpu")
            budget (int): Budget in USD
            purpose (str): Purpose of the PC
            
        Returns:
            ComponentRecommendation: Recommendations for the component
        """
        budget_rub = budget * 75  # Convert to RUB
        
        component_methods = {
            "cpu": self.api_client.get_cpu_list,
            "gpu": self.api_client.get_gpu_list,
            "ram": self.api_client.get_ram_list,
            "storage": self.api_client.get_storage_list,
            "motherboard": self.api_client.get_motherboard_list,
            "power_supply": self.api_client.get_power_supply_list,
            "case": self.api_client.get_case_list
        }
        
        if component_type not in component_methods:
            raise ValueError(f"Unsupported component type: {component_type}")
        
        method = component_methods[component_type]
        components = await method(price_to=budget_rub)
        
        # Create and return recommendations
        recommendations = ComponentRecommendation(
            component_type=component_type,
            budget_usd=budget,
            purpose=purpose,
            recommendations=components[:5]  # Limit to top 5
        )
            
        return recommendations