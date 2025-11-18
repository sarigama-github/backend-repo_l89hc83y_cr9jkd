"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Example schemas (you can keep using these or the new ones below)

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# --------------------------------------------------
# School Portal Schemas
# --------------------------------------------------

class School(BaseModel):
    """Schools collection schema (collection name: "school")"""
    name: str = Field(..., description="School name")
    email: EmailStr = Field(..., description="School admin email")
    password: str = Field(..., min_length=6, description="Password (plain for demo)")
    address: Optional[str] = Field(None, description="Address")
    phone: Optional[str] = Field(None, description="Phone number")

class Order(BaseModel):
    """Uniform orders for a school (collection name: "order")"""
    school_id: str = Field(..., description="ID of the school (stringified ObjectId)")
    order_number: str = Field(..., description="Human-friendly order number")
    amount: float = Field(..., ge=0, description="Order amount")
    status: str = Field("paid", description="Order status: paid/pending/cancelled")
    items: Optional[List[str]] = Field(default=None, description="List of item names")

class PayoutRequest(BaseModel):
    """Payout requests made by schools (collection name: "payoutrequest")"""
    school_id: str = Field(..., description="ID of the school (stringified ObjectId)")
    amount: float = Field(..., ge=0, description="Requested payout amount")
    bank_name: str = Field(..., description="Bank name")
    account_holder: str = Field(..., description="Account holder name")
    account_number: str = Field(..., description="Bank account number")
    ifsc: str = Field(..., description="IFSC/SWIFT code")
    status: str = Field("pending", description="Request status: pending/approved/rejected/paid")
