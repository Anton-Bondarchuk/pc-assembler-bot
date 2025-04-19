# import pytest
# from unittest.mock import patch, MagicMock, AsyncMock

# from bot.yandex_market.api.service import PcAssemblerService
# from bot.yandex_market.api.client import YandexMarketApiClient
# from bot.yandex_market.domain.models.models import (
#     PcBuild, Cpu, Gpu, Ram, Storage, Motherboard, PowerSupply, Case, ComponentRecommendation
# )


# @pytest.fixture
# def mock_api_client():
#     """Create a mock YandexMarketApiClient."""
#     client = AsyncMock(spec=YandexMarketApiClient)
#     return client


# @pytest.fixture
# def assembler_service(mock_api_client):
#     """Create a PcAssemblerService with a mock API client."""
#     return PcAssemblerService(api_client=mock_api_client)


# @pytest.mark.asyncio
# async def test_create_pc_build(assembler_service, mock_api_client):
#     """Test creating a PC build."""
#     # Create a mock PC build
#     mock_build = PcBuild(
#         budget_usd=1000,
#         budget_rub=75000,
#         purpose="Игры",
#         cpu=Cpu(name="Test CPU", price=15000),
#         gpu=Gpu(name="Test GPU", price=25000),
#         ram=Ram(name="Test RAM", price=5000),
#         storage=Storage(name="Test Storage", price=5000),
#         motherboard=Motherboard(name="Test Motherboard", price=10000),
#         power_supply=PowerSupply(name="Test PSU", price=5000),
#         case=Case(name="Test Case", price=5000)
#     )
    
#     # Configure the mock API client
#     mock_api_client.generate_pc_build.return_value = mock_build
    
#     # Call the method to test
#     result = await assembler_service.create_pc_build(1000, "Игры")
    
#     # Verify API client was called correctly
#     mock_api_client.generate_pc_build.assert_called_once_with(75000, "Игры")
    
#     # Verify result
#     assert result == mock_build
#     assert result.budget_usd == 1000
#     assert result.budget_rub == 75000
#     assert result.purpose == "Игры"
#     assert result.cpu.name == "Test CPU"
#     assert result.gpu.name == "Test GPU"


# @pytest.mark.asyncio
# async def test_create_pc_build_error(assembler_service, mock_api_client):
#     """Test error handling in create_pc_build."""
#     # Configure the mock API client to raise an exception
#     mock_api_client.generate_pc_build.side_effect = Exception("API Error")
    
#     # Call the method and expect an exception
#     with pytest.raises(Exception) as excinfo:
#         await assembler_service.create_pc_build(1000, "Игры")
    
#     assert "API Error" in str(excinfo.value)


# @pytest.mark.asyncio
# async def test_get_component_recommendations(assembler_service, mock_api_client):
#     """Test getting component recommendations."""
#     # Create mock components
#     mock_cpus = [
#         Cpu(name="CPU 1", price=10000),
#         Cpu(name="CPU 2", price=15000),
#         Cpu(name="CPU 3", price=20000)
#     ]
    
#     # Configure the mock API client
#     mock_api_client.get_cpu_list.return_value = mock_cpus
    
#     # Call the method to test
#     result = await assembler_service.get_component_recommendations("cpu", 500, "Игры")
    
#     # Verify API client was called correctly
#     mock_api_client.get_cpu_list.assert_called_once_with(price_to=37500)
    
#     # Verify result
#     assert isinstance(result, ComponentRecommendation)
#     assert result.component_type == "cpu"
#     assert result.budget_usd == 500
#     assert result.purpose == "Игры"
#     assert len(result.recommendations) == 3
#     assert result.recommendations[0].name == "CPU 1"


# @pytest.mark.asyncio
# async def test_get_component_recommendations_invalid_type(assembler_service):
#     """Test getting recommendations for invalid component type."""
#     with pytest.raises(ValueError) as excinfo:
#         await assembler_service.get_component_recommendations("invalid_type", 1000, "Игры")
    
#     assert "Unsupported component type" in str(excinfo.value)