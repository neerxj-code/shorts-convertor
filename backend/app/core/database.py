from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import text

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration helper for SQLite schema updates
    with engine.connect() as conn:
        try:
            # Check jobs table columns
            res_jobs = conn.execute(text("PRAGMA table_info(jobs);")).fetchall()
            jobs_cols = {row[1] for row in res_jobs}
            
            if "accuracy_mode" not in jobs_cols:
                print("[Database] Adding missing 'accuracy_mode' column to 'jobs' table...")
                conn.execute(text("ALTER TABLE jobs ADD COLUMN accuracy_mode VARCHAR DEFAULT 'BALANCED';"))
                conn.commit()

            # Check clips table columns
            res_clips = conn.execute(text("PRAGMA table_info(clips);")).fetchall()
            clips_cols = {row[1] for row in res_clips}

            if "score" not in clips_cols:
                print("[Database] Adding missing 'score' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN score INTEGER DEFAULT 80;"))
            if "score_breakdown_json" not in clips_cols:
                print("[Database] Adding missing 'score_breakdown_json' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN score_breakdown_json TEXT;"))
            if "category" not in clips_cols:
                print("[Database] Adding missing 'category' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN category VARCHAR DEFAULT 'Insight';"))
            if "hook" not in clips_cols:
                print("[Database] Adding missing 'hook' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN hook TEXT;"))
            if "reason" not in clips_cols:
                print("[Database] Adding missing 'reason' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN reason TEXT;"))
            if "transcript" not in clips_cols:
                print("[Database] Adding missing 'transcript' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN transcript TEXT;"))
            if "is_selected" not in clips_cols:
                print("[Database] Adding missing 'is_selected' column to 'clips' table...")
                conn.execute(text("ALTER TABLE clips ADD COLUMN is_selected INTEGER DEFAULT 1;"))
            
            conn.commit()
            print("[Database] SQLite schema initialization & column migrations verified.")
        except Exception as e:
            print(f"[Database] Warning during schema migration check: {e}")
