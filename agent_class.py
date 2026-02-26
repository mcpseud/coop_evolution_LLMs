"""
Agent class for LLM-based game theory players
Handles communication, decision-making, memory management, and API interactions
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import openai
import os


class Agent:
    def __init__(self, agent_id: str, system_prompt: str, model: str = "gpt-4",
                 api_key: Optional[str] = None, memory_limit: int = 500,
                 allow_thinking: bool = True, dry_run: bool = False):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.model = model
        self.memory_limit = memory_limit
        self.allow_thinking = allow_thinking
        self.dry_run = dry_run
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Initialize OpenAI client
        if not dry_run:
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass --api-key")
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
        
        # Initialize memories for other agents
        self.memories = {}  # {agent_id: memory_text}
        
        # Track statistics
        self.stats = {
            'total_games': 0,
            'total_payoff': 0,
            'strategies_used': defaultdict(int),
            'api_calls': 0
        }
        
        # Cache for current conversation
        self.conversation_history = []
    
    def communicate(self, context: Dict, previous_messages: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Generate a communication message to send to opponent. Returns (message, thinking)."""
        prompt = self._build_communication_prompt(context, previous_messages)

        thinking, response = self._call_llm(prompt, "communication")

        if thinking:
            self.logger.debug(f"Thinking: {thinking}")

        return response, thinking
    
    def make_move(self, context: Dict, messages: List[Dict]) -> Tuple[str, Optional[str]]:
        """Decide on a move in the game. Returns (move, thinking)."""
        prompt = self._build_move_prompt(context, messages)

        thinking, response = self._call_llm(prompt, "move_decision")

        if thinking:
            self.logger.debug(f"Thinking: {thinking}")

        # Extract the actual move from response using scenario move_mapping
        move = self._extract_move(
            response, context['scenario']['game_type'],
            context['scenario'].get('move_mapping')
        )

        self.stats['total_games'] += 1
        self.stats['strategies_used'][move] += 1

        return move, thinking
    
    def update_memory_after_pairing(self, opponent_id: str, pairing_history: List[Dict]) -> Optional[str]:
        """Update memory about an opponent after a pairing. Returns thinking."""
        prompt = self._build_memory_update_prompt(opponent_id, pairing_history)

        thinking, response = self._call_llm(prompt, "memory_update")

        if thinking:
            self.logger.debug(f"Thinking: {thinking}")

        # Truncate to memory limit
        if len(response) > self.memory_limit:
            response = response[:self.memory_limit]

        self.memories[opponent_id] = response
        self.logger.info(f"Updated memory for {opponent_id}: {response[:100]}...")
        return thinking
    
    def generate_gossip(self, about_agent: str, to_agent: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate gossip about another agent. Returns (gossip, thinking)."""
        if about_agent not in self.memories:
            return None, None

        prompt = self._build_gossip_prompt(about_agent, to_agent)

        thinking, response = self._call_llm(prompt, "gossip_generation")

        if thinking:
            self.logger.debug(f"Thinking: {thinking}")

        return response, thinking
    
    def receive_gossip(self, from_agent: str, about_agent: str, gossip: str) -> Optional[str]:
        """Process received gossip and update memories. Returns thinking."""
        prompt = self._build_gossip_processing_prompt(from_agent, about_agent, gossip)

        thinking, response = self._call_llm(prompt, "gossip_processing")

        if thinking:
            self.logger.debug(f"Thinking: {thinking}")

        # Update memory if we learned something new
        if response and len(response) > 10:  # Minimal check for meaningful update
            if len(response) > self.memory_limit:
                response = response[:self.memory_limit]
            self.memories[about_agent] = response
        return thinking
    
    def _build_communication_prompt(self, context: Dict, previous_messages: List[Dict]) -> str:
        """Build prompt for communication phase"""
        prompt_parts = [
            self.system_prompt,
            f"\nYour ID: {self.agent_id}",
            f"Opponent ID: {context['opponent_id']}",
            f"\nCurrent Scenario:\n{context['scenario']['description']}",
        ]
        
        if context.get('memory'):
            prompt_parts.append(f"\nYour memory about {context['opponent_id']}:\n{context['memory']}")
        
        if context.get('history'):
            prompt_parts.append(f"\nPrevious rounds with this opponent: {len(context['history'])}")
        
        if previous_messages:
            prompt_parts.append("\nConversation so far:")
            for msg in previous_messages:
                prompt_parts.append(f"{msg['sender']}: {msg['message']}")
        
        prompt_parts.append(
            "\nYou are now speaking DIRECTLY to your opponent. "
            "Your entire response will be sent to them as-is. "
            "Do not include any preamble, narration, or meta-commentary — just write your message."
        )
        
        if self.allow_thinking:
            prompt_parts.append("\nYou may use <thinking>...</thinking> tags for private thoughts.")
        
        return "\n".join(prompt_parts)
    
    def _build_move_prompt(self, context: Dict, messages: List[Dict]) -> str:
        """Build prompt for move decision"""
        game_type = context['scenario']['game_type']
        options = context['scenario']['options']
        
        prompt_parts = [
            self.system_prompt,
            f"\nYour ID: {self.agent_id}",
            f"Opponent ID: {context['opponent_id']}",
            f"\nScenario:\n{context['scenario']['description']}",
            f"\nYour options:",
        ]
        
        for option in options:
            prompt_parts.append(f"- {option}")
        
        if messages:
            prompt_parts.append("\nCommunication phase:")
            for msg in messages:
                prompt_parts.append(f"{msg['sender']}: {msg['message']}")
        
        if context.get('history'):
            # Show summary of past interactions
            prompt_parts.append(f"\nYou have played {len(context['history'])} previous rounds with this opponent.")
            recent = context['history'][-3:] if len(context['history']) > 3 else context['history']
            for round_data in recent:
                prompt_parts.append(
                    f"Round {round_data['round']}: "
                    f"You chose {round_data['moves'].get(self.agent_id, 'unknown')}, "
                    f"they chose {round_data['moves'].get(context['opponent_id'], 'unknown')}"
                )
        
        prompt_parts.append(f"\nChoose one option from: {', '.join(options)}")
        prompt_parts.append("Respond with ONLY your choice, no explanation.")
        
        if self.allow_thinking:
            prompt_parts.append("You may use <thinking>...</thinking> tags for private thoughts before your choice.")
        
        return "\n".join(prompt_parts)
    
    def _build_memory_update_prompt(self, opponent_id: str, pairing_history: List[Dict]) -> str:
        """Build prompt for memory update"""
        prompt_parts = [
            self.system_prompt,
            f"\nYou just finished playing with {opponent_id}.",
            f"Total rounds played: {len(pairing_history)}",
            "\nSummary of interactions:"
        ]
        
        for round_data in pairing_history:
            prompt_parts.append(
                f"Round {round_data['round']} ({round_data['game_type']}): "
                f"You chose {round_data['moves'].get(self.agent_id)}, "
                f"they chose {round_data['moves'].get(opponent_id)}, "
                f"your payoff: {round_data['payoffs'].get(self.agent_id)}"
            )
        
        if opponent_id in self.memories:
            prompt_parts.append(f"\nYour previous memory about {opponent_id}:")
            prompt_parts.append(self.memories[opponent_id])
        
        prompt_parts.append(
            f"\nWrite a brief memory note about {opponent_id} based on this interaction. "
            f"Focus on their play style, trustworthiness, and any patterns you noticed. "
            f"Maximum {self.memory_limit} characters."
        )

        if self.allow_thinking:
            prompt_parts.append("\nYou may use <thinking>...</thinking> tags for private thoughts.")

        return "\n".join(prompt_parts)
    
    def _build_gossip_prompt(self, about_agent: str, to_agent: str) -> str:
        """Build prompt for generating gossip"""
        prompt_parts = [
            self.system_prompt,
            f"\nYou have the opportunity to share information about {about_agent} with {to_agent}.",
            f"\nYour memory about {about_agent}:",
            self.memories.get(about_agent, "No prior interactions"),
            f"\nYou are now speaking DIRECTLY to {to_agent}. "
            f"Your entire response will be sent to them as-is. "
            f"Do not include any preamble, narration, or meta-commentary — just write what you want to say about {about_agent}.",
            "Keep it brief and consider your strategic goals.",
            "You may choose to be honest, deceptive, or decline to share."
        ]

        if self.allow_thinking:
            prompt_parts.append("\nYou may use <thinking>...</thinking> tags for private thoughts.")

        return "\n".join(prompt_parts)
    
    def _build_gossip_processing_prompt(self, from_agent: str, about_agent: str, gossip: str) -> str:
        """Build prompt for processing received gossip"""
        prompt_parts = [
            self.system_prompt,
            f"\n{from_agent} told you about {about_agent}:",
            f'"{gossip}"',
            f"\nYour current memory about {about_agent}:",
            self.memories.get(about_agent, "No prior interactions"),
            f"\nBased on this gossip and considering {from_agent}'s potential motivations,",
            f"update your memory about {about_agent}. Be skeptical of potentially biased information.",
            f"Maximum {self.memory_limit} characters."
        ]

        if self.allow_thinking:
            prompt_parts.append("\nYou may use <thinking>...</thinking> tags for private thoughts.")

        return "\n".join(prompt_parts)
    
    def _call_llm(self, prompt: str, call_type: str) -> Tuple[Optional[str], str]:
        """Make API call to OpenAI and parse response"""
        self.stats['api_calls'] += 1
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] {call_type} prompt: {prompt[:200]}...")
            if call_type == "move_decision":
                return None, "cooperate"  # Default move for dry run
            return None, f"[Dry run response for {call_type}]"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=4096
            )

            full_response = response.choices[0].message.content
            
            # Extract thinking if present
            thinking_match = re.search(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
            thinking = thinking_match.group(1) if thinking_match else None
            
            # Remove thinking tags from response
            clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
            if not clean_response and thinking:
                clean_response = thinking.strip()

            return thinking, clean_response
            
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            if call_type == "move_decision":
                return None, "cooperate"  # Safe default
            return None, ""
    
    def _extract_move(self, response: str, game_type: str, move_mapping: Optional[Dict] = None) -> str:
        """Extract the actual move from LLM response.

        Checks in order: scenario move_mapping, keyword matching, safe canonical default.
        """
        response_lower = response.lower().strip()

        # First try scenario move_mapping (most reliable - maps option text to canonical moves)
        if move_mapping:
            for option_text, canonical_move in move_mapping.items():
                if option_text.lower() in response_lower:
                    return canonical_move

        # Fall back to keyword matching based on game type
        if game_type == "prisoners_dilemma":
            if any(word in response_lower for word in ['cooperate', 'collaborate', 'trust', 'share']):
                return 'cooperate'
            elif any(word in response_lower for word in ['defect', 'betray', 'compete', 'take']):
                return 'defect'

        elif game_type == "stag_hunt":
            if any(word in response_lower for word in ['stag', 'collaborate', 'team', 'together', 'big']):
                return 'stag'
            elif any(word in response_lower for word in ['hare', 'solo', 'individual', 'safe', 'small']):
                return 'hare'

        elif game_type == "hawk_dove":
            if any(word in response_lower for word in ['hawk', 'aggressive', 'fight', 'attack']):
                return 'hawk'
            elif any(word in response_lower for word in ['dove', 'peaceful', 'yield', 'peace']):
                return 'dove'

        elif game_type == "coordination":
            if any(word in response_lower for word in ['option a', 'a', 'first']):
                return 'option_a'
            elif any(word in response_lower for word in ['option b', 'b', 'second']):
                return 'option_b'

        # Default to a safe canonical move for the game type (never return raw LLM words)
        valid_defaults = {
            'prisoners_dilemma': 'cooperate',
            'stag_hunt': 'stag',
            'hawk_dove': 'dove',
            'coordination': 'option_a'
        }
        self.logger.warning(
            f"Could not extract move from '{response[:100]}' for {game_type}, using default"
        )
        return valid_defaults.get(game_type, 'cooperate')
    
    def get_memory(self, agent_id: str) -> Optional[str]:
        """Get memory about a specific agent"""
        return self.memories.get(agent_id)
    
    def get_all_memories(self) -> Dict[str, str]:
        """Get all memories"""
        return self.memories.copy()
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return self.stats.copy()
