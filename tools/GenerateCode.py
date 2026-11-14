import hashlib
import base64

class CodeGenerator:
    def _generate_deterministic_number(self, input_string, min_digits=3, max_digits=8):
        hash_bytes = hashlib.sha256(input_string.encode()).digest()
        stable_int = int.from_bytes(hash_bytes, byteorder='big')
        
        length = min_digits + (stable_int % (max_digits - min_digits + 1))
        start_range = 10**(length - 1)
        end_range = (10**length) - 1
        
        return start_range + (stable_int % (end_range - start_range + 1))

    def regular_code(self, product_price):
        return f"P59{int(product_price * 2)}9".upper()

    def unique_code(self, product_name, product_price, size="Normal"):
        double_product_price = int(product_price * 2)
        product_name_split_code = "".join([n[:3] for n in product_name.split()])
        
        hash_bytes = hashlib.sha256(product_name_split_code.encode()).digest()
        base32_encoded = base64.b32encode(hash_bytes).decode('utf-8')
        product_name_code = "".join([char for char in base32_encoded if char.isalpha()])[:8]
        
        seed_string = f"{product_name}-{product_price}-{size}"
        random_post_price_code = self._generate_deterministic_number(seed_string)
        price_code_length = len(str(abs(random_post_price_code)))
        
        product_code = f"{product_name_code}-{double_product_price}{random_post_price_code}.{price_code_length}-{size[:3]}"
        return product_code.upper()

