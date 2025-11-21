#!/usr/bin/env python3
"""
LLM Game Theory Simulation System
Main entry point for running multi-agent game theory experiments
"""

import argparse
import logging
import json
import os
from datetime import datetime
from pathlib import Path

from simulation_engine import SimulationEngine
from config_loader import ConfigLoader
from data_logger import DataLogger


def setup_logging(output_dir):
    """Set up logging configuration"""
    log_file = output_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM Game Theory Simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python main.py --agents agents.csv --config experiment_config.csv --output results/
  
For more information, see README.md
        """
    )
    
    parser.add_argument(
        '--agents', 
        type=str, 
        required=True,
        help='Path to CSV file containing agent configurations'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        required=True,
        help='Path to CSV file containing experiment configuration'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='output',
        help='Directory for output files (default: output)'
    )
    
    parser.add_argument(
        '--api-key', 
        type=str, 
        help='OpenAI API key (can also be set via OPENAI_API_KEY environment variable)'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Run simulation without making API calls (for testing)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    logger = setup_logging(output_dir)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting LLM Game Theory Simulation")
    logger.info(f"Agent config: {args.agents}")
    logger.info(f"Experiment config: {args.config}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Load configurations
        config_loader = ConfigLoader()
        agents_config = config_loader.load_agents(args.agents)
        experiment_config = config_loader.load_experiment(args.config)
        
        logger.info(f"Loaded {len(agents_config)} agent configurations")
        logger.info(f"Experiment configuration: {json.dumps(experiment_config, indent=2)}")
        
        # Initialize data logger
        data_logger = DataLogger(output_dir)
        
        # Create simulation engine
        simulation = SimulationEngine(
            agents_config=agents_config,
            experiment_config=experiment_config,
            data_logger=data_logger,
            api_key=args.api_key,
            dry_run=args.dry_run
        )
        
        # Run simulation
        logger.info("Starting simulation...")
        results = simulation.run()
        
        # Save final results
        results_file = output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Simulation complete! Results saved to {results_file}")
        logger.info(f"Detailed logs available in {output_dir}")
        
        # Print summary statistics
        print("\n=== Simulation Summary ===")
        print(f"Total pairings: {results['total_pairings']}")
        print(f"Total rounds played: {results['total_rounds']}")
        print(f"Total API calls: {results['total_api_calls']}")
        print(f"Cooperation rate: {results['cooperation_rate']:.2%}")
        print("\nDetailed results and logs saved to:", output_dir)
        
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
