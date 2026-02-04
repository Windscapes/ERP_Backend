"""
Seed script to populate the database with sample data
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.nursery import Nursery
from app.models.product import Product
import random

# Sample data
NURSERIES = [
    {"nursery_id": "NUR-001", "nursery_name": "Green Valley Nursery"},
    {"nursery_id": "NUR-002", "nursery_name": "Sunny Gardens"},
    {"nursery_id": "NUR-003", "nursery_name": "Paradise Plants"},
    {"nursery_id": "NUR-004", "nursery_name": "Urban Greens"},
    {"nursery_id": "NUR-005", "nursery_name": "Botanical Haven"},
]

PLANT_TYPES = [
    "Rose", "Tulip", "Sunflower", "Orchid", "Lily", "Daisy", "Marigold", "Jasmine",
    "Lavender", "Petunia", "Hibiscus", "Geranium", "Chrysanthemum", "Carnation",
    "Zinnia", "Dahlia", "Begonia", "Pansy", "Azalea", "Gardenia", "Fern", "Palm",
    "Cactus", "Succulent", "Bonsai", "Bamboo", "Aloe Vera", "Snake Plant",
    "Peace Lily", "Spider Plant", "Pothos", "Monstera", "Fiddle Leaf Fig",
    "Rubber Plant", "ZZ Plant", "Philodendron", "Dracaena", "Anthurium"
]

SIZES = ["Small", "Medium", "Large", "Extra Large", "Mini", "Jumbo", "Standard", "Compact"]

COLORS = ["Red", "White", "Pink", "Yellow", "Purple", "Blue", "Orange", "Mixed", "Green", "Variegated"]

def create_products(db: Session, count: int = 30):
    """Create sample products"""
    products = []
    
    for i in range(count):
        nursery = random.choice(NURSERIES)
        plant = random.choice(PLANT_TYPES)
        size = random.choice(SIZES)
        color = random.choice(COLORS)
        
        # Generate product details
        product_id = f"PRD-{str(i+1).zfill(4)}"
        item_name = f"{color} {plant}"
        inventory_quantity = random.randint(5, 150)
        ordered_quantity = random.randint(0, 50)
        base_price = round(random.uniform(5.99, 199.99), 2)
        rate_percentage = round(random.uniform(10.0, 35.0), 2)
        
        product = Product(
            product_id=product_id,
            nursery_id=nursery["nursery_id"],
            item_name=item_name,
            size=size,
            inventory_quantity=inventory_quantity,
            ordered_quantity=ordered_quantity,
            low_stock_threshold=10,
            base_price_per_unit=base_price,
            rate_percentage=rate_percentage,
            image_url=f"https://images.unsplash.com/photo-{random.randint(1000000000000, 9999999999999)}"
        )
        
        products.append(product)
        print(f"Created product: {item_name} ({size}) - ${base_price}")
    
    db.bulk_save_objects(products)
    db.commit()
    print(f"\n✓ Successfully created {count} products")

def create_nurseries(db: Session):
    """Create sample nurseries"""
    nurseries = []
    
    for nursery_data in NURSERIES:
        # Check if nursery already exists
        existing = db.query(Nursery).filter(Nursery.nursery_id == nursery_data["nursery_id"]).first()
        if not existing:
            nursery = Nursery(**nursery_data)
            nurseries.append(nursery)
            print(f"Created nursery: {nursery_data['nursery_name']}")
    
    if nurseries:
        db.bulk_save_objects(nurseries)
        db.commit()
        print(f"\n✓ Successfully created {len(nurseries)} nurseries")
    else:
        print("\n✓ All nurseries already exist")

def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("Starting database seeding...")
    print("=" * 60)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create nurseries first
        print("\n[1/2] Creating nurseries...")
        create_nurseries(db)
        
        # Create products
        print("\n[2/2] Creating products...")
        create_products(db, count=30)  # Create 30 products
        
        print("\n" + "=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
