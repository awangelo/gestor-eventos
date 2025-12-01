#!/usr/bin/env python
"""
Test script to validate banner upload validation in CadastroEventoView
"""
import os
import sys
import django
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_eventos.settings')
django.setup()

from api.views import _validate_image_file

def test_banner_validation():
    print("🧪 Testando validação de upload de banner\n")
    
    # Test 1: Valid image extensions
    print("✅ Teste 1: Extensões válidas")
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    for ext in valid_extensions:
        mock_file = SimpleUploadedFile(
            f"test{ext}",
            b"fake image content",
            content_type=f"image/{ext[1:]}" if ext != '.jpg' else "image/jpeg"
        )
        error = _validate_image_file(mock_file)
        if error:
            print(f"  ❌ {ext}: {error}")
        else:
            print(f"  ✓ {ext}: Aceito")
    
    # Test 2: Invalid extensions
    print("\n❌ Teste 2: Extensões inválidas")
    invalid_files = [
        ('document.pdf', 'application/pdf'),
        ('script.js', 'application/javascript'),
        ('data.txt', 'text/plain'),
        ('archive.zip', 'application/zip'),
    ]
    
    for filename, content_type in invalid_files:
        mock_file = SimpleUploadedFile(
            filename,
            b"fake content",
            content_type=content_type
        )
        error = _validate_image_file(mock_file)
        if error:
            print(f"  ✓ {filename}: Rejeitado - {error}")
        else:
            print(f"  ❌ {filename}: ERRO - deveria ser rejeitado!")
    
    # Test 3: File size validation (max 5MB)
    print("\n📏 Teste 3: Tamanho do arquivo")
    
    # Small file (should pass)
    small_file = SimpleUploadedFile(
        "small.jpg",
        b"x" * (1024 * 1024),  # 1MB
        content_type="image/jpeg"
    )
    error = _validate_image_file(small_file)
    if error:
        print(f"  ❌ Arquivo 1MB: {error}")
    else:
        print(f"  ✓ Arquivo 1MB: Aceito")
    
    # Large file (should fail)
    large_file = SimpleUploadedFile(
        "large.jpg",
        b"x" * (6 * 1024 * 1024),  # 6MB
        content_type="image/jpeg"
    )
    error = _validate_image_file(large_file)
    if error:
        print(f"  ✓ Arquivo 6MB: Rejeitado - {error}")
    else:
        print(f"  ❌ Arquivo 6MB: ERRO - deveria ser rejeitado!")
    
    # Test 4: None/empty file
    print("\n🚫 Teste 4: Arquivo vazio/None")
    error = _validate_image_file(None)
    if error:
        print(f"  ❌ None: {error}")
    else:
        print(f"  ✓ None: Aceito (opcional)")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    test_banner_validation()
