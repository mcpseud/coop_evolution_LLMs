#!/usr/bin/env python3
"""
Basic analysis script for LLM Game Theory Simulation results
Provides quick insights into simulation outcomes
"""

import json
import csv
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


class ResultsAnalyzer:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.data = {}
        
    def load_data(self):
        """Load all data files from the output directory"""
        print(f"Loading data from {self.output_dir}...")
        
        # Find the most recent files
        move_files = list(self.output_dir.glob("moves_*.csv"))
        comm_files = list(self.output_dir.glob("communications_*.csv"))
        payoff_files = list(self.output_dir.glob("payoffs_*.csv"))
        memory_files = list(self.output_dir.glob("memories_*.csv"))
        
        if not move_files:
            raise FileNotFoundError(f"No move files found in {self.output_dir}")
        
        # Use most recent files
        self.data['moves'] = self._load_csv(sorted(move_files)[-1])
        self.data['communications'] = self._load_csv(sorted(comm_files)[-1]) if comm_files else []
        self.data['payoffs'] = self._load_csv(sorted(payoff_files)[-1]) if payoff_files else []
        self.data['memories'] = self._load_csv(sorted(memory_files)[-1]) if memory_files else []
        
        print(f"Loaded {len(self.data['moves'])} moves")
        
    def _load_csv(self, filepath: Path) -> List[Dict]:
        """Load CSV file into list of dictionaries"""
        data = []
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def analyze_cooperation_rates(self):
        """Analyze cooperation rates by agent and game type"""
        print("\n=== Cooperation Analysis ===")
        
        # Define cooperative moves for each game
        cooperative_moves = {
            'prisoners_dilemma': ['cooperate', 'maintain prices', 'share research', 'fair terms'],
            'stag_hunt': ['stag', 'joint venture', 'develop standard together', 'international partnership'],
            'hawk_dove': ['dove', 'seek agreement', 'seek alternatives', 'reasonable offer'],
            'coordination': ['option_a', 'option_b', 'Platform A', 'Platform B']  # Both are cooperative in coordination
        }
        
        # Overall cooperation rate
        total_cooperative = 0
        total_moves = len(self.data['moves'])
        
        for move_data in self.data['moves']:
            game_type = move_data['game_type']
            move = move_data['move'].lower()
            
            if game_type in cooperative_moves:
                if any(coop_move.lower() in move for coop_move in cooperative_moves[game_type]):
                    total_cooperative += 1
        
        if total_moves > 0:
            print(f"Overall cooperation rate: {total_cooperative/total_moves:.2%}")
        
        # By game type
        game_cooperation = defaultdict(lambda: {'cooperative': 0, 'total': 0})
        
        for move_data in self.data['moves']:
            game_type = move_data['game_type']
            move = move_data['move'].lower()
            
            game_cooperation[game_type]['total'] += 1
            
            if game_type in cooperative_moves:
                if any(coop_move.lower() in move for coop_move in cooperative_moves[game_type]):
                    game_cooperation[game_type]['cooperative'] += 1
        
        print("\nCooperation rate by game type:")
        for game_type, stats in sorted(game_cooperation.items()):
            if stats['total'] > 0:
                rate = stats['cooperative'] / stats['total']
                print(f"  {game_type}: {rate:.2%} ({stats['cooperative']}/{stats['total']})")
        
        # By agent
        agent_cooperation = defaultdict(lambda: {'cooperative': 0, 'total': 0})
        
        for move_data in self.data['moves']:
            agent_id = move_data['agent_id']
            game_type = move_data['game_type']
            move = move_data['move'].lower()
            
            agent_cooperation[agent_id]['total'] += 1
            
            if game_type in cooperative_moves:
                if any(coop_move.lower() in move for coop_move in cooperative_moves[game_type]):
                    agent_cooperation[agent_id]['cooperative'] += 1
        
        # Extract strategy names from agent IDs
        strategy_cooperation = defaultdict(lambda: {'cooperative': 0, 'total': 0})
        
        for agent_id, stats in agent_cooperation.items():
            strategy = agent_id.rsplit('_', 2)[0]  # Extract strategy name
            strategy_cooperation[strategy]['cooperative'] += stats['cooperative']
            strategy_cooperation[strategy]['total'] += stats['total']
        
        print("\nCooperation rate by strategy:")
        for strategy, stats in sorted(strategy_cooperation.items(), 
                                     key=lambda x: x[1]['cooperative']/x[1]['total'] if x[1]['total'] > 0 else 0, 
                                     reverse=True):
            if stats['total'] > 0:
                rate = stats['cooperative'] / stats['total']
                print(f"  {strategy}: {rate:.2%} ({stats['cooperative']}/{stats['total']})")
    
    def analyze_payoffs(self):
        """Analyze average payoffs by strategy and game type"""
        if not self.data['payoffs']:
            print("\nNo payoff data available")
            return
            
        print("\n=== Payoff Analysis ===")
        
        # Average payoff by strategy
        strategy_payoffs = defaultdict(list)
        
        for payoff_data in self.data['payoffs']:
            agent_id = payoff_data['agent_id']
            strategy = agent_id.rsplit('_', 2)[0]
            payoff = int(payoff_data['payoff'])
            strategy_payoffs[strategy].append(payoff)
        
        print("\nAverage payoff by strategy:")
        for strategy, payoffs in sorted(strategy_payoffs.items(), 
                                       key=lambda x: sum(x[1])/len(x[1]), 
                                       reverse=True):
            avg_payoff = sum(payoffs) / len(payoffs)
            print(f"  {strategy}: {avg_payoff:.2f} (n={len(payoffs)})")
        
        # Average payoff by game type
        game_payoffs = defaultdict(list)
        
        for payoff_data in self.data['payoffs']:
            game_type = payoff_data['game_type']
            payoff = int(payoff_data['payoff'])
            game_payoffs[game_type].append(payoff)
        
        print("\nAverage payoff by game type:")
        for game_type, payoffs in sorted(game_payoffs.items()):
            avg_payoff = sum(payoffs) / len(payoffs)
            print(f"  {game_type}: {avg_payoff:.2f}")
    
    def analyze_communication_patterns(self):
        """Analyze communication patterns"""
        if not self.data['communications']:
            print("\nNo communication data available")
            return
            
        print("\n=== Communication Analysis ===")
        
        # Message count by agent
        message_counts = Counter()
        
        for comm in self.data['communications']:
            sender = comm['sender_id'].rsplit('_', 2)[0]
            message_counts[sender] += 1
        
        print("\nMessages sent by strategy:")
        for strategy, count in message_counts.most_common():
            print(f"  {strategy}: {count}")
        
        # Common words/phrases
        word_counts = Counter()
        
        for comm in self.data['communications']:
            message = comm['message'].lower()
            # Simple word extraction (could be improved)
            words = message.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_counts[word] += 1
        
        print("\nMost common words in communications:")
        for word, count in word_counts.most_common(10):
            print(f"  {word}: {count}")
    
    def analyze_game_outcomes(self):
        """Analyze mutual cooperation vs defection in different games"""
        print("\n=== Game Outcome Patterns ===")
        
        # Group moves by pairing and round
        pairings = defaultdict(lambda: defaultdict(dict))
        
        for move_data in self.data['moves']:
            pairing_id = move_data['pairing_id']
            round_num = move_data['round']
            agent_id = move_data['agent_id']
            game_type = move_data['game_type']
            move = move_data['move']
            
            pairings[pairing_id][round_num]['game_type'] = game_type
            pairings[pairing_id][round_num][agent_id] = move
        
        # Analyze outcome patterns
        outcome_patterns = defaultdict(lambda: defaultdict(int))
        
        for pairing_id, rounds in pairings.items():
            for round_num, round_data in rounds.items():
                game_type = round_data.get('game_type')
                if not game_type:
                    continue
                
                # Get the two moves (excluding game_type)
                moves = [v for k, v in round_data.items() if k != 'game_type']
                
                if len(moves) == 2:
                    # Categorize outcome
                    if game_type == 'prisoners_dilemma':
                        if all('cooperate' in m.lower() or 'maintain' in m.lower() or 'share' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Mutual Cooperation'] += 1
                        elif all('defect' in m.lower() or 'cut' in m.lower() or 'secret' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Mutual Defection'] += 1
                        else:
                            outcome_patterns[game_type]['Mixed'] += 1
                    
                    elif game_type == 'stag_hunt':
                        if all('stag' in m.lower() or 'joint' in m.lower() or 'together' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Both Hunt Stag'] += 1
                        elif all('hare' in m.lower() or 'independent' in m.lower() or 'proprietary' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Both Hunt Hare'] += 1
                        else:
                            outcome_patterns[game_type]['Mixed'] += 1
                    
                    elif game_type == 'hawk_dove':
                        if all('hawk' in m.lower() or 'aggressive' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Both Hawk'] += 1
                        elif all('dove' in m.lower() or 'agreement' in m.lower() or 'reasonable' in m.lower() for m in moves):
                            outcome_patterns[game_type]['Both Dove'] += 1
                        else:
                            outcome_patterns[game_type]['Hawk-Dove'] += 1
                    
                    elif game_type == 'coordination':
                        if moves[0].lower() == moves[1].lower():
                            outcome_patterns[game_type]['Coordinated'] += 1
                        else:
                            outcome_patterns[game_type]['Miscoordinated'] += 1
        
        # Print outcome patterns
        for game_type, outcomes in sorted(outcome_patterns.items()):
            print(f"\n{game_type}:")
            total = sum(outcomes.values())
            for outcome, count in sorted(outcomes.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                print(f"  {outcome}: {count} ({percentage:.1f}%)")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*60)
        print("SIMULATION SUMMARY REPORT")
        print("="*60)
        
        # Basic statistics
        print(f"\nTotal moves recorded: {len(self.data['moves'])}")
        print(f"Total communications: {len(self.data['communications'])}")
        
        # Run all analyses
        self.analyze_cooperation_rates()
        self.analyze_payoffs()
        self.analyze_communication_patterns()
        self.analyze_game_outcomes()
        
        print("\n" + "="*60)
        print("Analysis complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze LLM Game Theory Simulation Results"
    )
    
    parser.add_argument(
        'output_dir',
        type=str,
        help='Path to simulation output directory'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export analysis to file (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    analyzer = ResultsAnalyzer(args.output_dir)
    
    try:
        analyzer.load_data()
        analyzer.generate_summary_report()
        
        if args.export:
            print(f"\nExporting analysis to {args.export}...")
            # Could implement JSON export here
            
    except Exception as e:
        print(f"Error analyzing results: {e}")
        raise


if __name__ == "__main__":
    main()
