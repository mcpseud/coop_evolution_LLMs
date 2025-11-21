"""
Configuration Loader for LLM Game Theory Simulations
Handles loading and parsing of CSV configuration files
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any


class ConfigLoader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_agents(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load agent configurations from CSV file
        Expected columns: strategy_name, system_prompt, model, frequency
        """
        agents = []
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Agent configuration file not found: {filepath}")
        
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate required columns
            required_columns = ['strategy_name', 'system_prompt', 'frequency']
            if not all(col in reader.fieldnames for col in required_columns):
                missing = [col for col in required_columns if col not in reader.fieldnames]
                raise ValueError(f"Agent CSV missing required columns: {missing}")
            
            for row in reader:
                agent_config = {
                    'strategy_name': row['strategy_name'].strip(),
                    'system_prompt': row['system_prompt'].strip(),
                    'model': row.get('model', 'gpt-4').strip(),
                    'frequency': int(row.get('frequency', 1))
                }
                
                # Validate frequency
                if agent_config['frequency'] < 1:
                    self.logger.warning(
                        f"Invalid frequency for {agent_config['strategy_name']}, setting to 1"
                    )
                    agent_config['frequency'] = 1
                
                agents.append(agent_config)
        
        self.logger.info(f"Loaded {len(agents)} agent configurations from {filepath}")
        return agents
    
    def load_experiment(self, filepath: str) -> Dict[str, Any]:
        """
        Load experiment configuration from CSV file
        This file should have parameters as rows with 'parameter' and 'value' columns
        """
        config = {}
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Experiment configuration file not found: {filepath}")
        
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate required columns
            if 'parameter' not in reader.fieldnames or 'value' not in reader.fieldnames:
                raise ValueError("Experiment CSV must have 'parameter' and 'value' columns")
            
            for row in reader:
                param = row['parameter'].strip().lower()
                value = row['value'].strip()
                
                # Parse different parameter types
                if param == 'avg_rounds':
                    config['avg_rounds'] = int(value)
                
                elif param == 'rounds_fixed':
                    config['rounds_fixed'] = value.lower() in ['true', 'yes', '1', 'fixed']
                
                elif param == 'total_pairings':
                    config['total_pairings'] = int(value)
                
                elif param == 'allow_gossip':
                    config['allow_gossip'] = value.lower() in ['true', 'yes', '1']
                
                elif param == 'memory_limit':
                    config['memory_limit'] = int(value)
                
                elif param == 'max_communication_rounds':
                    config['max_communication_rounds'] = int(value)
                
                elif param == 'game_proportions':
                    # Parse game proportions (format: "pd:40,sh:30,hd:20,coord:10")
                    proportions = {}
                    for game_prop in value.split(','):
                        if ':' in game_prop:
                            game, prop = game_prop.split(':')
                            game_map = {
                                'pd': 'prisoners_dilemma',
                                'sh': 'stag_hunt',
                                'hd': 'hawk_dove',
                                'coord': 'coordination'
                            }
                            full_name = game_map.get(game.strip(), game.strip())
                            proportions[full_name] = float(prop.strip())
                    
                    # Normalize proportions to sum to 1
                    total = sum(proportions.values())
                    if total > 0:
                        proportions = {k: v/total for k, v in proportions.items()}
                    
                    config['game_proportions'] = proportions
                
                elif param == 'game_varies_across_pairings':
                    config['game_varies_across_pairings'] = value.lower() in ['true', 'yes', '1']
                
                elif param == 'allow_thinking':
                    config['allow_thinking'] = value.lower() in ['true', 'yes', '1']
        
        # Set defaults for any missing parameters
        defaults = {
            'avg_rounds': 5,
            'rounds_fixed': True,
            'total_pairings': 100,
            'allow_gossip': True,
            'memory_limit': 500,
            'max_communication_rounds': 3,
            'game_proportions': {
                'prisoners_dilemma': 0.25,
                'stag_hunt': 0.25,
                'hawk_dove': 0.25,
                'coordination': 0.25
            },
            'game_varies_across_pairings': True,
            'allow_thinking': True
        }
        
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
                self.logger.info(f"Using default value for {key}: {default_value}")
        
        self.logger.info(f"Loaded experiment configuration from {filepath}")
        return config
    
    def save_agent_template(self, filepath: str):
        """Save a template CSV file for agent configuration"""
        filepath = Path(filepath)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['strategy_name', 'system_prompt', 'model', 'frequency']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write example agents
            examples = [
                {
                    'strategy_name': 'Tit-for-Tat',
                    'system_prompt': 'You are a cooperative agent that starts by cooperating and then mirrors your opponent\'s previous move. Value reciprocity and fairness.',
                    'model': 'gpt-4',
                    'frequency': 2
                },
                {
                    'strategy_name': 'Always Cooperate',
                    'system_prompt': 'You are an altruistic agent that always seeks mutual benefit. Prioritize collective success over individual gain.',
                    'model': 'gpt-4',
                    'frequency': 1
                },
                {
                    'strategy_name': 'Always Defect',
                    'system_prompt': 'You are a self-interested agent focused on maximizing your own payoff. Prioritize individual success.',
                    'model': 'gpt-4',
                    'frequency': 1
                },
                {
                    'strategy_name': 'Random',
                    'system_prompt': 'You make decisions based on varied considerations. Sometimes cooperate, sometimes compete, based on the specific situation.',
                    'model': 'gpt-4',
                    'frequency': 2
                }
            ]
            
            for example in examples:
                writer.writerow(example)
        
        self.logger.info(f"Saved agent template to {filepath}")
    
    def save_experiment_template(self, filepath: str):
        """Save a template CSV file for experiment configuration"""
        filepath = Path(filepath)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['parameter', 'value', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write all parameters with descriptions
            parameters = [
                {
                    'parameter': 'avg_rounds',
                    'value': '5',
                    'description': 'Average number of rounds per pairing'
                },
                {
                    'parameter': 'rounds_fixed',
                    'value': 'true',
                    'description': 'Whether rounds are fixed (true) or stochastic/Poisson (false)'
                },
                {
                    'parameter': 'total_pairings',
                    'value': '100',
                    'description': 'Total number of pairings to run'
                },
                {
                    'parameter': 'allow_gossip',
                    'value': 'true',
                    'description': 'Whether agents can share information about others after pairings'
                },
                {
                    'parameter': 'memory_limit',
                    'value': '500',
                    'description': 'Maximum characters for memory about each other agent'
                },
                {
                    'parameter': 'max_communication_rounds',
                    'value': '3',
                    'description': 'Maximum back-and-forth messages before move decision'
                },
                {
                    'parameter': 'game_proportions',
                    'value': 'pd:40,sh:30,hd:20,coord:10',
                    'description': 'Relative proportions of game types (pd=prisoners dilemma, sh=stag hunt, hd=hawk-dove, coord=coordination)'
                },
                {
                    'parameter': 'game_varies_across_pairings',
                    'value': 'true',
                    'description': 'If true, game type set per pairing. If false, can change each round within pairing'
                },
                {
                    'parameter': 'allow_thinking',
                    'value': 'true',
                    'description': 'Whether agents can use <thinking> tags for private thoughts'
                }
            ]
            
            for param in parameters:
                writer.writerow(param)
        
        self.logger.info(f"Saved experiment template to {filepath}")
