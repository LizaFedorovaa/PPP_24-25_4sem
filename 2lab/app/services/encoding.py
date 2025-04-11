import heapq
import base64
from collections import Counter
from typing import Dict, Tuple

class HuffmanNode:
    def __init__(self, char: str, freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(freq: Dict[str, int]) -> HuffmanNode:
    heap = [HuffmanNode(char, f) for char, f in freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = HuffmanNode(None, left.freq + right.freq)
        parent.left = left
        parent.right = right
        heapq.heappush(heap, parent)
    return heap[0]

def generate_huffman_codes(root: HuffmanNode, code: str = "", codes: Dict[str, str] = None) -> Dict[str, str]:
    if codes is None:
        codes = {}
    if root.char is not None:
        codes[root.char] = code or "0"  # Минимизируем длину кодов
    if root.left:
        generate_huffman_codes(root.left, code + "0", codes)
    if root.right:
        generate_huffman_codes(root.right, code + "1", codes)
    return codes

def huffman_encode(text: str) -> Tuple[str, Dict[str, str], int]:
    if not text:
        return "", {}, 0
    freq = Counter(text)
    root = build_huffman_tree(freq)
    codes = generate_huffman_codes(root)
    encoded = "".join(codes[char] for char in text)
    padding = (8 - len(encoded) % 8) % 8  # Паддинг зависит от длины
    encoded += "0" * padding
    byte_data = int(encoded, 2).to_bytes((len(encoded) + 7) // 8, byteorder="big")
    return base64.b64encode(byte_data).decode("utf-8"), codes, padding

def huffman_decode(encoded: str, codes: Dict[str, str], padding: int) -> str:
    if not encoded:
        return ""
    byte_data = base64.b64decode(encoded)
    binary = bin(int.from_bytes(byte_data, byteorder="big"))[2:].zfill(len(byte_data) * 8)
    binary = binary[:-padding] if padding else binary
    reverse_codes = {v: k for k, v in codes.items()}
    decoded = ""
    current_code = ""
    for bit in binary:
        current_code += bit
        if current_code in reverse_codes:
            decoded += reverse_codes[current_code]
            current_code = ""
    return decoded

def xor_encrypt(data: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    data_bytes = data.encode("utf-8")
    encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_bytes * (len(data_bytes) // len(key_bytes) + 1)))
    return base64.b64encode(encrypted).decode("utf-8")

def xor_decrypt(encrypted: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    encrypted_bytes = base64.b64decode(encrypted)
    decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1)))
    return decrypted.decode("utf-8")

def encode_data(text: str, key: str) -> Tuple[str, Dict[str, str], int]:
    huffman_encoded, codes, padding = huffman_encode(text)
    encrypted = xor_encrypt(huffman_encoded, key)
    return encrypted, codes, padding

def decode_data(encoded: str, key: str, codes: Dict[str, str], padding: int) -> str:
    decrypted = xor_decrypt(encoded, key)
    return huffman_decode(decrypted, codes, padding)