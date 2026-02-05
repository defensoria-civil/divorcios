-- Script SQL para crear usuario de prueba
-- Hash de "password123" con bcrypt
-- Puede regenerarse con: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('password123'))"

-- Primero eliminar si existe
DELETE FROM users WHERE username = 'semper';

-- Insertar nuevo usuario
INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
VALUES (
    'semper',
    'semper@gmail.com',
    '$2b$12$R0LfyfOdGplnl9PeVjPJeOMQrnCT0QSTmb/t5ZNHj8eFSeBShepuq',
    'Sebastian Pereyra',
    'admin',
    true,
    NOW(),
    NOW()
);
