import json
import os
import logging
from typing import Dict, List, Any, Optional
from ortools.linear_solver import pywraplp
import asyncio

class PcAssemblerService:
    """Service for optimizing PC builds based on budget and intended use goals."""
    
    # Goal-specific component importance coefficients
    GOAL_ALLOCATIONS = {
        "games": {
            "cpu": 0.20,
            "video_card": 0.35,
            "memory": 0.10,
            "storage": 0.10,
            "motherboard": 0.10,
            "power_supply": 0.08,
            "case": 0.07
        },
        "office": {
            "cpu": 0.25,
            "video_card": 0.10,
            "memory": 0.15,
            "storage": 0.20,
            "motherboard": 0.12,
            "power_supply": 0.08,
            "case": 0.10
        },
        "graphics": {
            "cpu": 0.25,
            "video_card": 0.30,
            "memory": 0.15,
            "storage": 0.12,
            "motherboard": 0.08,
            "power_supply": 0.05,
            "case": 0.05
        },
        "video": {
            "cpu": 0.30,
            "video_card": 0.25,
            "memory": 0.15,
            "storage": 0.15,
            "motherboard": 0.05,
            "power_supply": 0.05,
            "case": 0.05
        },
        "programming": {
            "cpu": 0.30,
            "video_card": 0.10,
            "memory": 0.20,
            "storage": 0.15,
            "motherboard": 0.10,
            "power_supply": 0.08,
            "case": 0.07
        },
        "universal": {
            "cpu": 0.25,
            "video_card": 0.20,
            "memory": 0.15,
            "storage": 0.15,
            "motherboard": 0.10,
            "power_supply": 0.08,
            "case": 0.07
        }
    }

    # Budget allocation recommendations by goal (percentage of total budget)
    BUDGET_ALLOCATIONS = {
        "games": {
            "cpu": 0.20,
            "video_card": 0.40,
            "memory": 0.10,
            "storage": 0.10,
            "motherboard": 0.10,
            "power_supply": 0.07,
            "case": 0.03
        },
        "office": {
            "cpu": 0.30,
            "video_card": 0.10,
            "memory": 0.20,
            "storage": 0.20,
            "motherboard": 0.10,
            "power_supply": 0.05,
            "case": 0.05
        },
        "graphics": {
            "cpu": 0.25,
            "video_card": 0.35,
            "memory": 0.15,
            "storage": 0.10,
            "motherboard": 0.05,
            "power_supply": 0.05,
            "case": 0.05
        },
        "video": {
            "cpu": 0.35,
            "video_card": 0.25,
            "memory": 0.15,
            "storage": 0.10,
            "motherboard": 0.05,
            "power_supply": 0.05,
            "case": 0.05
        },
        "programming": {
            "cpu": 0.30,
            "video_card": 0.15,
            "memory": 0.25,
            "storage": 0.15,
            "motherboard": 0.05,
            "power_supply": 0.05,
            "case": 0.05
        },
        "universal": {
            "cpu": 0.25,
            "video_card": 0.25,
            "memory": 0.15,
            "storage": 0.15,
            "motherboard": 0.10,
            "power_supply": 0.05,
            "case": 0.05
        }
    }
    
    # Translation mapping for component categories
    CATEGORY_TRANSLATIONS = {
        'cpu': 'Процессор',
        'memory': 'Оперативная память',
        'motherboard': 'Материнская плата',
        'power_supply': 'Блок питания',
        'case': 'Корпус',
        'video_card': 'Видеокарта',
        'storage': 'Накопитель'
    }
    
    # Translation mapping for goals
    GOAL_TRANSLATIONS = {
        'games': 'Игровой',
        'office': 'Офисный',
        'graphics': 'Для графики',
        'video': 'Для видеомонтажа',
        'programming': 'Для программирования',
        'universal': 'Универсальный'
    }

    def __init__(self, data_dir: str = "./bot/pc-part-dataset/data/json/"):
        """
        Initialize the PC Assembler Service.
        
        Args:
            data_dir: Directory containing the PC components JSON files
        """
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        self.components_cache = {}  # Cache to store loaded components
    
    async def load_components_async(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Asynchronously load all component data from JSON files.
        """
        # If components are already cached, return them
        if self.components_cache:
            return self.components_cache
        
        # Use asyncio to run the synchronous file loading in a thread pool
        return await asyncio.to_thread(self._load_components_sync)
    
    def _load_components_sync(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Synchronously load all component data from JSON files.
        """
        components = {}
        
        # Map of filename patterns to category keys
        category_files = {
            'cpu': 'cpu.json',
            'memory': 'memory.json',
            'motherboard': 'motherboard.json',
            'power_supply': 'power-supply.json',
            'case': 'case.json',
            'video_card': 'video-card.json',
            'storage': 'storage.json',
        }
        
        for category, filename in category_files.items():
            # Check for both standard hyphen and unicode hyphen versions
            standard_path = os.path.join(self.data_dir, filename)
            unicode_path = os.path.join(self.data_dir, filename.replace('-', '‑'))
            
            file_path = None
            if os.path.exists(standard_path):
                file_path = standard_path
            elif os.path.exists(unicode_path):
                file_path = unicode_path
            
            if not file_path:
                self.logger.warning(f"Component file for {category} not found")
                continue
                
            try:
                with open(file_path, 'r') as f:
                    components[category] = json.load(f)
                self.logger.info(f"Loaded {len(components[category])} {category} components")
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
        
        if not components:
            raise ValueError(f"No component files found in {self.data_dir}")
        
        # Store in cache for future use
        self.components_cache = components
        return components
    
    def _calculate_base_utility(self, component: Dict[str, Any], category: str) -> Optional[float]:
        """
        Calculate a base utility score for a component based on its attributes and category.
        
        Args:
            component: The component data
            category: The component category
            
        Returns:
            A utility value or None if utility can't be calculated
        """
        # Base value to ensure all components have some utility
        base_utility = 50
        
        # If price is None, we can't calculate price/performance
        if component.get('price') is None:
            return None
        
        price = float(component.get('price', 0))
        if price <= 0:
            return None
        
        # Category-specific utility calculations
        if category == 'cpu':
            # Base CPU utility on core count and clock speeds if available
            core_count = float(component.get('core_count', 4))
            boost_clock = float(component.get('boost_clock', component.get('core_clock', 3.0)))
            
            # More cores and higher clock speed = higher utility
            return base_utility + (core_count * boost_clock * 2)
            
        elif category == 'video_card':
            # Base GPU utility on memory and clock speeds if available
            memory = float(component.get('memory', 4))
            boost_clock = float(component.get('boost_clock', component.get('core_clock', 1000)))
            
            # More memory and higher clock speed = higher utility
            return base_utility + (memory * 5) + (boost_clock / 100)
            
        elif category == 'memory':
            # Base RAM utility on total capacity and speed
            if 'modules' in component and 'speed' in component:
                try:
                    # Extract module info (e.g. [2, 8] = 2 modules of 8GB each)
                    if isinstance(component['modules'], list) and len(component['modules']) >= 2:
                        num_modules = float(component['modules'][0])
                        size_per_module = float(component['modules'][1])
                        total_size = num_modules * size_per_module
                    else:
                        total_size = 8  # Default if we can't parse
                    
                    # Extract speed info
                    if isinstance(component['speed'], list) and len(component['speed']) >= 2:
                        speed = float(component['speed'][1])
                    else:
                        speed = 3000  # Default if we can't parse
                    
                    return base_utility + (total_size * 2) + (speed / 100)
                except:
                    return base_utility
            
            return base_utility
            
        elif category == 'motherboard':
            # Base motherboard utility on form factor and features
            form_factor = component.get('form_factor', '')
            
            # Bigger form factors generally offer more features
            form_factor_score = 0
            if 'ATX' in str(form_factor):
                form_factor_score = 20
            elif 'Micro ATX' in str(form_factor):
                form_factor_score = 15
            elif 'Mini ITX' in str(form_factor):
                form_factor_score = 10
            
            return base_utility + form_factor_score
            
        elif category == 'power_supply':
            # Base PSU utility on wattage and efficiency
            wattage = float(component.get('wattage', 500))
            efficiency = str(component.get('efficiency', '')).lower()
            
            efficiency_score = 0
            if 'titanium' in efficiency:
                efficiency_score = 30
            elif 'platinum' in efficiency:
                efficiency_score = 25
            elif 'gold' in efficiency:
                efficiency_score = 20
            elif 'silver' in efficiency:
                efficiency_score = 15
            elif 'bronze' in efficiency:
                efficiency_score = 10
            
            return base_utility + (wattage / 20) + efficiency_score
            
        elif category == 'case':
            # Base case utility on type and features
            case_type = str(component.get('type', ''))
            
            type_score = 0
            if 'Full Tower' in case_type:
                type_score = 20
            elif 'Mid Tower' in case_type:
                type_score = 15
            elif 'Mini Tower' in case_type:
                type_score = 10
            
            return base_utility + type_score
            
        elif category == 'storage':
            # Base storage utility on capacity and type (SSD vs HDD)
            capacity = float(component.get('capacity', 500))
            storage_type = str(component.get('type', '')).lower()
            
            type_score = 0
            if 'ssd' in storage_type:
                type_score = 20
            elif 'nvme' in storage_type:
                type_score = 30
            
            return base_utility + (capacity / 100) + type_score
        
        # Default utility for unknown categories
        return base_utility
    
    def _calculate_utility(self, component: Dict[str, Any], category: str, goal: str, budget: float) -> Optional[float]:
        """
        Calculate a utility score for a component based on attributes, category, goal, and budget.
        
        Args:
            component: The component data
            category: The component category
            goal: The PC build goal
            budget: The total budget
            
        Returns:
            A utility value or None if utility can't be calculated
        """
        # Calculate the base utility for this component
        base_utility = self._calculate_base_utility(component, category)
        
        if base_utility is None:
            return None
        
        # Get component price
        price = float(component.get('price', 0))
        
        # Get the importance coefficient for this category based on the user's goal
        goal_weights = self.GOAL_ALLOCATIONS.get(goal, self.GOAL_ALLOCATIONS["universal"])
        category_weight = goal_weights.get(category, 0.1)
        
        # Get the recommended budget allocation for this category
        budget_allocation = self.BUDGET_ALLOCATIONS.get(goal, self.BUDGET_ALLOCATIONS["universal"])
        category_budget = budget_allocation.get(category, 0.1) * budget
        
        # Calculate price factor based on budget level
        # For high budgets, we'll be more lenient with expensive components
        # and even give a bonus to higher-end components
        if budget >= 2000:  # High budget
            if price > category_budget * 2:  # Way over budget
                price_factor = 0.6
            elif price > category_budget * 1.5:  # Significantly over budget
                price_factor = 0.8
            elif price > category_budget:  # Over budget
                price_factor = 0.9
            elif price >= category_budget * 0.7:  # Ideal price range for high budgets
                price_factor = 1.2  # Bonus for using more of the budget
            elif price >= category_budget * 0.4:  # Decent price range
                price_factor = 1.0
            else:  # Too cheap for the budget
                price_factor = 0.7
        elif budget >= 1000:  # Medium budget
            if price > category_budget * 1.5:  # Way over budget
                price_factor = 0.6
            elif price > category_budget * 1.2:  # Over budget 
                price_factor = 0.8
            elif price > category_budget:  # Slightly over budget
                price_factor = 0.9
            elif price >= category_budget * 0.6:  # Ideal price range
                price_factor = 1.1
            elif price >= category_budget * 0.3:  # Decent price range
                price_factor = 1.0
            else:  # Too cheap for the budget
                price_factor = 0.8
        else:  # Low budget
            if price > category_budget * 1.2:  # Way over budget
                price_factor = 0.5
            elif price > category_budget:  # Over budget
                price_factor = 0.7
            elif price >= category_budget * 0.8:  # Ideal price range
                price_factor = 1.0
            elif price >= category_budget * 0.5:  # Decent price range
                price_factor = 0.9
            else:  # Too cheap but might be necessary for low budgets
                price_factor = 0.8
        
        # For high budgets, we're going to add a raw price component to encourage spending more
        price_bonus = 0
        if budget >= 1500:
            # Add a bonus that scales with the price, but caps at a certain level
            price_bonus = min(price / 100, category_budget / 50)
        
        # Final utility calculation: base utility * goal weight * price factor + price bonus
        final_utility = (base_utility * (category_weight ** 2) * price_factor) + price_bonus
        
        return final_utility
    
    def _filter_components_by_goal(self, components: Dict[str, List[Dict[str, Any]]], goal: str, budget: float) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pre-filter components based on the goal and budget to focus on more appropriate options.
        
        Args:
            components: Dictionary of components by category
            goal: The PC build goal
            budget: The total budget
            
        Returns:
            Filtered components dictionary
        """
        filtered_components = {}
        
        # Get budget allocations for this goal
        budget_allocation = self.BUDGET_ALLOCATIONS.get(goal, self.BUDGET_ALLOCATIONS["universal"])
        
        # Adjust filtering based on budget size
        for category, items in components.items():
            # Calculate target budget for this category
            category_budget = budget_allocation.get(category, 0.1) * budget
            
            # For high budgets, allow more expensive components
            if budget >= 2000:
                max_price = category_budget * 3  # Very generous for high budgets
            elif budget >= 1000:
                max_price = category_budget * 2.5  # More generous for medium-high budgets
            else:
                max_price = category_budget * 2  # Standard for low budgets
            
            # Filter items based on price range
            filtered_items = []
            for item in items:
                if item.get('price') is None:
                    continue
                    
                try:
                    price = float(item['price'])
                    # Keep items that are within reasonable price range for this category
                    if price > 0 and price <= max_price:
                        filtered_items.append(item)
                except:
                    continue
            
            # For higher budgets, make sure we include more expensive options
            if budget >= 1500 and filtered_items:
                # Sort by price (descending) and ensure we have enough high-end options
                filtered_items.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
                # Get at least 100 high-end components if available
                high_end_items = filtered_items[:100]
                
                # Get a balanced selection of components across the price range
                remaining_items = filtered_items[100:]
                if remaining_items:
                    remaining_items.sort(key=lambda x: float(x.get('price', 0)))
                    # Select components across the price range
                    step = max(1, len(remaining_items) // 900)  # Up to 900 more items
                    balanced_items = remaining_items[::step]
                    
                    # Combine high-end and balanced selections
                    filtered_items = high_end_items + balanced_items
                else:
                    filtered_items = high_end_items
            
            # Keep a reasonable number of components (up to 1000)
            if len(filtered_items) > 1000:
                # For low budgets: prioritize cheaper components
                # For high budgets: ensure a good mix of high-end components
                if budget < 1000:
                    # Sort by price (ascending) for low budgets
                    filtered_items.sort(key=lambda x: float(x.get('price', 0)))
                else:
                    # For high budgets, get a mix of high-end and mid-range
                    # Sort by price and take a balanced selection
                    filtered_items.sort(key=lambda x: float(x.get('price', 0)))
                    
                # Limit to 1000 items
                filtered_items = filtered_items[:1000]
                
            if filtered_items:
                filtered_components[category] = filtered_items
        
        return filtered_components
    
    async def generate_pc_build(self, budget: float, goal: str) -> Dict[str, Any]:
        """
        Generate an optimal PC build based on the given budget and goal.
        
        Args:
            budget: The total budget in USD
            goal: The purpose of the build (games, office, etc.)
            
        Returns:
            A dictionary containing the selected components, total price, and other details
        """
        # Load components
        components = await self.load_components_async()
        
        # Pre-filter components by goal and budget
        self.logger.info(f"Pre-filtering components based on {goal} build requirements...")
        filtered_components = self._filter_components_by_goal(components, goal, budget)
        
        # Calculate utility for each component and filter out invalid components
        valid_components = {}
        for category, items in filtered_components.items():
            valid_items = []
            
            for item in items:
                # Skip components with None/null price
                if item.get('price') is None:
                    continue
                
                try:
                    price = float(item['price'])
                    if price <= 0:
                        continue
                    
                    # Calculate utility score for this component based on the goal and budget
                    utility = self._calculate_utility(item, category, goal, budget)
                    if utility is None or utility <= 0:
                        continue
                    
                    # Add utility to the item for later use
                    item_with_utility = item.copy()
                    item_with_utility['utility'] = utility
                    valid_items.append(item_with_utility)
                except Exception as e:
                    # Skip items that cause errors
                    self.logger.debug(f"Error processing {category} component: {e}")
                    continue
            
            if valid_items:  # Only add category if it has valid items
                self.logger.info(f"Found {len(valid_items)} valid {category} components for {goal} build")
                valid_components[category] = valid_items
        
        # Check if we still have enough valid components
        if not valid_components:
            return {
                'status': 'ERROR',
                'message': 'No valid components with price and utility values found'
            }
        
        # Check for missing categories (we need at least CPU, memory, motherboard, power supply, and case)
        required_categories = {'cpu', 'memory', 'motherboard', 'power_supply', 'case'}
        missing_categories = required_categories - set(valid_components.keys())
        if missing_categories:
            return {
                'status': 'ERROR',
                'message': f'Missing components for categories: {", ".join(missing_categories)}'
            }
        
        # Run the optimization in a separate thread to avoid blocking
        return await asyncio.to_thread(self._solve_mckp, valid_components, budget, goal)
    
    def _solve_mckp(self, valid_components: Dict[str, List[Dict[str, Any]]], budget: float, goal: str) -> Dict[str, Any]:
        """
        Solve the Multiple-Choice Knapsack Problem to find the optimal PC build.
        
        Args:
            valid_components: Dictionary of valid components by category
            budget: The total budget
            goal: The PC build goal
            
        Returns:
            A dictionary containing the solution details
        """
        # For large budgets, try to encourage spending at least 80% of the budget
        min_budget_pct = 0.8 if budget >= 1500 else 0.0
        min_spend = budget * min_budget_pct
        
        # Create the solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        
        if not solver:
            return {
                'status': 'ERROR',
                'message': 'Failed to create solver. Make sure OR-Tools is properly installed.'
            }
        
        # Create binary decision variables
        x = {}  # x[category][i] = 1 if component i is selected in category
        
        for category, items in valid_components.items():
            x[category] = []
            for i in range(len(items)):
                x[category].append(solver.BoolVar(f'x_{category}_{i}'))
        
        # Budget constraint (upper bound)
        budget_constraint = solver.Constraint(0, budget)
        for category, items in valid_components.items():
            for i, item in enumerate(items):
                price = float(item['price'])
                budget_constraint.SetCoefficient(x[category][i], price)
        
        # For high budgets, add a minimum spend constraint to avoid cheap builds
        if min_spend > 0:
            min_budget_constraint = solver.Constraint(min_spend, solver.infinity())
            for category, items in valid_components.items():
                for i, item in enumerate(items):
                    price = float(item['price'])
                    min_budget_constraint.SetCoefficient(x[category][i], price)
        
        # One component per category constraint
        for category, items in valid_components.items():
            constraint = solver.Constraint(1, 1)  # Exactly one
            for i in range(len(items)):
                constraint.SetCoefficient(x[category][i], 1.0)
        
        # Objective: maximize total utility
        objective = solver.Objective()
        for category, items in valid_components.items():
            for i, item in enumerate(items):
                utility = float(item['utility'])
                objective.SetCoefficient(x[category][i], utility)
        objective.SetMaximization()
        
        # Solve the problem
        status = solver.Solve()
        
        # Process the solution
        if status == pywraplp.Solver.OPTIMAL:
            solution = {}
            total_price = 0.0
            total_utility = 0.0
            
            # Get the budget allocation for this goal
            budget_allocation = self.BUDGET_ALLOCATIONS.get(goal, self.BUDGET_ALLOCATIONS["universal"])
            
            # Collect selected components with their details
            components_with_details = []
            
            for category, items in valid_components.items():
                for i in range(len(items)):
                    if x[category][i].solution_value() > 0.5:  # Selected
                        component = items[i]
                        solution[category] = component
                        price = float(component['price'])
                        total_price += price
                        total_utility += float(component['utility'])
                        
                        # Calculate budget allocation details
                        budget_percentage = (price / budget) * 100
                        recommended_percentage = budget_allocation.get(category, 0.1) * 100
                        
                        # Add component with details to the list
                        components_with_details.append({
                            'category': category,
                            'category_ru': self.CATEGORY_TRANSLATIONS.get(category, category),
                            'name': component['name'],
                            'price': price,
                            'utility': float(component['utility']),
                            'budget_percentage': budget_percentage,
                            'recommended_percentage': recommended_percentage,
                            'details': component  # Include full component details
                        })
            
            # If we're spending less than 80% of a high budget, try again with higher minimum
            if budget >= 1500 and total_price < budget * 0.8:
                # Try again with a higher minimum spend constraint
                # This is a recursive call, but with modified min_spend requirements
                second_attempt = self._solve_mckp_with_min_spend(
                    valid_components, budget, goal, budget * 0.8
                )
                if second_attempt['status'] == 'OPTIMAL':
                    return second_attempt
            
            # Sort components for display
            sorted_components = sorted(components_with_details, key=lambda x: x['category'])
            
            return {
                'status': 'OPTIMAL',
                'goal': goal,
                'goal_ru': self.GOAL_TRANSLATIONS.get(goal, goal),
                'selected_components': solution,
                'components_with_details': sorted_components,
                'total_price': total_price,
                'total_utility': total_utility,
                'remaining_budget': budget - total_price,
                'budget_allocation': budget_allocation
            }
        elif status == pywraplp.Solver.INFEASIBLE:
            return {'status': 'INFEASIBLE', 'message': 'No feasible solution found with this budget'}
        else:
            return {'status': 'ERROR', 'message': f'Solver error with status: {status}'}
    
    def _solve_mckp_with_min_spend(self, valid_components, budget, goal, min_spend):
        """Helper method to solve MCKP with a specific minimum spend requirement"""
        # Create the solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        
        if not solver:
            return {'status': 'ERROR', 'message': 'Failed to create solver'}
        
        # Create binary decision variables
        x = {}  # x[category][i] = 1 if component i is selected in category
        
        for category, items in valid_components.items():
            x[category] = []
            for i in range(len(items)):
                x[category].append(solver.BoolVar(f'x_{category}_{i}'))
        
        # Budget constraint (upper bound)
        budget_constraint = solver.Constraint(0, budget)
        
        # Minimum spend constraint (lower bound)
        min_budget_constraint = solver.Constraint(min_spend, solver.infinity())
        
        # Set coefficients for both constraints
        for category, items in valid_components.items():
            for i, item in enumerate(items):
                price = float(item['price'])
                budget_constraint.SetCoefficient(x[category][i], price)
                min_budget_constraint.SetCoefficient(x[category][i], price)
        
        # One component per category constraint
        for category, items in valid_components.items():
            constraint = solver.Constraint(1, 1)  # Exactly one
            for i in range(len(items)):
                constraint.SetCoefficient(x[category][i], 1.0)
        
        # Objective: maximize total utility
        objective = solver.Objective()
        for category, items in valid_components.items():
            for i, item in enumerate(items):
                utility = float(item['utility'])
                objective.SetCoefficient(x[category][i], utility)
        objective.SetMaximization()
        
        # Solve the problem
        status = solver.Solve()
        
        # Process the solution
        if status == pywraplp.Solver.OPTIMAL:
            solution = {}
            total_price = 0.0
            total_utility = 0.0
            
            # Get the budget allocation for this goal
            budget_allocation = self.BUDGET_ALLOCATIONS.get(goal, self.BUDGET_ALLOCATIONS["universal"])
            
            # Collect selected components with their details
            components_with_details = []
            
            for category, items in valid_components.items():
                for i in range(len(items)):
                    if x[category][i].solution_value() > 0.5:  # Selected
                        component = items[i]
                        solution[category] = component
                        price = float(component['price'])
                        total_price += price
                        total_utility += float(component['utility'])
                        
                        # Calculate budget allocation details
                        budget_percentage = (price / budget) * 100
                        recommended_percentage = budget_allocation.get(category, 0.1) * 100
                        
                        # Add component with details to the list
                        components_with_details.append({
                            'category': category,
                            'category_ru': self.CATEGORY_TRANSLATIONS.get(category, category),
                            'name': component['name'],
                            'price': price,
                            'utility': float(component['utility']),
                            'budget_percentage': budget_percentage,
                            'recommended_percentage': recommended_percentage,
                            'details': component  # Include full component details
                        })
            
            # Sort components for display
            sorted_components = sorted(components_with_details, key=lambda x: x['category'])
            
            return {
                'status': 'OPTIMAL',
                'goal': goal,
                'goal_ru': self.GOAL_TRANSLATIONS.get(goal, goal),
                'selected_components': solution,
                'components_with_details': sorted_components,
                'total_price': total_price,
                'total_utility': total_utility,
                'remaining_budget': budget - total_price,
                'budget_allocation': budget_allocation
            }
        elif status == pywraplp.Solver.INFEASIBLE:
            # If infeasible with this min_spend, return the original solution
            return {'status': 'INFEASIBLE'}
        else:
            return {'status': 'ERROR', 'message': f'Solver error with status: {status}'}
    
    @staticmethod
    def format_price(price: float, currency: str = "USD") -> str:
        """Format price with currency symbol and thousand separators"""
        if currency == "USD":
            return "${:,.2f}".format(price)
        elif currency == "RUB":
            return "{:,.2f} ₽".format(price)
        else:
            return "{:,.2f}".format(price)
    
    @staticmethod
    def convert_usd_to_rub(price_usd: float, exchange_rate: float = 75.0) -> float:
        """Convert a price from USD to RUB"""
        return price_usd * exchange_rate