from marshmallow import Schema, fields, validate

class UserUpdateSchema(Schema):
    """Schema for updating user profile information (excluding password and role by default)"""
    name = fields.String(validate=validate.Length(min=3, max=100))
    username = fields.String(validate=validate.Length(min=3, max=50))
    email = fields.Email()
    # Role can only be updated by admins, handled in route logic

class PasswordUpdateSchema(Schema):
    """Schema for updating user password"""
    current_password = fields.String(required=False) # Required only if user updates their own password
    new_password = fields.String(required=True, validate=validate.Length(min=6))

# Schema for Admin creating a user (similar to auth.schemas.UserSchema but can be separate)
class AdminUserCreateSchema(Schema):
    """Schema for admin creating a new user"""
    name = fields.String(required=True, validate=validate.Length(min=3, max=100))
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    role = fields.String(required=False, validate=validate.OneOf(['admin', 'vendedor', 'suporte'])) 