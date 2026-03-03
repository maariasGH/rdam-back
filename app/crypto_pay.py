import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

def encrypt_string(plain_text: str, secret_key: str) -> str:
    # 1. Derivar clave de 256 bits (SHA-256) igual que en JS
    key = SHA256.new(secret_key.encode()).digest()
    
    # 2. Generar IV aleatorio de 16 bytes
    iv = get_random_bytes(16)
    
    # 3. Configurar AES-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # 4. Encriptar con Padding PKCS7
    ciphertext = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    
    # 5. Combinar IV + Ciphertext y pasar a Base64
    combined = iv + ciphertext
    return base64.b64encode(combined).decode('utf-8')

def decrypt_string(encrypted_text: str, secret_key: str) -> str:
    try:
        key = SHA256.new(secret_key.encode()).digest()
        combined = base64.b64decode(encrypted_text)
        
        iv = combined[:16] # Los primeros 16 bytes son el IV
        ciphertext = combined[16:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Error al desencriptar: {e}")
        return None