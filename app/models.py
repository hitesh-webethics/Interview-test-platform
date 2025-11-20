from sqlalchemy import Column, Integer, String, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base

# Role Table
class Role(Base):
    __tablename__= "roles"

    id = Column(Integer, primary_key = True, index = True)
    role_name = Column(String(100), unique = True, nullable = False)

    # Relationship with next table
    # users = relationship("User", back_populates= "role", cascade = "all, delete", passive_deletes = True)


# User Table
class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String(150), nullable = False)
    email = Column(String(200), unique = True, nullable = False)
    password = Column(Text, nullable = False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete = "CASCADE")) # Foreign Key connectes user to role.id
    created_at = Column(TIMESTAMP(timezone = True), server_default = func.now())

    # Relationship (Access roles)
    role = relationship("Role", backref = "users")

    # categories = relationship("Category", back_populates="creator")
    # questions = relationship("Question", back_populates="creator")

# Category Table
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Foreign Key connectes category to user.id
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", backref="categories")
    
    sub_categories = relationship("Subcategory", backref="category", cascade="all, delete", passive_deletes=True)

# Subcategory Table
class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id")) # Foreign Key connects subcategory to category
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    # category = relationship("Category", back_populates="subcategories")

# Questions Table
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    sub_category_id = Column(Integer, ForeignKey("subcategories.id", ondelete="SET NULL"), nullable=True)  # Optional
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # Stored as JSON string
    correct_option = Column(String(1), nullable=False)  # Single character: 'a', 'b', 'c', 'd'
    difficulty = Column(String(20), nullable=False)  # 'Easy', 'Medium', 'Hard'
    user_id = Column(Integer, ForeignKey("users.id")) # Foreign key for connecting with user.id
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    category = relationship("Category")
    sub_category = relationship("Subcategory")
    creator = relationship("User", backref="questions")