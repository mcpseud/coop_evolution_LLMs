# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM-based game theory simulation system for studying cooperation and competition between AI agents in business scenarios. The system runs multi-agent iterated games where LLM-powered agents communicate, make decisions, maintain memories about other agents, and share reputations through gossip.

## Running the Simulation

### Basic command structure
```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --output results/
```

### Key command-line options
- `--agents`: Path to agent configuration CSV (defines agent strategies and frequencies)
- `--config`: Path to experiment configuration CSV (defines simulation parameters)
- `--output`: Output directory (default: `output/`)
- `--api-key`: OpenAI API key (or use `OPENAI_API_KEY` environment variable)
- `--dry-run`: Test configuration without making API calls
- `--verbose`: Enable detailed debug logging

### Testing without API costs
```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --dry-run
```

## System Architecture

### Core Module Responsibilities

**game_theory_main.py** - Entry point that:
- Parses command-line arguments
- Sets up logging infrastructure
- Orchestrates the overall simulation flow
- Saves final results and summary statistics

**simulation_engine.py** - Core simulation orchestration:
- Creates agent pool based on frequencies in config
- Manages pairings (random selection of two agents)
- Runs multiple rounds per pairing
- Handles game type selection using configured proportions
- Coordinates communication and decision phases
- Manages post-pairing gossip if enabled
- Updates agent memories after each pairing

**agent_class.py** - LLM-powered agent implementation:
- Makes API calls to OpenAI for all agent decisions
- Handles four distinct contexts: communication, move decisions, memory updates, and gossip
- Maintains memory about other agents (character-limited)
- Parses `<thinking>` tags for private reasoning (if enabled)
- Extracts moves from LLM responses using keyword matching
- Tracks statistics (total games, payoffs, strategies used)

**game_manager.py** - Game theory logic:
- Defines payoff matrices for all four game types (Prisoner's Dilemma, Stag Hunt, Hawk-Dove, Coordination)
- Maps various LLM responses to valid game moves
- Validates and normalizes agent moves
- Calculates payoffs for move pairs
- Provides game theory analysis (Nash equilibria, Pareto optimality, social optimum)

**scenarios_manager.py** - Business scenario generation:
- Provides 3 different business contexts per game type
- Translates abstract game theory into realistic business decisions
- Maps business options to game-theoretic moves
- Randomizes scenario selection to prevent pattern recognition

**config_loader.py** - Configuration management:
- Loads agent configurations from CSV (strategy name, system prompt, model, frequency)
- Loads experiment parameters from CSV
- Parses game proportions (e.g., "pd:40,sh:25,hd:20,coord:15")
- Provides sensible defaults for missing parameters
- Can generate template CSV files

**data_logger.py** - Comprehensive logging:
- Logs to 6 separate CSV files: moves, communications, thinking, memories, gossip, payoffs
- Maintains complete JSON log of all pairings
- Generates summary statistics
- Supports exporting data for analysis

### Simulation Flow

1. **Initialization**: Load agent configs and experiment params, create agent pool based on frequencies
2. **Pairing Loop**: For each of `total_pairings` iterations:
   - Randomly select two agents
   - Determine number of rounds (fixed or Poisson-distributed)
   - Determine game type(s) based on `game_varies_across_pairings` setting
3. **Round Execution**: For each round in a pairing:
   - Select business scenario for the game type
   - **Communication Phase**: Agents exchange messages (up to `max_communication_rounds`)
   - **Decision Phase**: Both agents make moves simultaneously
   - Calculate payoffs using game theory matrices
   - Record all interactions
4. **Memory Update**: After all rounds in a pairing, both agents update their memories about each other
5. **Gossip Phase** (if enabled): Agents randomly share information about their recent opponent with other agents
6. **Finalization**: Generate summary statistics and save all logs

## Configuration Files

### Agent Configuration CSV Structure
```csv
strategy_name,system_prompt,model,frequency
```
- `strategy_name`: Identifier (e.g., "Tit-for-Tat", "Always Cooperate")
- `system_prompt`: Behavioral instructions for the LLM
- `model`: OpenAI model (e.g., "gpt-4", "gpt-3.5-turbo")
- `frequency`: Number of agents of this type to create

The system prompt is critical - it defines agent behavior. Classic strategies (Tit-for-Tat, Grim Trigger, Pavlov, etc.) are implemented through prompting, not hard-coded logic.

### Experiment Configuration CSV Structure
```csv
parameter,value,description
```

Key parameters:
- `avg_rounds`: Average rounds per pairing (exact if `rounds_fixed=true`, mean of Poisson if `false`)
- `total_pairings`: Total number of agent pairings to run
- `game_proportions`: Relative frequency of game types (format: "pd:40,sh:25,hd:20,coord:15")
- `game_varies_across_pairings`: If true, game type is constant within a pairing; if false, varies per round
- `allow_gossip`: Enable reputation sharing between agents
- `memory_limit`: Max characters for memories about each agent
- `max_communication_rounds`: Number of back-and-forth messages before decisions
- `allow_thinking`: Enable `<thinking>` tags for private agent reasoning

## Game Types and Move Mappings

The system supports four classic game theory scenarios:

**Prisoner's Dilemma**: `cooperate` vs `defect`
- Business contexts: price competition, R&D sharing, supplier contracts
- Keywords mapped to cooperate: trust, collaborate, share
- Keywords mapped to defect: betray, compete, take

**Stag Hunt**: `stag` vs `hare`
- Business contexts: joint ventures, industry standards, market expansion
- Keywords for stag: team, together, big
- Keywords for hare: solo, safe, small

**Hawk-Dove**: `hawk` vs `dove`
- Business contexts: patent disputes, territory conflicts, talent acquisition
- Keywords for hawk: fight, aggressive, attack
- Keywords for dove: peace, yield, share

**Coordination**: `option_a` vs `option_b`
- Business contexts: technology platforms, scheduling systems, trade shows
- Keywords for option_a: a, first
- Keywords for option_b: b, second

## Important Implementation Details

### Move Extraction Logic
The `agent_class.py` module extracts moves from LLM responses using keyword matching (see `_extract_move()` method). If no keywords match, it defaults to the first word of the response or `'cooperate'`. This can be fragile - test agent prompts carefully.

### Memory Management
Memories are stored per-agent as a dictionary `{opponent_id: memory_text}`. After each pairing, agents generate updated memories by calling the LLM with the full pairing history. Memories are truncated to `memory_limit` characters.

### Gossip Mechanism
After a pairing, each agent has a 50% chance to gossip to a randomly selected third agent about their recent opponent. The receiving agent processes gossip skeptically (prompted to consider sender's motivations).

### API Call Patterns
Each simulation makes numerous OpenAI API calls:
- Communication: up to `max_communication_rounds * 2` per round
- Decisions: 2 per round
- Memory updates: 2 per pairing
- Gossip: variable (50% chance per agent after each pairing)

Use `--dry-run` for testing to avoid costs.

### File Naming Conventions
- Main entry point: `game_theory_main.py` (NOT `main.py` as referenced in README)
- Agent module: `agent_class.py` (NOT `agent.py` as referenced in README)
- Scenario module: `scenarios_manager.py` (NOT `scenarios.py` as referenced in README)
- All other modules match README references

## Output Files

All outputs are timestamped with format `YYYYMMDD_HHMMSS`:

**CSV logs** (one row per event):
- `moves_{timestamp}.csv` - All decisions made
- `communications_{timestamp}.csv` - All messages exchanged
- `thinking_{timestamp}.csv` - Private agent reasoning (if enabled)
- `memories_{timestamp}.csv` - Memory updates after pairings
- `gossip_{timestamp}.csv` - Reputation information shared
- `payoffs_{timestamp}.csv` - Outcomes for each round

**JSON files**:
- `results_{timestamp}.json` - High-level summary statistics
- `complete_log_{timestamp}.json` - Structured record of all pairings
- `summary_{timestamp}.json` - Statistical analysis of moves by game type
- `simulation_{timestamp}.log` - System logs

## Extending the System

### Adding New Game Types
1. Add payoff matrix to `game_manager.py` `payoff_matrices` dict
2. Add valid moves to `valid_moves` dict
3. Update `_map_to_valid_move()` with keyword mappings
4. Create 2-3 business scenarios in `scenarios_manager.py`
5. Update game proportion parsing in `config_loader.py` if using abbreviation

### Adding New Scenarios
Add to the appropriate list in `scenarios_manager.py` with required fields:
- `name`: Short identifier
- `description`: Full business context
- `options`: List of choices presented to agents
- `move_mapping`: Dict mapping option text to game-theoretic moves

### Modifying Agent Strategies
Edit system prompts in the agents CSV file. The LLM behavior is entirely prompt-driven. Include guidance about:
- General philosophy (cooperative, competitive, adaptive)
- How to use history and context
- Response to betrayal or cooperation
- Communication strategy
