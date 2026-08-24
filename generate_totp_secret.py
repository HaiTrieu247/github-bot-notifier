import os
import base64

def generate_base32_secret(length=32):
    """
    Tạo chuỗi Base32 ngẫu nhiên (chỉ dùng A-Z, 2-7).
    Sử dụng os.urandom an toàn về mặt mã hóa.
    """
    # 20 bytes ngẫu nhiên khi encode base32 sẽ ra đúng 32 ký tự
    random_bytes = os.urandom(20)
    
    # Mã hóa sang Base32 và bỏ dấu '=' (padding)
    secret = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
    
    return secret[:length]

if __name__ == "__main__":
    secret = generate_base32_secret(32)
    print("\n" + "="*50)
    print("MÃ BÍ MẬT CỦA BẠN (16-32 ký tự Base32):")
    print(secret)
    print("="*50 + "\n")
    print("Hãy copy đoạn mã này và dán vào:")
    print("1. File .env (ADMIN_TOTP_SECRET)")
    print("2. Trong app Google Authenticator của bạn (chọn Enter a setup key)")
