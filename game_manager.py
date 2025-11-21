"""
Game Manager for different game theory scenarios
Handles payoff matrices and game logic for prisoner's dilemma, stag hunt, hawk-dove, and coordination games
"""

from typing import Dict, Tuple, List


class GameManager:
    def __init__(self):
        # Define payoff matrices for each game type
        # Format: {(player1_move, player2_move): (player1_payoff, player2_payoff)}
        
        self.payoff_matrices = {
            'prisoners_dilemma': {
                ('cooperate', 'cooperate'): (3, 3),    # Both cooperate
                ('cooperate', 'defect'): (0, 5),       # P1 cooperates, P2 defects
                ('defect', 'cooperate'): (5, 0),       # P1 defects, P2 cooperates
                ('defect', 'defect'): (1, 1)           # Both defect
            },
            
            'stag_hunt': {
                ('stag', 'stag'): (4, 4),              # Both hunt stag (high reward, requires cooperation)
                ('stag', 'hare'): (0, 3),              # P1 hunts stag alone (fails), P2 gets hare
                ('hare', 'stag'): (3, 0),              # P1 gets hare, P2 hunts stag alone (fails)
                ('hare', 'hare'): (2, 2)               # Both hunt hare (safe option)
            },
            
            'hawk_dove': {
                ('hawk', 'hawk'): (-1, -1),            # Both fight (both lose)
                ('hawk', 'dove'): (3, 1),              # Hawk wins, dove yields
                ('dove', 'hawk'): (1, 3),              # Dove yields, hawk wins
                ('dove', 'dove'): (2, 2)               # Both share peacefully
            },
            
            'coordination': {
                ('option_a', 'option_a'): (3, 3),      # Both choose A (coordinate)
                ('option_a', 'option_b'): (0, 0),      # Miscoordination
                ('option_b', 'option_a'): (0, 0),      # Miscoordination
                ('option_b', 'option_b'): (3, 3)       # Both choose B (coordinate)
            }
        }
        
        # Define valid moves for each game
        self.valid_moves = {
            'prisoners_dilemma': ['cooperate', 'defect'],
            'stag_hunt': ['stag', 'hare'],
            'hawk_dove': ['hawk', 'dove'],
            'coordination': ['option_a', 'option_b']
        }
    
    def calculate_payoffs(self, game_type: str, move1: str, move2: str) -> Tuple[int, int]:
        """Calculate payoffs for both players given their moves"""
        if game_type not in self.payoff_matrices:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # Normalize moves
        move1 = move1.lower().strip()
        move2 = move2.lower().strip()
        
        # Validate moves
        if move1 not in self.valid_moves[game_type]:
            # Try to map to valid move
            move1 = self._map_to_valid_move(move1, game_type)
        
        if move2 not in self.valid_moves[game_type]:
            move2 = self._map_to_valid_move(move2, game_type)
        
        # Get payoffs
        payoffs = self.payoff_matrices[game_type].get((move1, move2))
        
        if payoffs is None:
            # This shouldn't happen if moves are properly validated
            return (0, 0)
        
        return payoffs
    
    def _map_to_valid_move(self, move: str, game_type: str) -> str:
        """Try to map an invalid move to a valid one"""
        move_lower = move.lower()
        
        # Common mappings
        if game_type == 'prisoners_dilemma':
            if any(word in move_lower for word in ['trust', 'collaborate', 'share']):
                return 'cooperate'
            elif any(word in move_lower for word in ['betray', 'compete', 'take']):
                return 'defect'
        
        elif game_type == 'stag_hunt':
            if any(word in move_lower for word in ['team', 'together', 'big']):
                return 'stag'
            elif any(word in move_lower for word in ['solo', 'safe', 'small']):
                return 'hare'
        
        elif game_type == 'hawk_dove':
            if any(word in move_lower for word in ['fight', 'aggressive', 'attack']):
                return 'hawk'
            elif any(word in move_lower for word in ['peace', 'yield', 'share']):
                return 'dove'
        
        elif game_type == 'coordination':
            if 'a' in move_lower or 'first' in move_lower:
                return 'option_a'
            elif 'b' in move_lower or 'second' in move_lower:
                return 'option_b'
        
        # Default to first valid move if no mapping found
        return self.valid_moves[game_type][0]
    
    def get_game_description(self, game_type: str) -> str:
        """Get a description of the game type"""
        descriptions = {
            'prisoners_dilemma': (
                "A classic game where mutual cooperation yields good outcomes for both, "
                "but each player has an incentive to defect for personal gain."
            ),
            'stag_hunt': (
                "A coordination game where the best outcome requires mutual trust and cooperation, "
                "but a safe individual option is always available."
            ),
            'hawk_dove': (
                "A game modeling conflict where aggressive behavior pays off against peaceful opponents, "
                "but mutual aggression is costly for both."
            ),
            'coordination': (
                "A pure coordination game where players must choose the same option to succeed, "
                "with no inherent advantage to either choice."
            )
        }
        
        return descriptions.get(game_type, "Unknown game type")
    
    def get_equilibria(self, game_type: str) -> List[Tuple[str, str]]:
        """Get Nash equilibria for a game type"""
        equilibria = {
            'prisoners_dilemma': [('defect', 'defect')],
            'stag_hunt': [('stag', 'stag'), ('hare', 'hare')],
            'hawk_dove': [],  # Mixed strategy equilibrium
            'coordination': [('option_a', 'option_a'), ('option_b', 'option_b')]
        }
        
        return equilibria.get(game_type, [])
    
    def is_pareto_optimal(self, game_type: str, move1: str, move2: str) -> bool:
        """Check if an outcome is Pareto optimal"""
        current_payoffs = self.calculate_payoffs(game_type, move1, move2)
        
        # Check all other possible outcomes
        for m1 in self.valid_moves[game_type]:
            for m2 in self.valid_moves[game_type]:
                if (m1, m2) == (move1, move2):
                    continue
                
                other_payoffs = self.calculate_payoffs(game_type, m1, m2)
                
                # If another outcome is better for both players, current is not Pareto optimal
                if (other_payoffs[0] > current_payoffs[0] and 
                    other_payoffs[1] > current_payoffs[1]):
                    return False
        
        return True
    
    def get_social_optimum(self, game_type: str) -> Tuple[str, str]:
        """Get the socially optimal outcome (highest total payoff)"""
        best_total = -float('inf')
        best_moves = None
        
        for m1 in self.valid_moves[game_type]:
            for m2 in self.valid_moves[game_type]:
                payoffs = self.calculate_payoffs(game_type, m1, m2)
                total = payoffs[0] + payoffs[1]
                
                if total > best_total:
                    best_total = total
                    best_moves = (m1, m2)
        
        return best_moves
