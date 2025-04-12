import sys
from datetime import datetime

import yaml

from src.db import get_session_factory, init_db
from src.models.db import Milestone, Roadmap, Task

# Initialize DB
init_db()
session = get_session_factory()()

# Command line argument for YAML file
yaml_file = sys.argv[1]
roadmap_id = sys.argv[2]

try:
    # Load YAML data
    with open(yaml_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    print(f"Importing from {yaml_file} to roadmap {roadmap_id}")

    # Import milestones
    for m in data.get("milestones", []):
        milestone_id = m["id"]
        milestone = Milestone(
            id=milestone_id,
            title=m["name"],
            description=m.get("description", ""),
            status=m.get("status", "planned"),
            roadmap_id=roadmap_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(milestone)
        session.commit()
        print(f"Added milestone: {milestone_id}: {m['name']}")

    # Import tasks
    for t in data.get("tasks", []):
        task_id = t["id"]
        milestone_id = t.get("milestone")

        task = Task(
            id=task_id,
            title=t["title"],
            description=t.get("description", ""),
            status=t.get("status", "todo"),
            priority=t.get("priority", "P0"),
            roadmap_id=roadmap_id,
            milestone_id=milestone_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(task)
        session.commit()
        print(f"Added task: {task_id}: {t['title']}")

    print("Import completed successfully")

except Exception as e:
    print(f"Error during import: {e}")
    session.rollback()
finally:
    session.close()
