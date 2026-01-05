import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role, User, Category
from app.auth import hash_password

def seed_roles(db: Session):
    roles = ["Admin", "Creator"]
    for role_name in roles:
        existing_role = db.query(Role).filter(Role.role_name == role_name).first()
        if not existing_role:
            new_role = Role(role_name=role_name)
            db.add(new_role)
            print(f"Role '{role_name}' created.")
        else:
            print(f"Role '{role_name}' already exists.")
    db.commit()

def seed_users(db: Session):
    users_data = [
        {"email": "admin@gmail.com", "name": "Admin User", "password": "admin123", "role_name": "Admin"},
        {"email": "creator@gmail.com", "name": "Creator User", "password": "creator123", "role_name": "Creator"},
    ]

    for user in users_data:
        existing_user = db.query(User).filter(User.email == user["email"]).first()
        if not existing_user:
            role = db.query(Role).filter(Role.role_name == user["role_name"]).first()
            if not role:
                print(f"Error: Role '{user['role_name']}' not found for user '{user['email']}'. Skipping.")
                continue
            
            hashed_pwd = hash_password(user["password"])
            new_user = User(
                email=user["email"],
                name=user["name"],
                password=hashed_pwd,
                role_id=role.id
            )
            db.add(new_user)
            print(f"User '{user['email']}' created.")
        else:
            print(f"User '{user['email']}' already exists.")
    db.commit()

def seed_categories(db: Session):
    # We need a user to assign categories to. We'll use the Creator user.
    creator_user = db.query(User).filter(User.email == "creator@gmail.com").first()
    if not creator_user:
        print("Error: Creator user not found. Cannot seed categories.")
        return

    categories_data = [
        {"name": "Programming", "parent": None},
        {"name": "Databases", "parent": None},
        {"name": "Python", "parent": "Programming"},
        {"name": "JavaScript", "parent": "Programming"},
    ]

    # Process seeded items to ensure parents are created first
    # Simple sort might not be enough if nested deeper, but for this list:
    # Parents (None) should come first.
    categories_data.sort(key=lambda x: x["parent"] is not None)

    for cat_data in categories_data:
        # Check if exists (name + parent combo or just name? 
        # Requirement: "No duplicate categories are created on re-run"
        # Since 'name' is just a string and parent is a string in this model (based on my read of models.py: parent_category = Column(String...))
        # Wait, let me double check models.py again.
        # Line 39: parent_category = Column(String(150), nullable=True)
        # So it's just a string, not a relationship or ID.
        
        # We need to prevent duplicates.
        existing_cat = db.query(Category).filter(
            Category.name == cat_data["name"],
            Category.parent_category == cat_data["parent"],
            Category.user_id == creator_user.id
        ).first()

        if not existing_cat:
            new_cat = Category(
                name=cat_data["name"],
                parent_category=cat_data["parent"],
                user_id=creator_user.id,
                description=f"Seeded category: {cat_data['name']}"
            )
            db.add(new_cat)
            print(f"Category '{cat_data['name']}' created.")
        else:
            print(f"Category '{cat_data['name']}' already exists.")
    db.commit()

def seed():
    db = SessionLocal()
    try:
        print("Starting database seed...")
        seed_roles(db)
        seed_users(db)
        seed_categories(db)
        print("Database seeded successfully!")
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
