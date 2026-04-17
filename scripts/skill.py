#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base65536 文件编码/解码工具（带字节异或加密和元数据隐藏）
使用Base65536编码将任意文件转换为Unicode文本，支持gzip压缩、原文件名保存，
以及基于SHA-256密钥的字节级异或加密，加密模式下隐藏真实元数据。

安装依赖:
    pip install base65536

用法:
    # 普通编码（无加密，元数据明文）
    python skill.py encode <输入文件> [-o <输出文件>] [--no-compress]

    # 加密编码（异或加密，隐藏元数据，输出密钥）
    python skill.py encode <输入文件> --scramble [-o <输出文件>]

    # 解码（若文件已加密，需提供密钥）
    python skill.py decode <输入文件> --key <密钥整数> [-o <输出文件>]

示例:
    # 加密编码
    python skill.py encode secret.zip --scramble -o public.txt
    # 输出:
    #   🔑 密钥（整数）: 108544482569932551567348223456789012...
    #   ✓ 已编码: public.txt

    # 解密还原
    python skill.py decode public.txt --key 108544482569932551567348223456789012...

注意:
    - 加密模式下，文件内的元数据（文件名、大小等）被隐藏，仅显示假占位信息。
    - 请妥善保管密钥，丢失密钥无法恢复文件。

Author: Assistant
Version: 3.0.0
"""

import argparse
import gzip
import base65536
import os
import json
import hashlib
import random

def sha256_to_int(data: bytes) -> int:
    """将数据的 SHA-256 转换为一个大整数，作为随机种子"""
    return int.from_bytes(hashlib.sha256(data).digest(), byteorder='big')

def xor_bytes(data: bytes, seed: int) -> bytes:
    """使用种子生成伪随机字节流，对数据进行异或加密/解密"""
    rng = random.Random(seed)
    key_stream = bytes([rng.getrandbits(8) for _ in range(len(data))])
    return bytes([a ^ b for a, b in zip(data, key_stream)])

def encrypt_body(text: str, seed: int) -> str:
    """加密 Base65536 文本：转字节 -> 异或 -> Base65536 编码"""
    data_bytes = text.encode('utf-8')
    encrypted_bytes = xor_bytes(data_bytes, seed)
    return base65536.encode(encrypted_bytes)

def decrypt_body(encrypted_b65536: str, seed: int) -> str:
    """解密：Base65536 解码 -> 异或 -> UTF-8 解码"""
    encrypted_bytes = base65536.decode(encrypted_b65536)
    decrypted_bytes = xor_bytes(encrypted_bytes, seed)
    return decrypted_bytes.decode('utf-8')

def main():
    parser = argparse.ArgumentParser(description="Base65536 文件编码/解码工具（带异或加密）")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    encode_parser = subparsers.add_parser("encode", help="编码文件")
    encode_parser.add_argument("input", help="输入文件路径")
    encode_parser.add_argument("-o", "--output", help="输出文件路径")
    encode_parser.add_argument("--no-compress", action="store_true", help="不压缩（适用于已压缩文件）")
    encode_parser.add_argument("--scramble", action="store_true", help="异或加密并隐藏元数据（加密模式）")
    
    decode_parser = subparsers.add_parser("decode", help="解码文件")
    decode_parser.add_argument("input", help="输入文件路径")
    decode_parser.add_argument("-o", "--output", help="输出文件路径（可选，默认使用原文件名）")
    decode_parser.add_argument("--key", help="解密密钥（整数，加密模式必需）")
    
    args = parser.parse_args()
    
    if args.command == "encode":
        with open(args.input, "rb") as f:
            data = f.read()
        
        original_size = len(data)
        original_name = os.path.basename(args.input)
        
        compressed_flag = not args.no_compress
        if compressed_flag:
            compressed_data = gzip.compress(data, compresslevel=9)
            print(f"  压缩: {original_size} → {len(compressed_data)} 字节 ({len(compressed_data)/original_size*100:.1f}%)")
        else:
            compressed_data = data
        
        b65536_text = base65536.encode(compressed_data)
        print(f"  编码: {len(compressed_data)} 字节 → {len(b65536_text)} 字符")
        
        real_metadata = {
            "original_name": original_name,
            "compressed": compressed_flag,
            "original_size": original_size
        }
        
        if args.scramble:
            # 生成密钥：基于编码后内容计算 SHA-256 整数
            seed_bytes = b65536_text.encode('utf-8')
            key_int = sha256_to_int(seed_bytes)
            print(f"  🔑 密钥（整数）: {key_int}")
            
            # 异或加密主体文本
            encrypted_body = encrypt_body(b65536_text, key_int)
            
            # 加密真实元数据（使用相同的密钥种子）
            real_meta_json = json.dumps(real_metadata).encode('utf-8')
            rng = random.Random(key_int)
            meta_key_bytes = bytes([rng.getrandbits(8) for _ in range(len(real_meta_json))])
            encrypted_meta = bytes([a ^ b for a, b in zip(real_meta_json, meta_key_bytes)])
            encrypted_meta_b65536 = base65536.encode(encrypted_meta)
            
            # 假元数据（对外可见）
            fake_metadata = {
                "original_name": "encrypted_file",
                "compressed": True,
                "original_size": 0,
                "scrambled": True,
                "note": "This file is encrypted. Use key to decrypt."
            }
            metadata_line = f"#METADATA:{json.dumps(fake_metadata)}\n"
            
            # 最终输出：假元数据行 + 加密主体 + 加密元数据
            final_text = metadata_line + encrypted_body + "\n###ENCRYPTED_META###" + encrypted_meta_b65536
        else:
            real_metadata["scrambled"] = False
            metadata_line = f"#METADATA:{json.dumps(real_metadata)}\n"
            final_text = metadata_line + b65536_text
        
        output = args.output or original_name + ".b65536.txt"
        with open(output, "w", encoding="utf-8") as f:
            f.write(final_text)
        
        print(f"✓ 已编码: {output}")
        if args.scramble:
            print(f"  请保管好密钥: {key_int}")
        print(f"  最终大小: {len(final_text)} 字符 (原文件的 {len(b65536_text)/original_size*100:.1f}%)")
    
    elif args.command == "decode":
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 分离元数据行
        if "\n" in content:
            first_line, rest = content.split("\n", 1)
        else:
            first_line, rest = content, ""
        
        metadata = None
        if first_line.startswith("#METADATA:"):
            try:
                metadata = json.loads(first_line[10:])
                print(f"  读取到元数据: {metadata}")
            except:
                print("  警告: 元数据损坏，尝试直接解码")
        
        is_scrambled = metadata.get("scrambled", False) if metadata else False
        
        if is_scrambled:
            if not args.key:
                print("❌ 错误: 此文件已加密，需要提供 --key 密钥才能解码")
                return
            try:
                key_int = int(args.key)
            except ValueError:
                print("❌ 错误: 密钥必须是整数")
                return
            
            print(f"  使用密钥 {key_int} 进行解密...")
            
            # 分离加密主体和加密元数据
            if "###ENCRYPTED_META###" in rest:
                encrypted_body, encrypted_meta_b65536 = rest.split("###ENCRYPTED_META###", 1)
                encrypted_body = encrypted_body.rstrip("\n")
            else:
                print("❌ 错误: 加密文件格式不正确，缺少加密元数据")
                return
            
            # 解密真实元数据
            encrypted_meta = base65536.decode(encrypted_meta_b65536.strip())
            rng = random.Random(key_int)
            meta_key_bytes = bytes([rng.getrandbits(8) for _ in range(len(encrypted_meta))])
            real_meta_json_bytes = bytes([a ^ b for a, b in zip(encrypted_meta, meta_key_bytes)])
            try:
                real_metadata = json.loads(real_meta_json_bytes.decode('utf-8'))
                print(f"  解密元数据: {real_metadata}")
            except:
                print("❌ 错误: 密钥错误或文件损坏，无法解密元数据")
                return
            
            # 解密主体（使用修正后的字节异或解密）
            b65536_text = decrypt_body(encrypted_body, key_int)
        else:
            real_metadata = metadata
            b65536_text = rest
        
        # Base65536 解码
        data = base65536.decode(b65536_text.strip())
        
        # 处理压缩
        if real_metadata and real_metadata.get("compressed", False):
            if data[:2] == b'\x1f\x8b':
                print("  检测到 gzip 压缩，正在解压...")
                data = gzip.decompress(data)
            else:
                print("  警告: 元数据标记为压缩但数据非gzip格式，尝试直接还原")
        
        # 确定输出文件名
        if args.output:
            output = args.output
        else:
            output = real_metadata.get("original_name", "restored_file") if real_metadata else "restored_file"
            if os.path.exists(output):
                base, ext = os.path.splitext(output)
                output = f"{base}_restored{ext}"
                print(f"  文件已存在，改为: {output}")
        
        with open(output, "wb") as f:
            f.write(data)
        
        print(f"✓ 已解码: {output}")
        print(f"  还原大小: {len(data)} 字节")

if __name__ == "__main__":
    main()