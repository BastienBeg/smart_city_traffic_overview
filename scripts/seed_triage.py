import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime

# Add project root to path to allow imports
sys.path.append(os.getcwd())
# Also add services/api-gateway to path because the imports in main/routers might be relative or expect it
sys.path.append(os.path.join(os.getcwd(), 'services', 'api-gateway'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import from the specific location
# Note: Since we added services/api-gateway to path, we might be able to import src.models... 
# But for clarity and robustness related to the monolith structure:
try:
    from services.api_gateway.src.models.annotations import Annotation
except ImportError:
    # If run from services/api-gateway context
    from src.models.annotations import Annotation

# Default to localhost for running script from host
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/smartcity")

async def seed_data():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    try:
        async with async_session() as session:
            print("Creating seed data...")
            
            # Create 10 dummy annotations
            base_names = ["car", "bus", "truck", "motorcycle", "person"]
            
            for i in range(10):
                ann = Annotation(
                    id=uuid4(),
                    image_path=f"https://placehold.co/640x480?text=Traffic+{i}", # Placeholder image
                    label=base_names[i % len(base_names)],
                    is_verified=False,
                    created_at=datetime.utcnow(),
                    camera_id=f"cam_{i % 3 + 1}",
                    detection_id=uuid4()
                )
                session.add(ann)
            
            await session.commit()
            print("Added 10 dummy annotations.")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
