"""
Scenario Manager for business-themed game theory scenarios
Provides realistic business contexts for each game type without revealing the underlying game structure
"""

import random
from typing import Dict, List


class ScenarioManager:
    def __init__(self):
        # Define scenarios for each game type
        # Each scenario includes description and move options (without revealing the game type)
        
        self.scenarios = {
            'prisoners_dilemma': [
                {
                    'name': 'Price Competition',
                    'description': (
                        "You and a competitor are the only two firms selling a popular product in your market. "
                        "You're both considering whether to maintain current prices or cut prices to gain market share. "
                        "If you both maintain prices, you'll both enjoy healthy profits. "
                        "If one cuts prices while the other maintains, the price-cutter gains significant market share. "
                        "If you both cut prices, you'll end up in a price war with reduced profits for both."
                    ),
                    'options': ['maintain prices', 'cut prices'],
                    'move_mapping': {'maintain prices': 'cooperate', 'cut prices': 'defect'}
                },
                {
                    'name': 'R&D Information Sharing',
                    'description': (
                        "Your company and another firm are working on similar technologies. "
                        "You could share research findings to accelerate progress for both, or keep your research secret. "
                        "Mutual sharing would benefit both companies through faster innovation. "
                        "If one shares while the other doesn't, the non-sharer gets a competitive advantage. "
                        "If neither shares, progress is slower for both."
                    ),
                    'options': ['share research', 'keep secret'],
                    'move_mapping': {'share research': 'cooperate', 'keep secret': 'defect'}
                },
                {
                    'name': 'Supplier Contract Negotiation',
                    'description': (
                        "You're negotiating a long-term contract with a key supplier who also supplies your competitor. "
                        "You can offer fair terms that ensure stable supply for both companies, "
                        "or you can try to lock in exclusive terms that disadvantage your competitor. "
                        "If both offer fair terms, the supplier maintains good relationships with both. "
                        "If one tries for exclusivity while the other doesn't, they might secure an advantage. "
                        "If both push for exclusivity, the supplier may raise prices for both or seek other customers."
                    ),
                    'options': ['fair terms', 'exclusive terms'],
                    'move_mapping': {'fair terms': 'cooperate', 'exclusive terms': 'defect'}
                }
            ],
            
            'stag_hunt': [
                {
                    'name': 'Joint Venture Investment',
                    'description': (
                        "You and another company are considering a joint venture that requires significant investment from both parties. "
                        "You can commit to the full investment for the joint venture, which will only succeed if both invest fully. "
                        "Alternatively, you can pursue a smaller independent project that guarantees modest returns regardless of their decision. "
                        "The joint venture would yield excellent returns if both commit, but if only one invests fully, they lose their investment. "
                        "The independent project is safe but offers much lower returns."
                    ),
                    'options': ['joint venture', 'independent project'],
                    'move_mapping': {'joint venture': 'stag', 'independent project': 'hare'}
                },
                {
                    'name': 'Industry Standard Development',
                    'description': (
                        "Your company and a competitor are deciding whether to collaborate on developing a new industry standard. "
                        "Full collaboration would create a superior standard benefiting both companies greatly. "
                        "However, this requires significant resource commitment and trust. "
                        "Alternatively, you could develop your own proprietary solution, which is guaranteed to work but offers limited market potential. "
                        "If only one company commits to the standard while the other develops independently, the committing company wastes resources."
                    ),
                    'options': ['develop standard together', 'proprietary solution'],
                    'move_mapping': {'develop standard together': 'stag', 'proprietary solution': 'hare'}
                },
                {
                    'name': 'Market Expansion Strategy',
                    'description': (
                        "Two companies are considering whether to jointly enter an expensive new international market. "
                        "Joint entry would allow cost-sharing and greater market impact, yielding high returns if both commit. "
                        "Each could instead focus on expanding in their current domestic market with guaranteed moderate growth. "
                        "Solo entry into the international market would be too costly and likely fail. "
                        "The domestic expansion is safer but limits growth potential."
                    ),
                    'options': ['international partnership', 'domestic expansion'],
                    'move_mapping': {'international partnership': 'stag', 'domestic expansion': 'hare'}
                }
            ],
            
            'hawk_dove': [
                {
                    'name': 'Patent Dispute',
                    'description': (
                        "Your company and another firm both claim rights to a valuable patent. "
                        "You can aggressively pursue litigation to secure exclusive rights, "
                        "or you can propose a licensing agreement to share the technology. "
                        "If one pursues litigation while the other seeks agreement, the aggressive party likely wins exclusive rights. "
                        "If both litigate aggressively, you'll both incur massive legal costs with uncertain outcomes. "
                        "If both seek agreement, you can quickly establish a mutually beneficial licensing deal."
                    ),
                    'options': ['aggressive litigation', 'seek agreement'],
                    'move_mapping': {'aggressive litigation': 'hawk', 'seek agreement': 'dove'}
                },
                {
                    'name': 'Market Territory Conflict',
                    'description': (
                        "Your company and a competitor are both eyeing the same lucrative geographic market. "
                        "You can aggressively expand into the territory with heavy marketing and pricing strategies, "
                        "or you can propose dividing the territory or finding alternative markets. "
                        "If one expands aggressively while the other yields, the aggressive company dominates the market. "
                        "If both expand aggressively, you'll face a costly market war hurting both companies' profits. "
                        "If both seek alternatives, you can both find profitable opportunities without conflict."
                    ),
                    'options': ['aggressive expansion', 'seek alternatives'],
                    'move_mapping': {'aggressive expansion': 'hawk', 'seek alternatives': 'dove'}
                },
                {
                    'name': 'Talent Acquisition Battle',
                    'description': (
                        "Both your company and a competitor are trying to hire the same team of talented engineers. "
                        "You can make an aggressive offer well above market rate to secure them, "
                        "or you can make a reasonable offer and focus on your company's other advantages. "
                        "If one company makes an aggressive offer while the other doesn't, they get the team. "
                        "If both make aggressive offers, you'll start a bidding war that inflates salaries industry-wide. "
                        "If both make reasonable offers, the team chooses based on other factors, and salary inflation is avoided."
                    ),
                    'options': ['aggressive offer', 'reasonable offer'],
                    'move_mapping': {'aggressive offer': 'hawk', 'reasonable offer': 'dove'}
                }
            ],
            
            'coordination': [
                {
                    'name': 'Technology Platform Choice',
                    'description': (
                        "Your company and a key partner need to choose a technology platform for a joint project. "
                        "There are two equally good options: Platform A and Platform B. "
                        "The critical factor is that you both choose the same platform for compatibility. "
                        "If you choose different platforms, the project will face serious integration challenges. "
                        "Both platforms are equally capable, so the key is coordination."
                    ),
                    'options': ['Platform A', 'Platform B'],
                    'move_mapping': {'Platform A': 'option_a', 'Platform B': 'option_b'}
                },
                {
                    'name': 'Meeting Scheduling System',
                    'description': (
                        "Your division and another need to adopt a scheduling system for inter-departmental meetings. "
                        "Two systems are available: System Alpha (morning-optimized) and System Beta (afternoon-optimized). "
                        "Both systems work well, but they're incompatible with each other. "
                        "If both divisions choose the same system, scheduling is seamless. "
                        "If you choose different systems, coordination becomes very difficult."
                    ),
                    'options': ['System Alpha', 'System Beta'],
                    'move_mapping': {'System Alpha': 'option_a', 'System Beta': 'option_b'}
                },
                {
                    'name': 'Trade Show Participation',
                    'description': (
                        "Your company and a complementary business are deciding which major trade show to attend this year. "
                        "There are two equally prestigious shows: the Spring Expo and the Fall Summit. "
                        "Attending the same show would allow valuable collaboration and joint presentations. "
                        "Attending different shows means missing these synergy opportunities. "
                        "Both shows offer similar visibility and networking benefits."
                    ),
                    'options': ['Spring Expo', 'Fall Summit'],
                    'move_mapping': {'Spring Expo': 'option_a', 'Fall Summit': 'option_b'}
                }
            ]
        }
    
    def get_scenario(self, game_type: str) -> Dict:
        """Get a random scenario for the specified game type"""
        if game_type not in self.scenarios:
            raise ValueError(f"Unknown game type: {game_type}")
        
        scenario = random.choice(self.scenarios[game_type])
        
        # Return scenario with game type included (for internal use)
        return {
            'game_type': game_type,
            'name': scenario['name'],
            'description': scenario['description'],
            'options': scenario['options'],
            'move_mapping': scenario['move_mapping']
        }
    
    def get_all_scenarios_for_type(self, game_type: str) -> List[Dict]:
        """Get all scenarios for a specific game type"""
        if game_type not in self.scenarios:
            return []
        
        return [
            {
                'game_type': game_type,
                'name': s['name'],
                'description': s['description'],
                'options': s['options']
            }
            for s in self.scenarios[game_type]
        ]
    
    def add_scenario(self, game_type: str, scenario: Dict):
        """Add a new scenario to the collection"""
        if game_type not in self.scenarios:
            self.scenarios[game_type] = []
        
        # Validate scenario structure
        required_fields = ['name', 'description', 'options', 'move_mapping']
        for field in required_fields:
            if field not in scenario:
                raise ValueError(f"Scenario missing required field: {field}")
        
        self.scenarios[game_type].append(scenario)
    
    def export_scenarios(self) -> Dict:
        """Export all scenarios (without move mappings for external use)"""
        export_data = {}
        
        for game_type, scenarios in self.scenarios.items():
            export_data[game_type] = [
                {
                    'name': s['name'],
                    'description': s['description'],
                    'options': s['options']
                }
                for s in scenarios
            ]
        
        return export_data
