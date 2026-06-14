from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Integer)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    profile_image = Column(String, nullable=True)
    cover_image = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
