import sys
import os
import traceback

sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from services.advanced_analytics import get_pattern_success_rate, get_institutional_clusters, analyze_management_tone
    from services.audio_briefing import generate_market_minutes
    from database import init_db

    print("--- FULL CODEBASE CHECK ---")
    
    # 1. Check DB
    print("\n[DB] Initializing...")
    init_db()
    
    # 2. Test Success Rate
    print("\n[Pattern Success Engine] -> RELIANCE (EMA Crossover)")
    res1 = get_pattern_success_rate('RELIANCE', 'EMA Crossover')
    print(res1)
    
    # 3. Test Clusters
    print("\n[Institutional Clusters]")
    res2 = get_institutional_clusters()
    print(res2)
    
    # 4. Test Tone Shift
    print("\n[Tone Shift Analyzer] -> TCS")
    res3 = analyze_management_tone('TCS')
    print(res3)
    
    # 5. Test Audio Script
    print("\n[Audio Briefing Generator]")
    res4 = generate_market_minutes()
    print(res4)

    print("\nAll direct function calls executed successfully!")

except ImportError as e:
    print(f"\n[Environment Error]: Missing dependency - {e}")
    print("Please ensure your 'uv' installation is complete and dependencies are synced via 'pip install -r backend/requirements.txt'")
except Exception as e:
    print(f"\n[Execution Error]: {e}")
    traceback.print_exc()
