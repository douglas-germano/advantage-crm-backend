from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    """
    Esquema para validação dos dados do usuário na criação/registro.
    
    Fields:
        name: Nome completo do usuário (3-100 caracteres)
        username: Nome de usuário único (3-50 caracteres)
        email: Email válido e único
        password: Senha (mínimo 6 caracteres)
        role: Função do usuário (admin, vendedor, suporte)
    """
    name = fields.String(
        required=True, 
        validate=validate.Length(min=3, max=100),
        error_messages={'required': 'O nome é obrigatório'}
    )
    username = fields.String(
        required=True, 
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'O nome de usuário é obrigatório'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'O email é obrigatório', 'invalid': 'Email inválido'}
    )
    password = fields.String(
        required=True, 
        validate=validate.Length(min=6),
        error_messages={'required': 'A senha é obrigatória', 'invalid': 'A senha deve ter pelo menos 6 caracteres'}
    )
    role = fields.String(
        validate=validate.OneOf(['admin', 'vendedor', 'suporte']),
        error_messages={'invalid': 'Função inválida. Deve ser: admin, vendedor ou suporte'}
    )


class LoginSchema(Schema):
    """
    Esquema para validação dos dados de login.
    
    Fields:
        username: Nome de usuário
        password: Senha
    """
    username = fields.String(
        required=True,
        error_messages={'required': 'O nome de usuário é obrigatório'}
    )
    password = fields.String(
        required=True,
        error_messages={'required': 'A senha é obrigatória'}
    ) 