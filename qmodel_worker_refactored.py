#!/usr/bin/env python3
"""
Refactored QModel Worker
========================

A clean, modular worker for processing spike sorting jobs.
This worker polls the API for jobs and processes them step by step.

Usage:
    python qmodel_worker_refactored.py [--environment ENV]
    
Arguments:
    --environment: Environment to run in (local, production, localhost_https)
                  Default: production

Examples:
    python qmodel_worker_refactored.py --environment local
    python qmodel_worker_refactored.py --environment production
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.constants import Environment, WorkerConfig
from services.worker_service import WorkerService


def setup_logging():
    """Configure logging for the worker"""
    logging.basicConfig(
        level=getattr(logging, WorkerConfig.LOG_LEVEL),
        format=WorkerConfig.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Optionally add file handler
            # logging.FileHandler('worker.log')
        ]
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="QModel Worker - Process spike sorting jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --environment local       # Run against local development server
  %(prog)s --environment production  # Run against production server (default)
  %(prog)s --single                  # Process one job and exit
        """
    )
    
    parser.add_argument(
        "--environment", "-e",
        choices=[Environment.LOCAL, Environment.PRODUCTION, Environment.LOCALHOST_HTTPS],
        default=Environment.PRODUCTION,
        help="Environment to run worker in (default: production)"
    )
    
    parser.add_argument(
        "--single", "-s",
        action="store_true",
        help="Process a single job and exit (useful for testing)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the worker"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and configure worker service
        worker = WorkerService(environment=args.environment)
        
        # Log startup information
        status = worker.get_status()
        logger.info("="*60)
        logger.info("QModel Worker Starting")
        logger.info("="*60)
        logger.info(f"Environment: {status['environment']}")
        logger.info(f"API URL: {status['api_url']}")
        logger.info(f"SSL Verify: {status['ssl_verify']}")
        logger.info(f"Polling Interval: {status['polling_interval']} seconds")
        logger.info("="*60)
        
        if args.single:
            # Process a single job and exit
            logger.info("Single job mode - processing one job and exiting")
            success = worker.process_single_job()
            if success:
                logger.info("Single job processed successfully")
                sys.exit(0)
            else:
                logger.info("No job processed")
                sys.exit(1)
        else:
            # Start continuous processing
            logger.info("Starting continuous job processing...")
            logger.info("Press Ctrl+C to stop")
            worker.start()
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
