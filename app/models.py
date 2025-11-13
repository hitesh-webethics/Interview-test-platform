from sqlalchemy import Column, Integer, String, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base

# Role Table
class Role(Base):
    __tablename__= "roles"

    id = Column(Integer, primary_key = True, index = True)
    role_name = Column(String(100), unique = True, nullable = False)

    # Relationship with next table
    users = relationship("User", back_populates= "role", cascade = "all, delete", passive_deletes = True)

# User Table
class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String(150), nullable = False)
    email = Column(String(200), unique = True, nullable = False)
    password = Column(Text, nullable = False)

    # Foreign Key connectes user to role.id
    role_id = Column(Integer, ForeignKey("roles.id", ondelete = "CASCADE"))

    created_at = Column(TIMESTAMP(timezone = True), server_default = func.now())

    # Relationship (Access roles)
    role = relationship("Role", back_populates = "users")

