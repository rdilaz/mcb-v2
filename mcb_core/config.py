"""
MCB Configuration Module
Centralized configuration and constants for the MCB application.
Based on app_production.py for production-ready settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========================================
# CORE APPLICATION CONFIGURATION
# ========================================

# Engine Configuration
STOCKFISH_PATH = os.environ.get('STOCKFISH_PATH', "stockfish")
BLUNDER_THRESHOLD = 10
ENGINE_THINK_TIME = 0.08  # Changed to balanced for better accuracy

# Batch Engine Analysis Configuration
ENABLE_BATCH_ENGINE_ANALYSIS = True
BATCH_ANALYSIS_SIZE = 20  # Positions per batch

# Position Filtering Thresholds (Step 1.2 Enhancement)
SKIP_FORCED_MOVES = True
SKIP_BOOK_MOVES = True
SKIP_OBVIOUS_RECAPTURES = True
SKIP_TABLEBASE_POSITIONS = True
TABLEBASE_PIECE_LIMIT = 6

# Lazy Evaluation Thresholds (Step 1.3 Enhancement)
MIN_EVAL_DROP_FOR_ANALYSIS = 50  # Centipawns
EXPENSIVE_CHECK_THRESHOLD = 25    # Win probability drop % before running expensive checks (increased to reduce trap detection)

# Game Analysis Settings
GAMES_TO_FETCH = 1
MAX_GAMES_ALLOWED = 100  # Hard cap to prevent server overload
DAILY_GAME_LIMIT = 200   # Games per user per day

# Analysis Depth Mapping
# Keys into analyze_games.get_engine_limit(), which converts these legacy
# think-time values into adaptive depth + time-cap engine limits:
#   fast     -> depth 10, capped at 150ms
#   balanced -> depth 12, capped at 250ms
#   deep     -> depth 15, capped at 500ms
ANALYSIS_DEPTH_MAPPING = {
    'fast': 0.05,
    'balanced': 0.08,
    'deep': 0.12
}

# ========================================
# PRODUCTION SECURITY CONFIGURATION
# ========================================

# Flask Security Settings
SECURITY_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'your-secret-key-change-this'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max
}

# Rate Limiting Configuration
RATE_LIMITS = {
    'default': ["200 per day", "50 per hour"],
    'analysis': "5 per minute"  # Rate limit analysis requests
}

# CORS Configuration
CORS_CONFIG = {
    'production_origins': [os.environ.get('ALLOWED_ORIGIN', 'https://yourdomain.com')],
    'development_origins': ['*']  # Allow all origins for development
}

# HTTPS Configuration
HTTPS_ENFORCEMENT = os.environ.get('HTTPS_ENFORCEMENT', 'False').lower() == 'true'

# Timeout Configuration
ANALYSIS_TIMEOUT = 300  # 5 minute timeout
MAX_CONCURRENT_SESSIONS = 10  # Max concurrent analyses

# ========================================
# USERNAME VALIDATION CONFIGURATION
# ========================================

# Chess.com username validation pattern
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,25}$'

# Dangerous patterns to reject (SQL injection prevention)
DANGEROUS_PATTERNS = ['drop', 'select', 'insert', 'delete', 'update', 'union', '--', ';']

# ========================================
# BLUNDER ANALYSIS CONSTANTS
# ========================================

# Blunder Category Priority (for sorting and processing)
BLUNDER_CATEGORY_PRIORITY = {
    "Allowed Checkmate": 1,
    "Missed Checkmate": 2,
    "Hanging a Piece": 3,  # Moved up - hanging pieces are more critical
    "Allowed Winning Exchange for Opponent": 4,  # NEW CATEGORY
    "Allowed Fork": 5,
    "Missed Fork": 6,
    "Allowed Discovered Attack": 7,  # NEW CATEGORY
    "Missed Discovered Attack": 8,  # NEW CATEGORY
    "Losing Exchange": 9,
    "Missed Material Gain": 10,
    "Allowed Opportunity to Pressure Pinned Piece": 11,  # NEW CATEGORY
    "Missed Opportunity to Pressure Pinned Piece": 12,  # NEW CATEGORY
    "Allowed Pin": 13,
    "Missed Pin": 14,  # Moved down - pins are less critical than hanging pieces
    "Mistake": 15
}

# Chess Piece Values (in centipawns)
PIECE_VALUES = {
    1: 100,   # chess.PAWN
    2: 300,   # chess.KNIGHT
    3: 320,   # chess.BISHOP
    4: 500,   # chess.ROOK
    5: 900,   # chess.QUEEN
    6: 10000  # chess.KING
}

# Piece Names for Display
PIECE_NAMES = {
    1: "Pawn",
    2: "Knight", 
    3: "Bishop",
    4: "Rook",
    5: "Queen",
    6: "King"
}

# Category Weights for Severity Scoring (Production values)
CATEGORY_WEIGHTS = {
    "Allowed Checkmate": 3.0,
    "Missed Checkmate": 3.0,
    "Hanging a Piece": 2.5,  # Reduced from 3.0
    "Allowed Winning Exchange for Opponent": 1.8,  # NEW
    "Allowed Fork": 2.0,
    "Missed Fork": 2.0,
    "Allowed Discovered Attack": 2.2,  # NEW
    "Missed Discovered Attack": 2.0,  # NEW
    "Losing Exchange": 2.0,
    "Allowed Pin": 1.5,
    "Missed Pin": 1.5,
    "Missed Material Gain": 1.8,
    "Allowed Opportunity to Pressure Pinned Piece": 1.7,  # NEW
    "Missed Opportunity to Pressure Pinned Piece": 1.6,  # NEW
    "Mistake": 1.0
}

# Base Impact Values for Categories (Production tuned)
BASE_IMPACT_VALUES = {
    'Allowed Checkmate': 45.0,
    'Missed Checkmate': 40.0,
    'Hanging a Piece': 30.0,  # Reduced from 35.0
    'Allowed Winning Exchange for Opponent': 20.0,  # NEW
    'Allowed Fork': 20.0,
    'Missed Fork': 18.0,
    'Allowed Discovered Attack': 22.0,  # NEW
    'Missed Discovered Attack': 18.0,  # NEW
    'Losing Exchange': 15.0,
    'Missed Material Gain': 12.0,
    'Allowed Opportunity to Pressure Pinned Piece': 14.0,  # NEW
    'Missed Opportunity to Pressure Pinned Piece': 12.0,  # NEW
    'Allowed Pin': 10.0,
    'Missed Pin': 8.0,
    'Mistake': 15.0
}

# Educational descriptions for blunder categories (Production version)
BLUNDER_EDUCATIONAL_DESCRIPTIONS = {
    'Hanging a Piece': 'You left pieces undefended, allowing your opponent to capture them for free. Always check if your pieces are safe after making a move.',
    'Allowed Winning Exchange for Opponent': 'You left pieces in positions where they could be captured with a favorable exchange for your opponent. While the piece was defended, the sequence of captures would result in material loss.',  # NEW
    'Missed Fork': 'You missed opportunities to attack two or more enemy pieces simultaneously with a single piece, forcing your opponent to lose material.',
    'Allowed Fork': 'Your move allowed your opponent to attack multiple pieces at once, forcing you to lose material. Look ahead to see if your moves give your opponent tactical opportunities.',
    'Allowed Discovered Attack': 'Your move allowed your opponent to create a discovered attack, where moving one piece reveals an attack from another piece behind it, often winning material.',  # NEW
    'Missed Discovered Attack': 'You missed opportunities to create discovered attacks by moving a piece to reveal an attack from another piece, potentially winning material.',  # NEW
    'Missed Material Gain': 'You missed chances to win material through captures or tactical sequences. Look for opportunities to win pieces or pawns.',
    'Losing Exchange': 'You initiated exchanges that lost you material overall. Calculate the value of pieces being traded before making exchanges.',
    'Allowed Opportunity to Pressure Pinned Piece': 'Your move allowed your opponent to add pressure to one of your pinned pieces, potentially winning material through tactical sequences.',  # NEW
    'Missed Opportunity to Pressure Pinned Piece': 'You missed opportunities to add pressure to your opponent\'s pinned pieces, potentially winning material through tactical pressure.',  # NEW
    'Missed Pin': 'You missed opportunities to pin enemy pieces, restricting their movement and creating tactical advantages.',
    'Allowed Pin': 'Your move allowed your opponent to pin one of your pieces, limiting your options and creating weaknesses in your position.',
    'Allowed Checkmate': 'Your move gave your opponent a forced checkmate sequence. Always check if your moves leave your king vulnerable.',
    'Missed Checkmate': 'You missed opportunities to deliver checkmate. Look for forcing moves that can lead to mate.',
    'Mistake': 'This move significantly worsened your position or missed a better alternative. Review the position to understand what went wrong.'
}

# General descriptions for blunder categories (for hero stat)
BLUNDER_GENERAL_DESCRIPTIONS = {
    "Allowed Checkmate": "You played moves that allowed your opponent to deliver checkmate when it could have been avoided.",
    "Missed Checkmate": "You had opportunities to checkmate your opponent but played different moves instead.", 
    "Allowed Fork": "Your moves allowed your opponent to fork (attack multiple pieces simultaneously) with a single piece.",
    "Missed Fork": "You missed chances to fork your opponent's pieces, potentially winning material or gaining tactical advantage.",
    "Allowed Discovered Attack": "Your moves allowed your opponent to create discovered attacks, where moving one piece reveals an attack from another.",  # NEW
    "Missed Discovered Attack": "You missed opportunities to create discovered attacks by moving pieces to reveal attacks from other pieces.",  # NEW
    "Allowed Pin": "You positioned your pieces in ways that allowed your opponent to pin them (restrict their movement by attacking through them to more valuable pieces).",
    "Missed Pin": "You overlooked opportunities to pin your opponent's pieces, missing tactical advantages.",
    "Hanging a Piece": "You left pieces undefended, allowing your opponent to capture them for free or with favorable exchanges.",
    "Allowed Winning Exchange for Opponent": "You positioned pieces where capturing them would win material for your opponent through a series of exchanges.",  # NEW
    "Allowed Opportunity to Pressure Pinned Piece": "Your moves allowed your opponent to add tactical pressure to your pinned pieces, potentially winning material.",  # NEW
    "Missed Opportunity to Pressure Pinned Piece": "You missed chances to add pressure to your opponent's pinned pieces, overlooking tactical opportunities.",  # NEW
    "Losing Exchange": "You initiated trades that resulted in losing more material value than you gained.",
    "Missed Material Gain": "You missed opportunities to capture opponent pieces or win material through tactical sequences.",
    "Mistake": "You made moves that significantly worsened your position according to engine evaluation."
}

# ========================================
# FLASK APPLICATION SETTINGS
# ========================================

# Development Settings
DEBUG_MODE = os.environ.get('FLASK_ENV') != 'production'
PORT = int(os.environ.get('PORT', 5000))

# ========================================
# PROGRESS TRACKING CONFIGURATION  
# ========================================

# Time-weighted progress phases (in seconds) - Production optimized
PROGRESS_PHASE_WEIGHTS = {
    "starting": 0.5,
    "fetching_games": 2.0,
    "engine_init": 0.5, 
    "reading_pgn": 0.2,
    "analyzing_games": 8.0,  # Will be multiplied by game count
    "aggregating": 0.3
}

# Progress Queue Settings
PROGRESS_QUEUE_MAX_SIZE = 50
PROGRESS_HEARTBEAT_TIMEOUT = 30

# ========================================
# PERFORMANCE OPTIMIZATION SETTINGS
# ========================================

# Speed optimization settings
ESTIMATED_MOVES_PER_GAME = 35  # Average chess game length
SPEED_OPTIMIZATION_ENABLED = True

# Speed optimization descriptions for user feedback
OPTIMIZATION_DESCRIPTIONS = {
    'fast': {
        'mode': 'Fast',
        'speed_gain': '2-4x faster'
    },
    'balanced': {
        'mode': 'Balanced', 
        'speed_gain': '1.5-2.5x faster'
    },
    'deep': {
        'mode': 'Deep',
        'speed_gain': '1.5x faster'
    }
}

# Parallel Processing Configuration
#
# IMPORTANT: parallelism is OPT-IN and defaults to sequential (1 worker).
# Each worker runs its own Stockfish process; running more workers than the
# instance has vCPUs makes the engines fight over one core and can stall a
# request until timeouts fire (the classic "hangs on Cloud Run" failure).
# Container CPU counts are unreliable (os.cpu_count() often reports host cores),
# so we do NOT auto-detect. Instead, set MCB_ANALYSIS_WORKERS to match the
# vCPUs you actually allocate:
#   - 1 vCPU Cloud Run instance (default)      -> leave at 1  (sequential)
#   - bump the service to N vCPUs              -> set MCB_ANALYSIS_WORKERS=N
PARALLEL_PROCESSING_ENABLED = True
PARALLEL_GAME_WORKERS = max(1, int(os.environ.get('MCB_ANALYSIS_WORKERS', '1')))
PARALLEL_MIN_GAMES = 4             # Use the parallel path at/above this many games (only when workers > 1)
PARALLEL_MOVE_WORKERS = 2          # Number of concurrent move analysis workers per game
# Pool holds one engine per worker (min 2 so the single-worker path can still
# reuse a warmed engine across requests).
ENGINE_POOL_SIZE = max(2, PARALLEL_GAME_WORKERS)
ENGINE_HASH_MB = int(os.environ.get('MCB_ENGINE_HASH_MB', '32'))  # Stockfish TT size per engine (MB)
GAME_BATCH_SIZE = 10               # Max games per batch for parallel processing
MEMORY_STREAMING_ENABLED = False   # Disable streaming for stability - collect in memory instead

# Performance Monitoring
PERFORMANCE_LOGGING_ENABLED = True
PROGRESS_UPDATE_INTERVAL = 5       # Update progress every N games

# ========================================
# FILE PATHS AND DEFAULTS
# ========================================

# Default paths
DEFAULT_PGN_FILE = "testgames.pgn"
STOCKFISH_EXECUTABLE = "stockfish"

# ========================================
# FUTURE OPTIMIZATION PLACEHOLDERS
# ========================================

# Caching Configuration (for future Phase 3 optimizations)
POSITION_CACHE_SIZE = 10000
SEE_CACHE_SIZE = 5000

# Dynamic Think Time (for future Phase 4 optimizations)
DYNAMIC_THINK_TIME = False
MIN_THINK_TIME = 0.05
MAX_THINK_TIME = 0.15

# Game Batching (for future Phase 2 optimizations)
ENABLE_GAME_BATCHING = False
BATCH_SIZE_THRESHOLD = 50
MOVES_PER_BATCH = 10

# ========================================
# LOGGING CONFIGURATION
# ========================================

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
} 
