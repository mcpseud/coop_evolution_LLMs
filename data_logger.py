"""
Data Logger for LLM Game Theory Simulations
Handles recording all simulation data including moves, communications, memories, and thinking
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class DataLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Create timestamp for this run
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Initialize different log files
        self.log_files = {
            'moves': self.output_dir / f'moves_{self.timestamp}.csv',
            'communications': self.output_dir / f'communications_{self.timestamp}.csv',
            'thinking': self.output_dir / f'thinking_{self.timestamp}.csv',
            'memories': self.output_dir / f'memories_{self.timestamp}.csv',
            'gossip': self.output_dir / f'gossip_{self.timestamp}.csv',
            'payoffs': self.output_dir / f'payoffs_{self.timestamp}.csv'
        }
        
        # Initialize CSV writers
        self._init_csv_files()
        
        # Also maintain a complete log in JSON format
        self.complete_log = {
            'timestamp': self.timestamp,
            'pairings': []
        }
        
        self.current_pairing = None
    
    def _init_csv_files(self):
        """Initialize CSV files with headers"""
        # Moves log
        with open(self.log_files['moves'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pairing_id', 'round', 'agent_id', 'game_type', 'move'])
        
        # Communications log
        with open(self.log_files['communications'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pairing_id', 'round', 'sender_id', 'receiver_id', 'message'])
        
        # Thinking log
        with open(self.log_files['thinking'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pairing_id', 'round', 'agent_id', 'context', 'thinking'])
        
        # Memories log
        with open(self.log_files['memories'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pairing_id', 'agent_id', 'about_agent_id', 'memory'])
        
        # Gossip log
        with open(self.log_files['gossip'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'sender_id', 'receiver_id', 'about_agent_id', 'gossip'])
        
        # Payoffs log
        with open(self.log_files['payoffs'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pairing_id', 'round', 'agent_id', 'game_type', 'payoff'])
    
    def log_move(self, pairing_id: int, round_num: int, agent_id: str, move: str, game_type: str):
        """Log a move made by an agent"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['moves'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, pairing_id, round_num, agent_id, game_type, move])
        
        self.logger.debug(f"Logged move: {agent_id} -> {move} in {game_type}")
    
    def log_communication(self, pairing_id: int, round_num: int, sender_id: str, 
                         receiver_id: str, message: str):
        """Log a communication between agents"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['communications'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, pairing_id, round_num, sender_id, receiver_id, message])
        
        self.logger.debug(f"Logged communication: {sender_id} -> {receiver_id}")
    
    def log_thinking(self, pairing_id: int, round_num: int, agent_id: str, 
                    context: str, thinking: str):
        """Log private thinking of an agent"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['thinking'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, pairing_id, round_num, agent_id, context, thinking])
        
        self.logger.debug(f"Logged thinking for {agent_id}")
    
    def log_memory_update(self, pairing_id: int, agent_id: str, about_agent_id: str, 
                         memory: str):
        """Log a memory update"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['memories'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, pairing_id, agent_id, about_agent_id, memory])
        
        self.logger.debug(f"Logged memory update: {agent_id} about {about_agent_id}")
    
    def log_gossip(self, sender_id: str, receiver_id: str, about_agent_id: str, 
                   gossip: str):
        """Log gossip shared between agents"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['gossip'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, sender_id, receiver_id, about_agent_id, gossip])
        
        self.logger.debug(f"Logged gossip: {sender_id} -> {receiver_id} about {about_agent_id}")
    
    def log_payoff(self, pairing_id: int, round_num: int, agent_id: str, 
                   game_type: str, payoff: int):
        """Log payoff received by an agent"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_files['payoffs'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, pairing_id, round_num, agent_id, game_type, payoff])
        
        self.logger.debug(f"Logged payoff: {agent_id} received {payoff} in {game_type}")
    
    def log_round(self, round_data: Dict):
        """Append round data to the current pairing in the complete log"""
        if self.current_pairing is not None:
            self.current_pairing['rounds'].append(round_data)

    def start_pairing(self, pairing_id: int, agent1_id: str, agent2_id: str):
        """Start logging a new pairing"""
        self.current_pairing = {
            'pairing_id': pairing_id,
            'agents': [agent1_id, agent2_id],
            'start_time': datetime.now().isoformat(),
            'rounds': []
        }
        
        self.logger.info(f"Started logging pairing {pairing_id}: {agent1_id} vs {agent2_id}")
    
    def end_pairing(self):
        """End the current pairing and save to complete log"""
        if self.current_pairing:
            self.current_pairing['end_time'] = datetime.now().isoformat()
            self.complete_log['pairings'].append(self.current_pairing)
            self.current_pairing = None
            
            # Periodically save complete log
            if len(self.complete_log['pairings']) % 10 == 0:
                self._save_complete_log()
    
    def _save_complete_log(self):
        """Save the complete log to JSON file"""
        log_file = self.output_dir / f'complete_log_{self.timestamp}.json'
        
        with open(log_file, 'w') as f:
            json.dump(self.complete_log, f, indent=2)
        
        self.logger.debug(f"Saved complete log with {len(self.complete_log['pairings'])} pairings")
    
    def finalize(self):
        """Finalize logging and save all data"""
        # Save final complete log
        self._save_complete_log()
        
        # Create summary statistics
        summary = self._generate_summary()
        summary_file = self.output_dir / f'summary_{self.timestamp}.json'
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Finalized all logs in {self.output_dir}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics from the logs"""
        summary = {
            'timestamp': self.timestamp,
            'total_pairings': len(self.complete_log['pairings']),
            'log_files': {name: str(path) for name, path in self.log_files.items()},
            'statistics': {}
        }
        
        # Count moves by game type
        move_counts = {}
        try:
            with open(self.log_files['moves'], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    game_type = row['game_type']
                    move = row['move']
                    
                    if game_type not in move_counts:
                        move_counts[game_type] = {}
                    
                    move_counts[game_type][move] = move_counts[game_type].get(move, 0) + 1
            
            summary['statistics']['moves_by_game'] = move_counts
        except Exception as e:
            self.logger.error(f"Error generating move statistics: {e}")
        
        return summary
    
    def export_for_analysis(self, output_file: str):
        """Export data in a format suitable for analysis"""
        # Combine all relevant data into a single structured format
        analysis_data = {
            'metadata': {
                'timestamp': self.timestamp,
                'output_dir': str(self.output_dir)
            },
            'pairings': []
        }
        
        # Read and structure all the logged data
        try:
            # Read moves
            moves_by_pairing = {}
            with open(self.log_files['moves'], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pairing_id = int(row['pairing_id'])
                    if pairing_id not in moves_by_pairing:
                        moves_by_pairing[pairing_id] = []
                    moves_by_pairing[pairing_id].append(row)
            
            # Read communications
            comms_by_pairing = {}
            with open(self.log_files['communications'], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pairing_id = int(row['pairing_id'])
                    if pairing_id not in comms_by_pairing:
                        comms_by_pairing[pairing_id] = []
                    comms_by_pairing[pairing_id].append(row)
            
            # Combine into structured format
            for pairing_id in moves_by_pairing:
                pairing_data = {
                    'pairing_id': pairing_id,
                    'moves': moves_by_pairing.get(pairing_id, []),
                    'communications': comms_by_pairing.get(pairing_id, [])
                }
                analysis_data['pairings'].append(pairing_data)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            self.logger.info(f"Exported analysis data to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting analysis data: {e}")
