"""
Simulation Engine for LLM Game Theory Experiments
Handles the core logic of running pairings, rounds, and managing agent interactions
"""

import random
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from agent_class import Agent
from game_manager import GameManager
from scenarios_manager import ScenarioManager


class SimulationEngine:
    def __init__(self, agents_config, experiment_config, data_logger, api_key=None, dry_run=False):
        self.logger = logging.getLogger(__name__)
        self.experiment_config = experiment_config
        self.data_logger = data_logger
        self.dry_run = dry_run
        
        # Initialize game manager and scenario manager
        self.game_manager = GameManager()
        self.scenario_manager = ScenarioManager()
        
        # Create agent pool based on frequency
        self.agent_pool = self._create_agent_pool(agents_config, api_key)
        
        # Track statistics
        self.stats = {
            'total_pairings': 0,
            'total_rounds': 0,
            'total_api_calls': 0,
            'moves_by_game': defaultdict(lambda: defaultdict(int)),
            'cooperation_count': 0,
            'defection_count': 0,
            'coop_ewan_count': 0,
            'defection_ewan_count': 0
        }
        
    def _create_agent_pool(self, agents_config, api_key):
        """Create pool of agents based on frequency in config"""
        agent_pool = []
        
        for idx, config in enumerate(agents_config):
            frequency = config.get('frequency', 1)
            
            for i in range(frequency):
                agent = Agent(
                    agent_id=f"{config['strategy_name']}_{idx}_{i}",
                    system_prompt=config['system_prompt'],
                    model=config.get('model', 'gpt-4'),
                    api_key=api_key,
                    memory_limit=self.experiment_config['memory_limit'],
                    allow_thinking=self.experiment_config['allow_thinking'],
                    dry_run=self.dry_run
                )
                agent_pool.append(agent)
        
        self.logger.info(f"Created agent pool with {len(agent_pool)} agents")
        return agent_pool
    
    def run(self):
        """Run the complete simulation"""
        self.logger.info("Starting simulation with configuration:")
        self.logger.info(f"Total pairings: {self.experiment_config['total_pairings']}")
        self.logger.info(f"Gossiping allowed: {self.experiment_config['allow_gossip']}")
        
        for pairing_num in range(self.experiment_config['total_pairings']):
            self.logger.info(f"\n=== Starting Pairing {pairing_num + 1} ===")
            
            # Select two agents randomly
            agent1, agent2 = random.sample(self.agent_pool, 2)
            
            # Run the pairing
            self._run_pairing(agent1, agent2, pairing_num)
            
            # Handle post-pairing gossip if enabled
            if self.experiment_config['allow_gossip']:
                self._handle_gossip(agent1, agent2, pairing_num)
            
            self.stats['total_pairings'] += 1
        
        # Finalize data logger
        self.data_logger.finalize()

        # Aggregate API call counts from all agents
        self.stats['total_api_calls'] = sum(
            agent.get_stats()['api_calls'] for agent in self.agent_pool
        )

        # Calculate final statistics
        total_moves = self.stats['cooperation_count'] + self.stats['defection_count']
        cooperation_rate = self.stats['cooperation_count'] / total_moves if total_moves > 0 else 0

        total_moves_ewan = self.stats['coop_ewan_count'] + self.stats['defection_ewan_count']
        coop_ewan = self.stats['coop_ewan_count'] / total_moves_ewan if total_moves_ewan > 0 else 0

        return {
            'total_pairings': self.stats['total_pairings'],
            'total_rounds': self.stats['total_rounds'],
            'total_api_calls': self.stats['total_api_calls'],
            'cooperation_rate': cooperation_rate,
            'coop_ewan': coop_ewan,
            'moves_by_game': dict(self.stats['moves_by_game']),
            'agent_summaries': self._generate_agent_summaries()
        }
    
    def _run_pairing(self, agent1: Agent, agent2: Agent, pairing_num: int):
        """Run a single pairing between two agents"""
        # Determine number of rounds
        if self.experiment_config['rounds_fixed']:
            num_rounds = self.experiment_config['avg_rounds']
        else:
            # Poisson distribution
            num_rounds = np.random.poisson(self.experiment_config['avg_rounds'])
            num_rounds = max(1, num_rounds)  # Ensure at least 1 round
        
        self.logger.info(f"Pairing {agent1.agent_id} vs {agent2.agent_id} for {num_rounds} rounds")
        
        # Determine game type for this pairing
        if self.experiment_config['game_varies_across_pairings']:
            game_type = self._select_game_type()
            games_for_rounds = [game_type] * num_rounds
        else:
            games_for_rounds = [self._select_game_type() for _ in range(num_rounds)]
        
        # Track pairing history
        self.data_logger.start_pairing(pairing_num, agent1.agent_id, agent2.agent_id)
        pairing_history = []
        
        for round_num in range(num_rounds):
            game_type = games_for_rounds[round_num]
            
            self.logger.info(f"Round {round_num + 1}: {game_type}")
            
            # Get scenario for this game type
            scenario = self.scenario_manager.get_scenario(game_type)
            
            # Prepare context with history and memories
            context1 = self._prepare_context(agent1, agent2, pairing_history, scenario)
            context2 = self._prepare_context(agent2, agent1, pairing_history, scenario)
            
            # Communication phase
            messages = []
            for comm_round in range(self.experiment_config['max_communication_rounds']):
                # Agent 1 sends message
                msg1, thinking1 = agent1.communicate(context1, messages)
                if msg1:
                    messages.append({'sender': agent1.agent_id, 'message': msg1})
                    self.data_logger.log_communication(
                        pairing_num, round_num + 1, agent1.agent_id, agent2.agent_id, msg1
                    )
                if thinking1:
                    self.data_logger.log_thinking(
                        pairing_num, round_num + 1, agent1.agent_id, 'communication', thinking1
                    )

                # Agent 2 responds
                msg2, thinking2 = agent2.communicate(context2, messages)
                if msg2:
                    messages.append({'sender': agent2.agent_id, 'message': msg2})
                    self.data_logger.log_communication(
                        pairing_num, round_num + 1, agent2.agent_id, agent1.agent_id, msg2
                    )
                if thinking2:
                    self.data_logger.log_thinking(
                        pairing_num, round_num + 1, agent2.agent_id, 'communication', thinking2
                    )
            
            # Decision phase
            move1, move_thinking1 = agent1.make_move(context1, messages)
            move2, move_thinking2 = agent2.make_move(context2, messages)

            # Log moves
            self.data_logger.log_move(pairing_num, round_num + 1, agent1.agent_id, move1, game_type)
            self.data_logger.log_move(pairing_num, round_num + 1, agent2.agent_id, move2, game_type)

            # Log move thinking
            if move_thinking1:
                self.data_logger.log_thinking(
                    pairing_num, round_num + 1, agent1.agent_id, 'move_decision', move_thinking1
                )
            if move_thinking2:
                self.data_logger.log_thinking(
                    pairing_num, round_num + 1, agent2.agent_id, 'move_decision', move_thinking2
                )

            # Calculate payoffs
            payoffs = self.game_manager.calculate_payoffs(game_type, move1, move2)

            # Log payoffs
            self.data_logger.log_payoff(pairing_num, round_num + 1, agent1.agent_id, game_type, payoffs[0])
            self.data_logger.log_payoff(pairing_num, round_num + 1, agent2.agent_id, game_type, payoffs[1])

            # Update agent payoffs
            agent1.stats['total_payoff'] += payoffs[0]
            agent2.stats['total_payoff'] += payoffs[1]

            # Update statistics
            self._update_stats(game_type, move1, move2)
            
            # Add to pairing history
            pairing_history.append({
                'round': round_num + 1,
                'game_type': game_type,
                'scenario': scenario['name'],
                'moves': {agent1.agent_id: move1, agent2.agent_id: move2},
                'payoffs': {agent1.agent_id: payoffs[0], agent2.agent_id: payoffs[1]},
                'messages': messages
            })

            # Append round data to complete JSON log
            self.data_logger.log_round(pairing_history[-1])

            self.stats['total_rounds'] += 1
        
        # Update memories after pairing
        mem_thinking1 = agent1.update_memory_after_pairing(agent2.agent_id, pairing_history)
        mem_thinking2 = agent2.update_memory_after_pairing(agent1.agent_id, pairing_history)

        # Log memory updates
        self.data_logger.log_memory_update(
            pairing_num, agent1.agent_id, agent2.agent_id,
            agent1.get_memory(agent2.agent_id)
        )
        self.data_logger.log_memory_update(
            pairing_num, agent2.agent_id, agent1.agent_id,
            agent2.get_memory(agent1.agent_id)
        )

        # Log memory thinking
        if mem_thinking1:
            self.data_logger.log_thinking(
                pairing_num, 0, agent1.agent_id, 'memory_update', mem_thinking1
            )
        if mem_thinking2:
            self.data_logger.log_thinking(
                pairing_num, 0, agent2.agent_id, 'memory_update', mem_thinking2
            )

        self.data_logger.end_pairing()
    
    def _prepare_context(self, agent: Agent, opponent: Agent, history: List, scenario: Dict) -> Dict:
        """Prepare context for an agent including history, memory, and scenario"""
        return {
            'opponent_id': opponent.agent_id,
            'scenario': scenario,
            'history': history,
            'memory': agent.get_memory(opponent.agent_id),
            'round_number': len(history) + 1
        }
    
    def _select_game_type(self) -> str:
        """Select game type based on configured proportions"""
        game_props = self.experiment_config['game_proportions']
        games = list(game_props.keys())
        weights = list(game_props.values())
        return random.choices(games, weights=weights)[0]
    
    def _update_stats(self, game_type: str, move1: str, move2: str):
        """Update statistics based on moves"""
        self.stats['moves_by_game'][game_type][f"{move1}-{move2}"] += 1

        # Cooperative moves per game type
        cooperative_moves = {
            'prisoners_dilemma': ['cooperate'],
            'stag_hunt': ['stag'],
            'hawk_dove': ['dove'],
            'coordination': ['option_a', 'option_b']  # Both are cooperative in coordination
        }

        coop_set = cooperative_moves.get(game_type, ['cooperate'])

        for move in [move1, move2]:
            if move.lower() in coop_set:
                self.stats['cooperation_count'] += 1
            else:
                self.stats['defection_count'] += 1

        # Ewan's cooperation metric: for coordination games, cooperation
        # requires both agents to choose the same option (successful coordination).
        # For all other game types, uses the same individual-move logic as above.
        if game_type == 'coordination':
            if move1.lower() == move2.lower():
                self.stats['coop_ewan_count'] += 2
            else:
                self.stats['defection_ewan_count'] += 2
        else:
            for move in [move1, move2]:
                if move.lower() in coop_set:
                    self.stats['coop_ewan_count'] += 1
                else:
                    self.stats['defection_ewan_count'] += 1
    
    def _handle_gossip(self, agent1: Agent, agent2: Agent, pairing_num: int):
        """Handle gossip phase after pairing"""
        # Each agent can gossip to a random subset of other agents
        other_agents = [a for a in self.agent_pool if a not in [agent1, agent2]]

        # Agent 1 gossips
        if other_agents and random.random() < 0.5:  # 50% chance to gossip
            gossip_target = random.choice(other_agents)
            gossip1, gossip_thinking1 = agent1.generate_gossip(agent2.agent_id, gossip_target.agent_id)
            if gossip1:
                recv_thinking1 = gossip_target.receive_gossip(agent1.agent_id, agent2.agent_id, gossip1)
                self.data_logger.log_gossip(
                    agent1.agent_id, gossip_target.agent_id, agent2.agent_id, gossip1
                )
                if gossip_thinking1:
                    self.data_logger.log_thinking(
                        pairing_num, 0, agent1.agent_id, 'gossip_generation', gossip_thinking1
                    )
                if recv_thinking1:
                    self.data_logger.log_thinking(
                        pairing_num, 0, gossip_target.agent_id, 'gossip_processing', recv_thinking1
                    )

        # Agent 2 gossips
        if other_agents and random.random() < 0.5:
            gossip_target = random.choice(other_agents)
            gossip2, gossip_thinking2 = agent2.generate_gossip(agent1.agent_id, gossip_target.agent_id)
            if gossip2:
                recv_thinking2 = gossip_target.receive_gossip(agent2.agent_id, agent1.agent_id, gossip2)
                self.data_logger.log_gossip(
                    agent2.agent_id, gossip_target.agent_id, agent1.agent_id, gossip2
                )
                if gossip_thinking2:
                    self.data_logger.log_thinking(
                        pairing_num, 0, agent2.agent_id, 'gossip_generation', gossip_thinking2
                    )
                if recv_thinking2:
                    self.data_logger.log_thinking(
                        pairing_num, 0, gossip_target.agent_id, 'gossip_processing', recv_thinking2
                    )
    
    def _generate_agent_summaries(self) -> Dict:
        """Generate summary statistics for each agent"""
        summaries = {}
        
        for agent in self.agent_pool:
            summaries[agent.agent_id] = {
                'total_games': agent.get_stats()['total_games'],
                'total_payoff': agent.get_stats()['total_payoff'],
                'strategies_used': agent.get_stats()['strategies_used'],
                'final_memories': agent.get_all_memories()
            }
        
        return summaries
