-- AIPipeline initial schema
-- Tables match existing Pydantic models in master/models/

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    description TEXT DEFAULT '',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS shots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sequence_id TEXT,
    scene_description TEXT DEFAULT '',
    dialogue TEXT,

    -- Structured data stored as JSON
    subjects TEXT DEFAULT '[]',
    environment TEXT DEFAULT '{}',
    technical TEXT DEFAULT '{}',

    -- Legacy fields
    action TEXT,
    character_ids TEXT DEFAULT '[]',
    cinematic_id TEXT,

    -- Generation
    generated_prompt TEXT,
    negative_prompt TEXT,
    seed INTEGER,

    -- Media paths
    reference_images TEXT DEFAULT '[]',
    generated_image_path TEXT,
    generated_video_path TEXT,

    -- Timeline
    frame_count INTEGER DEFAULT 24,
    fps REAL DEFAULT 24.0,
    duration_seconds REAL DEFAULT 1.0,
    timecode_in TEXT,
    timecode_out TEXT,

    -- State
    status TEXT DEFAULT 'pending',
    workflow_type TEXT DEFAULT 'text_to_image',

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    reference_sheet TEXT,

    -- LoRA
    lora_path TEXT,
    lora_strength REAL DEFAULT 0.8,
    trigger_words TEXT DEFAULT '',
    use_lora INTEGER DEFAULT 0,

    -- Appearance
    default_clothing TEXT,

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS cinematics (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'General',

    -- Camera & Lens
    camera_body TEXT DEFAULT 'Arri Alexa',
    focal_length TEXT DEFAULT '35mm',
    lens_type TEXT DEFAULT 'Anamorphic',
    film_stock TEXT,

    -- Scene
    shot_type TEXT,
    lighting TEXT,

    -- Mood
    style TEXT DEFAULT 'Cinematic',
    environment TEXT DEFAULT '',
    atmosphere TEXT DEFAULT '',
    filters TEXT DEFAULT '[]',

    -- Backup
    raw_data TEXT,

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    shot_id TEXT,
    workflow_type TEXT NOT NULL,
    params TEXT DEFAULT '{}',

    -- Resource requirements
    vram_required_gb INTEGER DEFAULT 8,
    gpu_count_required INTEGER DEFAULT 1,

    -- State
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    progress REAL DEFAULT 0.0,

    -- Execution
    assigned_worker_id TEXT,
    created_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    output_files TEXT DEFAULT '[]',

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (shot_id) REFERENCES shots(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_shots_project ON shots(project_id);
CREATE INDEX IF NOT EXISTS idx_shots_status ON shots(status);
CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
CREATE INDEX IF NOT EXISTS idx_cinematics_project ON cinematics(project_id);
CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
