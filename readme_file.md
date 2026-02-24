# LLM Game Theory Simulation System

A comprehensive system for running game theory experiments with Large Language Models (LLMs) in business contexts. This system allows multiple AI agents to play iterated games, communicate, build reputations, and develop strategies over time.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [System Architecture](#system-architecture)
5. [Configuration Files](#configuration-files)
6. [Game Types](#game-types)
7. [Running Simulations](#running-simulations)
8. [Understanding Output](#understanding-output)
9. [Analyzing Results](#analyzing-results)
10. [Customization](#customization)
11. [Troubleshooting](#troubleshooting)

## Overview

This system simulates strategic interactions between LLM-based agents in business scenarios. Key features include:

- **Multiple Game Types**: Prisoner's Dilemma, Stag Hunt, Hawk-Dove, and Coordination games
- **Business Scenarios**: Each game is presented as a realistic business situation
- **Communication**: Agents can communicate before making decisions
- **Memory & Learning**: Agents maintain memories about past interactions
- **Reputation System**: Agents can share information (gossip) about others
- **Private Thinking**: Agents can use `<thinking>` tags for reasoning
- **Comprehensive Logging**: All interactions, decisions, and thoughts are recorded

## Installation

### Prerequisites

- Python 3.7 or higher
- OpenAI API key

### Step 1: Install Dependencies

```bash
pip install openai numpy
```

### Step 2: Set Up Your OpenAI API Key

Either set an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or pass it as a command-line argument when running simulations.

### Step 3: Download the Simulation Files

Place all the Python files in a directory:
- `game_theory_main.py`
- `simulation_engine.py`
- `agent_class.py`
- `game_manager.py`
- `scenarios_manager.py`
- `config_loader.py`
- `data_logger.py`

## Quick Start

1. **Use the provided example configuration files**:
   - `example_agents_csv.csv` - Defines different agent strategies
   - `example_experiment_csv.csv` - Sets experiment parameters

2. **Run your first simulation**:

```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --output my_first_run/
```

3. **Check the results** in the `my_first_run/` directory

## System Architecture

The system consists of several modular components:

### Core Components

1. **game_theory_main.py**: Entry point, handles command-line arguments
2. **simulation_engine.py**: Orchestrates the simulation
3. **agent_class.py**: Implements LLM-based agents with memory and communication
4. **game_manager.py**: Handles game logic and payoff calculations
5. **scenarios_manager.py**: Provides business contexts for games
6. **config_loader.py**: Loads configuration from CSV files
7. **data_logger.py**: Records all simulation data

### How It Works

1. Agents are created based on configuration
2. For each pairing:
   - Two agents are randomly selected
   - They play multiple rounds of games
   - Each round includes:
     - Scenario presentation
     - Communication phase
     - Decision phase
     - Payoff calculation
   - Agents update memories after pairing
   - Gossip may occur between agents
3. All data is logged for analysis

## Configuration Files

### agents.csv

Defines the agent strategies and their properties:

```csv
strategy_name,system_prompt,model,frequency
Tit-for-Tat,"You mirror your partner's previous action...",gpt-4.1-nano,3
Always Cooperate,"You always seek mutual benefit...",gpt-4.1-nano,2
```

- **strategy_name**: Identifier for the strategy
- **system_prompt**: Instructions that define agent behavior
- **model**: OpenAI model to use (e.g., gpt-4.1-nano, gpt-4.1-mini)
- **frequency**: How many agents of this type to create

### experiment_config.csv

Controls experiment parameters:

```csv
parameter,value,description
avg_rounds,10,Average rounds per pairing
rounds_fixed,false,Fixed or stochastic (Poisson)
total_pairings,200,Number of pairings to run
allow_gossip,true,Enable reputation sharing
memory_limit,500,Max characters for memories
```

Key parameters:
- **avg_rounds**: Average number of games per pairing
- **rounds_fixed**: If false, uses Poisson distribution
- **game_proportions**: Relative frequency of each game type
- **allow_thinking**: Enables private reasoning

## Game Types

### 1. Prisoner's Dilemma
- **Scenario Example**: Price competition between firms
- **Options**: Cooperate (maintain prices) vs Defect (cut prices)
- **Dilemma**: Individual incentive to defect, but mutual cooperation is better

### 2. Stag Hunt
- **Scenario Example**: Joint venture investment
- **Options**: Stag (risky collaboration) vs Hare (safe solo option)
- **Dilemma**: High reward requires mutual trust

### 3. Hawk-Dove
- **Scenario Example**: Patent dispute
- **Options**: Hawk (aggressive) vs Dove (peaceful)
- **Dilemma**: Aggression pays unless both are aggressive

### 4. Coordination
- **Scenario Example**: Technology platform choice
- **Options**: Option A vs Option B
- **Dilemma**: Success requires choosing the same option

## Running Simulations

### Basic Usage

```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --output results/
```

### Command-Line Options

- `--agents`: Path to agent configuration CSV (required)
- `--config`: Path to experiment configuration CSV (required)
- `--output`: Output directory for results (default: output/)
- `--api-key`: OpenAI API key (optional if set as environment variable)
- `--dry-run`: Run without API calls for testing
- `--verbose`: Enable detailed logging

### Dry Run Mode

Test your configuration without using API credits:

```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --dry-run
```

## Understanding Output

The system generates several output files:

### Log Files

1. **moves_[timestamp].csv**: All game decisions
2. **communications_[timestamp].csv**: Messages between agents
3. **thinking_[timestamp].csv**: Private agent thoughts
4. **memories_[timestamp].csv**: Memory updates
5. **gossip_[timestamp].csv**: Reputation information shared
6. **payoffs_[timestamp].csv**: Game outcomes

### Summary Files

- **results_[timestamp].json**: High-level statistics
- **complete_log_[timestamp].json**: Structured complete record
- **summary_[timestamp].json**: Statistical summary

### Example Output Analysis

```python
import pandas as pd

# Read move data
moves = pd.read_csv('output/moves_20240115_120000.csv')

# Analyze cooperation rates by strategy
cooperation_rate = moves[moves['move'].isin(['cooperate', 'share', 'stag', 'dove'])].groupby('agent_id').size() / moves.groupby('agent_id').size()
```

## Analyzing Results

### Key Metrics to Track

1. **Cooperation Rate**: Frequency of cooperative moves
2. **Average Payoffs**: By strategy and game type
3. **Strategy Dynamics**: How behaviors change over time
4. **Communication Patterns**: What agents say before decisions
5. **Reputation Effects**: Impact of gossip on behavior

### Sample Analysis Script

```python
import json
import pandas as pd

# Load results
with open('output/results_20240115_120000.json', 'r') as f:
    results = json.load(f)

print(f"Total pairings: {results['total_pairings']}")
print(f"Cooperation rate: {results['cooperation_rate']:.2%}")

# Analyze by game type
for game, moves in results['moves_by_game'].items():
    print(f"\n{game}:")
    for move_pair, count in moves.items():
        print(f"  {move_pair}: {count}")
```

## Customization

### Adding New Scenarios

Edit `scenarios_manager.py` to add business scenarios:

```python
new_scenario = {
    'name': 'Merger Negotiation',
    'description': 'Two companies considering a merger...',
    'options': ['propose merger', 'stay independent'],
    'move_mapping': {'propose merger': 'cooperate', 'stay independent': 'defect'}
}
```

### Creating New Agent Strategies

Add new rows to your agents.csv:

```csv
strategy_name,system_prompt,model,frequency
Cautious Cooperator,"You prefer cooperation but need to see consistent good faith...",gpt-4.1-nano,2
```

### Modifying Game Payoffs

Edit `game_manager.py` to adjust payoff matrices:

```python
self.payoff_matrices['prisoners_dilemma'] = {
    ('cooperate', 'cooperate'): (3, 3),
    ('cooperate', 'defect'): (0, 5),
    # etc.
}
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key required"**
   - Set the OPENAI_API_KEY environment variable
   - Or use `--api-key` parameter

2. **"Agent configuration file not found"**
   - Check file paths are correct
   - Ensure CSV files are in the specified location

3. **High API costs**
   - Use `--dry-run` for testing
   - Reduce `total_pairings` in configuration
   - Use a smaller model like gpt-4.1-nano

4. **Agents not behaving as expected**
   - Review system prompts in agents.csv
   - Check if `allow_thinking` is enabled
   - Examine thinking logs for reasoning

### Debug Mode

Run with verbose logging:

```bash
python game_theory_main.py --agents example_agents_csv.csv --config example_experiment_csv.csv --verbose
```

### Getting Help

1. Check log files for detailed error messages
2. Review the simulation_[timestamp].log file
3. Ensure all Python files are in the same directory
4. Verify CSV files have correct headers

## Tips for Effective Experiments

1. **Start Small**: Begin with few pairings to test configurations
2. **Use Dry Run**: Test setups without API calls
3. **Monitor Costs**: Make sure you are using the correct models
4. **Iterate Prompts**: Agent behavior depends heavily on system prompts
5. **Analyze Patterns**: Look for emergent behaviors across many pairings
6. **Compare Strategies**: Run same configuration multiple times for statistical significance

## Contributing to Research

This system is designed for research on AI cooperation and competition. When running experiments:

1. Document your hypotheses
2. Save configuration files with your results
3. Note interesting emergent behaviors
4. Share insights about effective prompting strategies
5. Consider how findings might apply to real-world AI deployment

Remember: The goal is to understand how AI agents might interact in economic settings and develop insights for beneficial AI integration into society.

---

For questions or issues, please refer to the code documentation or create detailed logs using the `--verbose` flag.